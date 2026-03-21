from decimal import Decimal
import logging

# Check for satcfdi availability
try:
    from satcfdi.create.cfd import cfdi40
except ImportError:
    cfdi40 = None

from .fiscal_engine import validate_copropiedad, calculate_retentions, sanitize_name, IVA_RETENTION_RATE_DIRECT
from .security import load_signer_from_secret_manager

logger = logging.getLogger(__name__)

def generate_signed_xml(invoice_data: dict) -> bytes:
    """
    Generates a CFDI 4.0 XML object.

    Current implementation builds the Comprobante structure using satcfdi.
    """

    # 1. Pre-generation Validation
    if 'copropietarios' in invoice_data and invoice_data['copropietarios']:
        percentages = [Decimal(str(p['porcentaje'])) for p in invoice_data['copropietarios']]
        validate_copropiedad(percentages)

    if not cfdi40:
        logger.error("satcfdi library not found")
        return b"<error>satcfdi not available</error>"

    # 2. Build Taxes (Impuestos)
    retentions = calculate_retentions(invoice_data['receptor']['rfc'], Decimal(str(invoice_data['subtotal'])))

    conceptos_list = []
    for c in invoice_data['conceptos']:
        concepto = {
            'ClaveProdServ': c['clave_prod_serv'],
            'Cantidad': Decimal(str(c['cantidad'])),
            'ClaveUnidad': c['clave_unidad'],
            'Descripcion': c['descripcion'],
            'ValorUnitario': Decimal(str(c['valor_unitario'])),
            'Importe': Decimal(str(c['importe'])),
            'ObjetoImp': c['objeto_imp']
        }

        # Inject taxes inside Concepto if applicable
        if c['objeto_imp'] == '02':
            # Base logic for Traslados
            traslado = {
                'Base': Decimal(str(c['importe'])),
                'Impuesto': '002',
                'TipoFactor': 'Tasa',
                'TasaOCuota': Decimal('0.160000'),
                'Importe': (Decimal(str(c['importe'])) * Decimal('0.16')).quantize(Decimal("0.01"))
            }
            impuestos_concepto = {'Traslados': [traslado]}

            # Apply retentions if Persona Moral
            if retentions['is_moral']:
                ret_isr = {
                    'Base': Decimal(str(c['importe'])),
                    'Impuesto': '001',
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': Decimal('0.100000'),
                    'Importe': (Decimal(str(c['importe'])) * Decimal('0.10')).quantize(Decimal("0.01"))
                }
                ret_iva = {
                    'Base': Decimal(str(c['importe'])),
                    'Impuesto': '002',
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': IVA_RETENTION_RATE_DIRECT,
                    'Importe': (Decimal(str(c['importe'])) * IVA_RETENTION_RATE_DIRECT).quantize(Decimal("0.01"))
                }
                impuestos_concepto['Retenciones'] = [ret_isr, ret_iva]

            concepto['Impuestos'] = impuestos_concepto

        conceptos_list.append(concepto)

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
                'RegimenFiscalReceptor': '601' # Default to General de Ley PM or logic needed
            },
            'conceptos': conceptos_list,
            'moneda': 'MXN',
            'tipo_de_comprobante': 'I',
            'lugar_expedicion': '28200',
            'exportacion': '01'
        }

        # Note: In satcfdi v4, SubTotal, Total, and global Impuestos are calculated automatically
        # so we don't pass them as kwargs to Comprobante constructor.

        cfdi = cfdi40.Comprobante(**kwargs)

        # 4. Complemento Notarios
        if 'complemento_notarios' in invoice_data and invoice_data['complemento_notarios']:
            # Lazy import to isolate dependency
            from .complement_notarios import create_complemento_notarios
            from .api_models import ComplementoNotariosModel

            comp_model = ComplementoNotariosModel(**invoice_data['complemento_notarios'])
            complemento = create_complemento_notarios(comp_model)
            cfdi['Complemento'] = complemento

        # 5. Signing
        signer = load_signer_from_secret_manager()
        if not signer:
            raise ValueError("Failed to retrieve cryptographic keys for signing.")

        cfdi.sign(signer)

        # Return the XML structure
        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e
