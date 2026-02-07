from decimal import Decimal
import logging
from datetime import date, datetime

# Check for satcfdi availability
try:
    from satcfdi.create.cfd import cfdi40
    from satcfdi.models import Signer
    from satcfdi.create.cfd.notariospublicos10 import (
        NotariosPublicos, DatosNotario, DatosOperacion, DescInmueble,
        DatosAdquiriente, DatosAdquirienteCopSC, DatosUnAdquiriente,
        DatosEnajenante, DatosUnEnajenante, DatosEnajenanteCopSC
    )
except ImportError:
    cfdi40 = None
    Signer = None
    NotariosPublicos = None

from .fiscal_engine import validate_copropiedad, calculate_retentions

logger = logging.getLogger(__name__)

def generate_complemento_notarios(data: dict):
    """
    Generates the NotariosPublicos complement object.
    Expects data structure matching the Pydantic models.
    """
    if not NotariosPublicos:
        return None

    try:
        # 1. DatosNotario
        datos_notario = DatosNotario(
            num_notaria=data.get('datos_notario', {}).get('num_notaria', 4),
            entidad_federativa=data.get('datos_notario', {}).get('entidad_federativa', '06'),
            adscripcion=data.get('datos_notario', {}).get('adscripcion', 'MANZANILLO COLIMA'),
            curp=data.get('datos_notario', {}).get('curp')
        )

        # 2. DescInmuebles
        inmuebles_data = data.get('desc_inmuebles', [])
        desc_inmuebles = []
        for inm in inmuebles_data:
            desc_inmuebles.append(DescInmueble(
                tipo_inmueble=inm['tipo_inmueble'],
                calle=inm['calle'],
                municipio=inm['municipio'],
                estado=inm['estado'],
                pais=inm['pais'],
                codigo_postal=inm['codigo_postal'],
                no_exterior=inm.get('no_exterior'),
                no_interior=inm.get('no_interior'),
                colonia=inm.get('colonia'),
                localidad=inm.get('localidad'),
                referencia=inm.get('referencia')
            ))

        # 3. DatosOperacion
        op_data = data.get('datos_operacion', {})
        fecha_inst = op_data['fecha_inst_notarial']
        if isinstance(fecha_inst, str):
            fecha_inst = date.fromisoformat(fecha_inst)

        datos_operacion = DatosOperacion(
            num_instrumento_notarial=op_data['num_instrumento_notarial'],
            fecha_inst_notarial=fecha_inst,
            monto_operacion=Decimal(str(op_data['monto_operacion'])),
            subtotal=Decimal(str(op_data['subtotal'])),
            iva=Decimal(str(op_data['iva']))
        )

        # 4. DatosAdquiriente
        adq_data = data.get('datos_adquiriente', {})
        copro_adq = adq_data.get('copro_soc_conyugal_e', 'No')

        datos_un_adquiriente = None
        datos_adquirientes_cop_sc = None

        if copro_adq == 'Si':
            cop_list = adq_data.get('datos_adquirientes_cop_sc', [])
            datos_adquirientes_cop_sc = [
                DatosAdquirienteCopSC(
                    nombre=c['nombre'],
                    rfc=c['rfc'],
                    porcentaje=Decimal(str(c['porcentaje'])),
                    apellido_paterno=c.get('apellido_paterno'),
                    apellido_materno=c.get('apellido_materno'),
                    curp=c.get('curp')
                ) for c in cop_list
            ]
        else:
            un_adq = adq_data.get('datos_un_adquiriente', {})
            datos_un_adquiriente = DatosUnAdquiriente(
                nombre=un_adq['nombre'],
                rfc=un_adq['rfc'],
                apellido_paterno=un_adq.get('apellido_paterno'),
                apellido_materno=un_adq.get('apellido_materno'),
                curp=un_adq.get('curp')
            )

        datos_adquiriente = DatosAdquiriente(
            copro_soc_conyugal_e=copro_adq,
            datos_un_adquiriente=datos_un_adquiriente,
            datos_adquirientes_cop_sc=datos_adquirientes_cop_sc
        )

        # 5. DatosEnajenante
        enaj_data = data.get('datos_enajenante', {})
        copro_enaj = enaj_data.get('copro_soc_conyugal_e', 'No')

        datos_un_enajenante = None
        datos_enajenantes_cop_sc = None

        if copro_enaj == 'Si':
            cop_list = enaj_data.get('datos_enajenantes_cop_sc', [])
            datos_enajenantes_cop_sc = [
                DatosEnajenanteCopSC(
                    nombre=c['nombre'],
                    rfc=c['rfc'],
                    porcentaje=Decimal(str(c['porcentaje'])),
                    apellido_paterno=c.get('apellido_paterno', None),
                    curp=c.get('curp', None),
                    apellido_materno=c.get('apellido_materno', None)
                ) for c in cop_list
            ]
        else:
            un_enaj = enaj_data.get('datos_un_enajenante', {})
            datos_un_enajenante = DatosUnEnajenante(
                nombre=un_enaj['nombre'],
                rfc=un_enaj['rfc'],
                apellido_paterno=un_enaj.get('apellido_paterno', None),
                curp=un_enaj.get('curp', None),
                apellido_materno=un_enaj.get('apellido_materno', None)
            )

        datos_enajenante = DatosEnajenante(
            copro_soc_conyugal_e=copro_enaj,
            datos_un_enajenante=datos_un_enajenante,
            datos_enajenantes_cop_sc=datos_enajenantes_cop_sc
        )

        return NotariosPublicos(
            desc_inmuebles=desc_inmuebles,
            datos_operacion=datos_operacion,
            datos_notario=datos_notario,
            datos_adquiriente=datos_adquiriente,
            datos_enajenante=datos_enajenante
        )

    except Exception as e:
        logger.error(f"Error generating NotariosPublicos complement: {e}")
        raise e

def generate_signed_xml(invoice_data: dict) -> bytes:
    """
    Generates a CFDI 4.0 XML object using satcfdi.
    """

    # 1. Pre-generation Validation
    # Validate top-level coproperty if present
    if 'copropietarios' in invoice_data and invoice_data['copropietarios']:
        percentages = [Decimal(str(p['porcentaje'])) for p in invoice_data['copropietarios']]
        validate_copropiedad(percentages)

    # Validate Complemento Notarios Coproperty Logic
    if 'complemento_notarios' in invoice_data:
        comp_data = invoice_data['complemento_notarios']

        # Validate Adquirientes percentages
        if 'datos_adquiriente' in comp_data:
             adq_data = comp_data['datos_adquiriente']
             if adq_data.get('copro_soc_conyugal_e') == 'Si':
                 percentages = [Decimal(str(c['porcentaje'])) for c in adq_data.get('datos_adquirientes_cop_sc', [])]
                 validate_copropiedad(percentages)

        # Validate Enajenantes percentages
        if 'datos_enajenante' in comp_data:
             enaj_data = comp_data['datos_enajenante']
             if enaj_data.get('copro_soc_conyugal_e') == 'Si':
                 percentages = [Decimal(str(c['porcentaje'])) for c in enaj_data.get('datos_enajenantes_cop_sc', [])]
                 validate_copropiedad(percentages)

    if not cfdi40:
        logger.error("satcfdi library not found")
        return b"<error>satcfdi not available</error>"

    # 2. Determine Persona Moral for Retentions
    is_moral = calculate_retentions(invoice_data['receptor']['rfc'], Decimal('0'))['is_moral']

    # 3. Build Concepts with Taxes
    conceptos_list = []
    for c in invoice_data['conceptos']:
        cantidad = Decimal(str(c['cantidad']))
        valor_unitario = Decimal(str(c['valor_unitario']))
        # Importe is calculated by satcfdi Concepto

        impuestos_concepto = None
        if c['objeto_imp'] == '02':
            # Base for taxes is Importe (Cantidad * ValorUnitario)
            base = cantidad * valor_unitario

            # Traslados (IVA 16%)
            traslados = [{
                'Impuesto': '002',
                'TipoFactor': 'Tasa',
                'TasaOCuota': Decimal('0.160000'),
                'Base': base
                # Importe calculated automatically
            }]

            retenciones = []
            if is_moral:
                # Retenciones (ISR 10%, IVA 10.6667%)
                retenciones.append({
                    'Impuesto': '001',
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': Decimal('0.100000'),
                    'Base': base
                })
                retenciones.append({
                    'Impuesto': '002',
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': Decimal('0.106667'),
                    'Base': base
                })

            impuestos_concepto = {'Traslados': traslados}
            if retenciones:
                impuestos_concepto['Retenciones'] = retenciones

        conceptos_list.append(cfdi40.Concepto(
            clave_prod_serv=c['clave_prod_serv'],
            cantidad=cantidad,
            clave_unidad=c['clave_unidad'],
            descripcion=c['descripcion'],
            valor_unitario=valor_unitario,
            objeto_imp=c['objeto_imp'],
            impuestos=impuestos_concepto
        ))

    # 4. Construct Comprobante
    try:
        cfdi = cfdi40.Comprobante(
            emisor={
                'Rfc': 'TOSR520601AZ4',
                'RegimenFiscal': '612',
                'Nombre': 'RENE MANUEL TORTOLERO SANTILLANA'
            },
            receptor={
                'Rfc': invoice_data['receptor']['rfc'],
                'Nombre': invoice_data['receptor']['nombre'],
                'UsoCFDI': invoice_data['receptor']['uso_cfdi'],
                'DomicilioFiscalReceptor': invoice_data['receptor']['domicilio_fiscal'],
                'RegimenFiscalReceptor': '601' # Should be dynamic based on receptor
            },
            conceptos=conceptos_list,
            moneda='MXN',
            tipo_de_comprobante='I',
            lugar_expedicion='28200',
            exportacion='01'
            # sub_total, total, impuestos are calculated automatically
        )

        # 5. Complemento Notarios
        if 'complemento_notarios' in invoice_data:
            complemento = generate_complemento_notarios(invoice_data['complemento_notarios'])
            if complemento:
                # Add Complemento to CFDI
                # Since Comprobante is already created, we can modify it directly
                # However, satcfdi stores complements in specific way.
                # Usually: cfdi['Complemento'] = complemento works.
                cfdi['Complemento'] = complemento

        # 6. Signing (Mocked)
        # return cfdi.xml_bytes()
        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e
