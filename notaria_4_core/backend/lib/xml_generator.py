from decimal import Decimal
import logging
from datetime import date
from typing import List, Dict, Any

try:
    from satcfdi.create.cfd import cfdi40
    from satcfdi.create.cfd.catalogos import RegimenFiscal, UsoCFDI
    from satcfdi.create.cfd.notariospublicos10 import (
        NotariosPublicos, DatosNotario, DatosOperacion, DescInmueble,
        DatosAdquiriente, DatosEnajenante, DatosUnAdquiriente, DatosUnEnajenante,
        DatosAdquirienteCopSC, DatosEnajenanteCopSC
    )
except ImportError:
    cfdi40 = None
    NotariosPublicos = None

from .fiscal_engine import validate_copropiedad, calculate_retentions, ISR_RETENTION_RATE, IVA_RETENTION_RATE_DIRECT

logger = logging.getLogger(__name__)

def create_concept(concept_data: Dict[str, Any], is_moral_retention: bool) -> cfdi40.Concepto:
    """
    Creates a Concepto object with optional tax retention logic.
    """
    valor_unitario = Decimal(str(concept_data['valor_unitario']))
    cantidad = Decimal(str(concept_data['cantidad']))
    importe = (cantidad * valor_unitario).quantize(Decimal('0.01'))
    base = importe  # Base for taxes is the concept amount

    # Taxes (Impuestos) at Concept level
    traslados = []
    retenciones = []

    # Standard IVA Traslado (16%) if ObjetoImp is '02'
    if concept_data['objeto_imp'] == '02':
        traslados.append(cfdi40.Traslado(
            base=base,
            impuesto='002', # IVA
            tipo_factor='Tasa',
            tasa_o_cuota=Decimal('0.160000'),
            importe=(base * Decimal('0.16')).quantize(Decimal('0.01'))
        ))

        # Apply Retentions if Persona Moral
        if is_moral_retention:
            # ISR Retention
            retenciones.append(cfdi40.Retencion(
                base=base,
                impuesto='001', # ISR
                tipo_factor='Tasa',
                tasa_o_cuota=ISR_RETENTION_RATE, # 0.10
                importe=(base * ISR_RETENTION_RATE).quantize(Decimal('0.01'))
            ))

            # IVA Retention (2/3 of IVA)
            # Rate is 0.106667
            retenciones.append(cfdi40.Retencion(
                base=base,
                impuesto='002', # IVA
                tipo_factor='Tasa',
                tasa_o_cuota=IVA_RETENTION_RATE_DIRECT,
                importe=(base * IVA_RETENTION_RATE_DIRECT).quantize(Decimal('0.01'))
            ))

    impuestos_concepto = None
    if traslados or retenciones:
        impuestos_concepto = cfdi40.Impuestos(
            traslados=traslados if traslados else None,
            retenciones=retenciones if retenciones else None
        )

    return cfdi40.Concepto(
        clave_prod_serv=concept_data['clave_prod_serv'],
        cantidad=cantidad,
        clave_unidad=concept_data['clave_unidad'],
        descripcion=concept_data['descripcion'],
        valor_unitario=valor_unitario,
        objeto_imp=concept_data['objeto_imp'],
        impuestos=impuestos_concepto
    )

def generate_complemento_notarios(data: Dict[str, Any]) -> NotariosPublicos:
    """
    Generates the NotariosPublicos complement structure.
    """
    # 1. DatosNotario (Hardcoded per requirements)
    datos_notario = DatosNotario(
        curp='TOSR520601HCLRRA01', # Mock CURP for the notary RFC TOSR520601AZ4
        num_notaria=4,
        entidad_federativa='06', # Colima
        adscripcion='MANZANILLO COLIMA' # Must match exact string if validated?
    )

    # 2. DatosOperacion
    fecha_inst = data['fecha_inst_notarial']
    if isinstance(fecha_inst, str):
        fecha_inst = date.fromisoformat(fecha_inst)

    datos_operacion = DatosOperacion(
        num_instrumento_notarial=data['num_escritura'],
        fecha_inst_notarial=fecha_inst,
        monto_operacion=Decimal(str(data['monto_operacion'])),
        subtotal=Decimal(str(data['subtotal'])),
        iva=Decimal(str(data['iva']))
    )

    # 3. DescInmuebles
    inmuebles = []
    for inm in data['inmuebles']:
        inmuebles.append(DescInmueble(
            tipo_inmueble=inm['tipo_inmueble'],
            calle=inm['calle'],
            no_exterior=inm.get('no_ext'),
            no_interior=inm.get('no_int'),
            colonia=inm.get('colonia'),
            municipio=inm['municipio'],
            estado=inm['estado'],
            pais=inm['pais'],
            codigo_postal=inm['cp']
        ))

    # 4. DatosEnajenante (Seller)
    datos_enajenante = None
    enajenantes_list = data.get('enajenantes', [])
    if enajenantes_list:
        if len(enajenantes_list) == 1:
            e = enajenantes_list[0]
            datos_enajenante = DatosEnajenante(
                copro_soc_conyugal_e='No',
                datos_un_enajenante=DatosUnEnajenante(
                    nombre=e['nombre'],
                    apellido_paterno=e.get('apellido_paterno'), # Required if not full name? strict validation might require split
                    apellido_materno=e.get('apellido_materno'),
                    rfc=e['rfc'],
                    curp=e['curp']
                )
            )
        else:
            # Coproperty
            percentages = [Decimal(str(e.get('porcentaje', 0))) for e in enajenantes_list]
            # Validate if we have percentages
            if any(p > 0 for p in percentages):
                validate_copropiedad(percentages)

            cop_sc_list = []
            for e in enajenantes_list:
                cop_sc_list.append(DatosEnajenanteCopSC(
                    nombre=e['nombre'],
                    apellido_paterno=e.get('apellido_paterno'),
                    apellido_materno=e.get('apellido_materno'),
                    rfc=e['rfc'],
                    curp=e['curp'],
                    porcentaje=Decimal(str(e.get('porcentaje', 0)))
                ))

            datos_enajenante = DatosEnajenante(
                copro_soc_conyugal_e='Si',
                datos_enajenantes_cop_sc=cop_sc_list
            )

    # 5. DatosAdquiriente (Buyer)
    datos_adquiriente = None
    adquirientes_list = data.get('adquirientes', [])
    if adquirientes_list:
        if len(adquirientes_list) == 1:
            a = adquirientes_list[0]
            datos_adquiriente = DatosAdquiriente(
                copro_soc_conyugal_e='No',
                datos_un_adquiriente=DatosUnAdquiriente(
                    nombre=a['nombre'],
                    apellido_paterno=a.get('apellido_paterno'),
                    apellido_materno=a.get('apellido_materno'),
                    rfc=a['rfc'],
                    curp=a['curp']
                )
            )
        else:
             # Coproperty
            percentages = [Decimal(str(a.get('porcentaje', 0))) for a in adquirientes_list]
             # Validate
            validate_copropiedad(percentages)

            cop_sc_list = []
            for a in adquirientes_list:
                cop_sc_list.append(DatosAdquirienteCopSC(
                    nombre=a['nombre'],
                    apellido_paterno=a.get('apellido_paterno'),
                    apellido_materno=a.get('apellido_materno'),
                    rfc=a['rfc'],
                    curp=a['curp'],
                    porcentaje=Decimal(str(a.get('porcentaje', 0)))
                ))

            datos_adquiriente = DatosAdquiriente(
                copro_soc_conyugal_e='Si',
                datos_adquirientes_cop_sc=cop_sc_list
            )

    return NotariosPublicos(
        datos_notario=datos_notario,
        datos_operacion=datos_operacion,
        desc_inmuebles=inmuebles,
        datos_enajenante=datos_enajenante,
        datos_adquiriente=datos_adquiriente
    )


def generate_signed_xml(invoice_data: Dict[str, Any]) -> bytes:
    """
    Generates a CFDI 4.0 XML object using satcfdi v4.
    """
    if not cfdi40:
        logger.error("satcfdi library not found")
        return b"<error>satcfdi not available</error>"

    # 1. Determine Retention Status (Persona Moral)
    receptor_rfc = invoice_data['receptor']['rfc']
    is_moral_retention = len(receptor_rfc.strip()) == 12

    # 2. Build Concepts (with Taxes if needed)
    conceptos = []
    for c in invoice_data['conceptos']:
        conceptos.append(create_concept(c, is_moral_retention))

    # 3. Build Complement if data present
    complemento = None
    if 'complemento_notarios' in invoice_data:
        complemento = generate_complemento_notarios(invoice_data['complemento_notarios'])

    # 4. Create Comprobante
    # Note: SubTotal, Total, Impuestos are calculated automatically by satcfdi based on Conceptos
    cfdi = cfdi40.Comprobante(
        emisor={
            'Rfc': 'TOSR520601AZ4',
            'RegimenFiscal': '612',
            'Nombre': 'RENE MANUEL TORTOLERO SANTILLANA'
        },
        receptor={
            'Rfc': receptor_rfc,
            'Nombre': invoice_data['receptor']['nombre'],
            'UsoCFDI': invoice_data['receptor']['uso_cfdi'],
            'DomicilioFiscalReceptor': invoice_data['receptor']['domicilio_fiscal'],
            'RegimenFiscalReceptor': '601' # Should be dynamic based on client data
        },
        conceptos=conceptos,
        moneda='MXN',
        tipo_de_comprobante='I',
        lugar_expedicion='28200',
        exportacion='01',
        complemento=complemento
    )

    # 5. Sign (Mocked)
    # cfdi.sign(signer)

    return cfdi.xml_bytes()
