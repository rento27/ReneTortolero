from decimal import Decimal
import logging

# Check for satcfdi availability
try:
    from satcfdi.create.cfd import cfdi40
except ImportError:
    cfdi40 = None

from .fiscal_engine import validate_copropiedad, calculate_retentions
from .api_models import ComplementoNotariosModel
from .security import load_signer_from_secret_manager

logger = logging.getLogger(__name__)

def generate_signed_xml(invoice_data: dict) -> bytes:
    """
    Generates a CFDI 4.0 XML object.

    Current implementation builds the Comprobante structure using satcfdi.
    Note: Signing is mocked as we do not have valid CSD certificates in this environment.
    """

    # 1. Pre-generation Validation
    if 'copropietarios' in invoice_data and invoice_data['copropietarios']:
        percentages = [Decimal(str(p['porcentaje'])) for p in invoice_data['copropietarios']]
        validate_copropiedad(percentages)

    if not cfdi40:
        logger.error("satcfdi library not found")
        return b"<error>satcfdi not available</error>"

    # 2. Build Taxes (Impuestos) directly inside Concepto
    # satcfdi v4 requires Concepto and automatically calculates totals from it.
    conceptos = []

    for c in invoice_data['conceptos']:
        concepto_impuestos = {}
        subtotal_c = Decimal(str(c['importe']))
        retentions = calculate_retentions(invoice_data['receptor']['rfc'], subtotal_c)

        if retentions['is_moral']:
             concepto_impuestos['Retenciones'] = [
                 {'Impuesto': '001', 'TasaOCuota': Decimal('0.100000'), 'Importe': retentions['isr'], 'Base': subtotal_c, 'TipoFactor': 'Tasa'},
                 {'Impuesto': '002', 'TasaOCuota': Decimal('0.106667'), 'Importe': retentions['iva'], 'Base': subtotal_c, 'TipoFactor': 'Tasa'}
             ]

        # Add IVA Traslado if necessary (hardcoded to 16% for simplicity in this example)
        if c['objeto_imp'] == '02':
             concepto_impuestos['Traslados'] = [
                 {'Impuesto': '002', 'TasaOCuota': Decimal('0.160000'), 'Importe': (subtotal_c * Decimal('0.16')).quantize(Decimal("0.01")), 'Base': subtotal_c, 'TipoFactor': 'Tasa'}
             ]

        concepto_dict = {
             'ClaveProdServ': c['clave_prod_serv'],
             'Cantidad': Decimal(str(c['cantidad'])),
             'ClaveUnidad': c['clave_unidad'],
             'Descripcion': c['descripcion'],
             'ValorUnitario': Decimal(str(c['valor_unitario'])),
             'ObjetoImp': c['objeto_imp']
        }

        if concepto_impuestos:
             concepto_dict['Impuestos'] = concepto_impuestos

        conceptos.append(concepto_dict)

    # 3. Construct Comprobante using v4 snake_case
    try:
        kwargs = {
            'emisor': {
                'Rfc': 'TOSR520601AZ4',
                'RegimenFiscal': '612',
                'Nombre': 'RENE MANUEL TORTOLERO SANTILLANA'
            },
            'receptor': {
                'Rfc': invoice_data['receptor']['rfc'],
                'Nombre': invoice_data['receptor']['nombre'],
                'UsoCFDI': invoice_data['receptor']['uso_cfdi'],
                'DomicilioFiscalReceptor': invoice_data['receptor']['domicilio_fiscal'],
                'RegimenFiscalReceptor': invoice_data['receptor']['regimen_fiscal']
            },
            'conceptos': conceptos,
            'moneda': 'MXN',
            'tipo_de_comprobante': 'I',
            'lugar_expedicion': '28200',
            'exportacion': '01' # No aplica
        }

        # 4. Complemento Notarios
        if 'complemento_notarios' in invoice_data and invoice_data['complemento_notarios']:
             from .complement_notarios import create_complemento_notarios
             comp_model = ComplementoNotariosModel(**invoice_data['complemento_notarios'])
             kwargs['complemento'] = create_complemento_notarios(comp_model)

        cfdi = cfdi40.Comprobante(**kwargs)

        # 5. Signing
        signer = load_signer_from_secret_manager()
        if signer:
             cfdi.sign(signer)

        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e
