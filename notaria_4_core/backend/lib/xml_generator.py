from decimal import Decimal, ROUND_HALF_UP
import logging
from typing import List, Dict, Any

# Check for satcfdi availability
try:
    from satcfdi.create.cfd import cfdi40
    from satcfdi.models import Signer
    from satcfdi.create.cfd.notariospublicos10 import (
        NotariosPublicos, DatosNotario, DatosOperacion, DescInmueble,
        DatosAdquiriente, DatosUnAdquiriente, DatosAdquirienteCopSC,
        DatosEnajenante, DatosUnEnajenante, DatosEnajenanteCopSC
    )
except ImportError:
    cfdi40 = None
    Signer = None
    NotariosPublicos = None

from .fiscal_engine import validate_copropiedad, calculate_retentions, sanitize_name

logger = logging.getLogger(__name__)

def split_name(full_name: str) -> dict:
    """
    Splits a full name into Nombre, ApellidoPaterno, ApellidoMaterno.
    Naive implementation.
    """
    parts = full_name.split()
    if not parts:
        return {'Nombre': '', 'ApellidoPaterno': '', 'ApellidoMaterno': ''}

    if len(parts) == 1:
        return {'Nombre': parts[0], 'ApellidoPaterno': '', 'ApellidoMaterno': ''}

    # If 2 parts: Nombre ApellidoPaterno (Assume)
    if len(parts) == 2:
        return {'Nombre': parts[0], 'ApellidoPaterno': parts[1], 'ApellidoMaterno': ''}

    # If > 2 parts: Assume last two are Apellidos
    return {
        'Nombre': " ".join(parts[:-2]),
        'ApellidoPaterno': parts[-2],
        'ApellidoMaterno': parts[-1]
    }

def generate_complemento_notarios(data: Dict[str, Any]) -> NotariosPublicos:
    """
    Generates the NotariosPublicos complement.
    """
    op_data = data['complemento_notarios']

    # 1. DatosNotario (Fixed for Notaria 4)
    datos_notario = DatosNotario(
        curp="TOSR520601HCOLXX00", # Placeholder/Fixed
        num_notaria=4,
        entidad_federativa="06",
        adscripcion="MANZANILLO COLIMA"
    )

    # 2. DatosOperacion
    datos_operacion = DatosOperacion(
        num_instrumento_notarial=op_data['num_instrumento'],
        fecha_inst_notarial=op_data['fecha_inst_notarial'],
        monto_operacion=Decimal(str(op_data['monto_operacion'])),
        subtotal=Decimal(str(op_data['subtotal_operacion'])),
        iva=Decimal(str(op_data['iva_operacion'])) if op_data.get('iva_operacion') else Decimal('0.00')
    )

    # 3. DescInmuebles
    desc_inmuebles = [
        DescInmueble(
            tipo_inmueble=inm['tipo_inmueble'],
            calle=inm['calle'],
            no_exterior=inm['no_exterior'],
            no_interior=inm.get('no_interior'),
            codigo_postal=inm['codigo_postal'],
            municipio=inm['municipio'],
            estado=inm['estado'],
            pais=inm['pais']
        ) for inm in op_data['inmuebles']
    ]

    # 4. DatosAdquiriente
    coprops = data.get('copropietarios')
    datos_adquiriente = None

    if coprops and len(coprops) > 0:
        adquirientes_list = []
        for cop in coprops:
            # Prefer structured name if available
            nombre = sanitize_name(cop['nombre'])
            ap_paterno = sanitize_name(cop.get('apellido_paterno') or "")
            ap_materno = sanitize_name(cop.get('apellido_materno') or "")

            # If explicit surname not provided, try to split (fallback)
            if not ap_paterno and " " in nombre:
                split = split_name(nombre)
                nombre = split['Nombre']
                ap_paterno = split['ApellidoPaterno']
                ap_materno = split['ApellidoMaterno']

            adquirientes_list.append(DatosAdquirienteCopSC(
                nombre=nombre,
                apellido_paterno=ap_paterno if ap_paterno else None,
                apellido_materno=ap_materno if ap_materno else None,
                rfc=cop['rfc'],
                porcentaje=Decimal(str(cop['porcentaje']))
            ))
        datos_adquiriente = DatosAdquiriente(
            copro_soc_conyugal_e="Si",
            datos_adquirientes_cop_sc=adquirientes_list
        )
    else:
        # Single Adquiriente
        datos_adquiriente = DatosAdquiriente(
            copro_soc_conyugal_e="No",
            datos_un_adquiriente=DatosUnAdquiriente(
                nombre=sanitize_name(data['receptor']['nombre']),
                rfc=data['receptor']['rfc']
            )
        )

    # 5. DatosEnajenante
    enajenantes_data = op_data['enajenantes']
    datos_enajenante = None

    if len(enajenantes_data) > 1 or (len(enajenantes_data) == 1 and enajenantes_data[0].get('es_copropiedad')):
        enajenantes_list = []
        for enaj in enajenantes_data:
            enajenantes_list.append(DatosEnajenanteCopSC(
                nombre=sanitize_name(enaj['nombre']),
                rfc=enaj['rfc'],
                porcentaje=Decimal(str(enaj['porcentaje'])) if enaj.get('porcentaje') else Decimal('0.00')
            ))
        datos_enajenante = DatosEnajenante(
            copro_soc_conyugal_e="Si",
            datos_enajenantes_cop_sc=enajenantes_list
        )
    else:
        single_enaj = enajenantes_data[0]
        nombre = sanitize_name(single_enaj['nombre'])
        ap_paterno = sanitize_name(single_enaj.get('apellido_paterno') or "")
        ap_materno = sanitize_name(single_enaj.get('apellido_materno') or "")

        if not ap_paterno:
            # Fallback split
            split = split_name(nombre)
            nombre = split['Nombre']
            ap_paterno = split['ApellidoPaterno']
            ap_materno = split['ApellidoMaterno']

        # DatosUnEnajenante REQUIRES apellido_paterno
        datos_enajenante = DatosEnajenante(
            copro_soc_conyugal_e="No",
            datos_un_enajenante=DatosUnEnajenante(
                nombre=nombre,
                apellido_paterno=ap_paterno if ap_paterno else '.', # Fallback dot to satisfy Schema
                apellido_materno=ap_materno if ap_materno else None,
                rfc=single_enaj['rfc'],
                curp=single_enaj['curp']
            )
        )

    return NotariosPublicos(
        datos_notario=datos_notario,
        datos_operacion=datos_operacion,
        desc_inmuebles=desc_inmuebles,
        datos_adquiriente=datos_adquiriente,
        datos_enajenante=datos_enajenante
    )

def generate_signed_xml(invoice_data: Dict[str, Any]) -> bytes:
    """
    Generates a CFDI 4.0 XML object.
    """

    # 1. Pre-generation Validation
    if 'copropietarios' in invoice_data and invoice_data['copropietarios']:
        percentages = [Decimal(str(p['porcentaje'])) for p in invoice_data['copropietarios']]
        validate_copropiedad(percentages)

    if not cfdi40:
        logger.error("satcfdi library not found")
        return b"<error>satcfdi not available</error>"

    # 2. Prepare Conceptos with Taxes
    rfc_receptor = invoice_data['receptor']['rfc']
    is_persona_moral = len(rfc_receptor) == 12

    conceptos_processed = []

    for c in invoice_data['conceptos']:
        cantidad = Decimal(str(c['cantidad']))
        valor_unitario = Decimal(str(c['valor_unitario']))
        base = cantidad * valor_unitario

        concepto_dict = {
            'ClaveProdServ': c['clave_prod_serv'],
            'Cantidad': cantidad,
            'ClaveUnidad': c['clave_unidad'],
            'Descripcion': c['descripcion'],
            'ValorUnitario': valor_unitario,
            'ObjetoImp': c['objeto_imp']
        }

        if c['objeto_imp'] == '02':
            traslados = [
                {
                    'Base': base,
                    'Impuesto': '002', # IVA
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': Decimal('0.160000'),
                    'Importe': (base * Decimal('0.16')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                }
            ]

            retenciones = []
            if is_persona_moral:
                retenciones.append({
                    'Base': base,
                    'Impuesto': '001',
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': Decimal('0.100000'),
                    'Importe': (base * Decimal('0.10')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                })
                retenciones.append({
                    'Base': base,
                    'Impuesto': '002',
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': Decimal('0.106667'),
                    'Importe': (base * Decimal('0.106667')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                })

            impuestos_dict = {'Traslados': traslados}
            if retenciones:
                impuestos_dict['Retenciones'] = retenciones

            concepto_dict['Impuestos'] = impuestos_dict

        conceptos_processed.append(concepto_dict)

    # 3. Construct Comprobante
    try:
        complemento_obj = None
        if invoice_data.get('complemento_notarios'):
            complemento_obj = generate_complemento_notarios(invoice_data)

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
                'RegimenFiscalReceptor': '601'
            },
            conceptos=conceptos_processed,
            moneda='MXN',
            tipo_de_comprobante='I',
            lugar_expedicion='28200',
            exportacion='01',
            forma_pago='03',
            metodo_pago='PUE',
            complemento=complemento_obj
        )

        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e
