from decimal import Decimal
import logging
from .api_models import ComplementoNotariosModel

# Check for satcfdi availability
try:
    from satcfdi.create.cfd import cfdi40
except ImportError:
    cfdi40 = None

from .fiscal_engine import validate_copropiedad, calculate_retentions, sanitize_name
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

    # 2. Build Taxes (Impuestos)
    # We calculate subtotal directly from concepts for retention calculation
    # In satcfdi v4, Comprobante computes Total, SubTotal and Impuestos automatically
    subtotal = sum(Decimal(str(c['cantidad'])) * Decimal(str(c['valor_unitario'])) for c in invoice_data['conceptos'])
    impuestos = None
    retentions = calculate_retentions(invoice_data['receptor']['rfc'], subtotal)

    if retentions['is_moral']:
        # Construct Impuestos node
        impuestos = {
            'Retenciones': [
                {'Impuesto': '001', 'Importe': retentions['isr']}, # ISR
                {'Impuesto': '002', 'Importe': retentions['iva']}  # IVA
            ]
        }

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
                'Nombre': sanitize_name(invoice_data['receptor']['nombre']),
                'UsoCFDI': invoice_data['receptor']['uso_cfdi'],
                'DomicilioFiscalReceptor': invoice_data['receptor']['domicilio_fiscal'],
                'RegimenFiscalReceptor': invoice_data['receptor']['regimen_fiscal']
            },
            'conceptos': [
                {
                    'ClaveProdServ': c['clave_prod_serv'],
                    'Cantidad': Decimal(str(c['cantidad'])),
                    'ClaveUnidad': c['clave_unidad'],
                    'Descripcion': c['descripcion'],
                    'ValorUnitario': Decimal(str(c['valor_unitario'])),
                    'ObjetoImp': c['objeto_imp']
                } for c in invoice_data['conceptos']
            ],
            'moneda': 'MXN',
            'tipo_de_comprobante': 'I',
            'lugar_expedicion': '28200',
            'exportacion': '01' # No aplica
        }

        if impuestos:
            kwargs['impuestos'] = impuestos

        # 4. Complemento Notarios
        if invoice_data.get('complemento_notarios'):
            from .complement_notarios import create_complemento_notarios
            comp_model = ComplementoNotariosModel(**invoice_data['complemento_notarios'])
            complemento = create_complemento_notarios(comp_model)
            if complemento:
                kwargs['complemento'] = complemento

        cfdi = cfdi40.Comprobante(**kwargs)

        # 5. Signing
        signer = load_signer_from_secret_manager()
        if signer:
            cfdi.sign(signer)

        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e
