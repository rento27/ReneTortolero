from decimal import Decimal
import logging

from .fiscal_engine import validate_copropiedad, calculate_retentions
from .security import load_signer_from_secret_manager

logger = logging.getLogger(__name__)

# Check for satcfdi availability
try:
    from satcfdi.create.cfd import cfdi40
except ImportError:
    cfdi40 = None


def generate_signed_xml(invoice_data: dict) -> bytes:
    """
    Generates a CFDI 4.0 XML object using satcfdi.
    Raises ValueError if `load_signer_from_secret_manager()` returns None.
    """
    if not cfdi40:
        logger.error("satcfdi library not found")
        return b"<error>satcfdi not available</error>"

    signer = load_signer_from_secret_manager()
    if signer is None:
        raise ValueError("Could not load signer. MOCK_SIGNER might be set or secrets are unavailable.")

    # 1. Pre-generation Validation
    if 'copropietarios' in invoice_data and invoice_data['copropietarios']:
        percentages = [Decimal(str(p['porcentaje'])) for p in invoice_data['copropietarios']]
        validate_copropiedad(percentages)

    retentions = calculate_retentions(invoice_data['receptor']['rfc'], Decimal(str(invoice_data['subtotal'])))

    # 2. Build Conceptos with their respective Impuestos
    conceptos = []
    for c in invoice_data['conceptos']:
        importe = Decimal(str(c['importe']))
        concepto_dict = {
            'ClaveProdServ': c['clave_prod_serv'],
            'Cantidad': Decimal(str(c['cantidad'])),
            'ClaveUnidad': c['clave_unidad'],
            'Descripcion': c['descripcion'],
            'ValorUnitario': Decimal(str(c['valor_unitario'])),
            'Importe': importe,
            'ObjetoImp': c['objeto_imp']
        }

        # Determine Impuestos for this Concepto
        # As per satcfdi v4 and CFDI 4.0 rules, taxes are nested in Concepto
        impuestos_dict = {}
        if c['objeto_imp'] == '02':
            # Traslados (IVA 16%)
            impuestos_dict['Traslados'] = [{
                'Base': importe,
                'Impuesto': '002',
                'TipoFactor': 'Tasa',
                'TasaOCuota': '0.160000',
                'Importe': importe * Decimal('0.16')
            }]

            # Retenciones (If Persona Moral)
            if retentions['is_moral']:
                impuestos_dict['Retenciones'] = [
                    {'Base': importe, 'Impuesto': '001', 'TipoFactor': 'Tasa', 'TasaOCuota': '0.100000', 'Importe': importe * Decimal('0.10')},
                    {'Base': importe, 'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': '0.106667', 'Importe': importe * Decimal('0.106667')}
                ]

        if impuestos_dict:
            concepto_dict['Impuestos'] = impuestos_dict

        conceptos.append(concepto_dict)

    # 3. Construct Comprobante
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
                'RegimenFiscalReceptor': '601' # Default to General de Ley PM or logic needed
            },
            'conceptos': conceptos,
            'moneda': 'MXN',
            'tipo_de_comprobante': 'I',
            'lugar_expedicion': '28200',
            'exportacion': '01' # No aplica
        }

        # 4. Complemento Notarios
        if invoice_data.get('complemento_notarios'):
            # Lazy import to isolate satcfdi dependency handling
            from .complement_notarios import create_complemento_notarios
            from .api_models import ComplementoNotariosModel

            # Re-instantiate the Pydantic model from dict to ensure validation
            comp_model = ComplementoNotariosModel(**invoice_data['complemento_notarios'])
            complemento = create_complemento_notarios(comp_model)
            kwargs['complemento'] = complemento

        cfdi = cfdi40.Comprobante(**kwargs)

        # 5. Signing
        cfdi.sign(signer=signer)

        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e
