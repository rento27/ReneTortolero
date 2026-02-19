from decimal import Decimal
import logging
from .fiscal_engine import validate_copropiedad, calculate_retentions, IVA_RETENTION_RATE_DIRECT
from .security import load_signer_from_secret_manager

# Check for satcfdi availability
try:
    from satcfdi.create.cfd import cfdi40
except ImportError:
    cfdi40 = None

logger = logging.getLogger(__name__)

def generate_signed_xml(invoice_data: dict, complemento=None) -> bytes:
    """
    Generates a CFDI 4.0 XML object.

    Args:
        invoice_data: Dictionary with invoice data (from InvoiceRequest.model_dump())
        complemento: Optional satcfdi complement object (e.g. NotariosPublicos)
    """

    # 1. Pre-generation Validation
    if 'copropietarios' in invoice_data and invoice_data['copropietarios']:
        percentages = [Decimal(str(p['porcentaje'])) for p in invoice_data['copropietarios']]
        validate_copropiedad(percentages)

    if not cfdi40:
        logger.error("satcfdi library not found")
        return b"<error>satcfdi not available</error>"

    # 2. Build Concepts and Taxes
    is_moral = len(invoice_data['receptor']['rfc']) == 12
    concepts = []

    for c in invoice_data['conceptos']:
        c_args = {
            'clave_prod_serv': c['clave_prod_serv'],
            'cantidad': Decimal(str(c['cantidad'])),
            'clave_unidad': c['clave_unidad'],
            'descripcion': c['descripcion'],
            'valor_unitario': Decimal(str(c['valor_unitario'])),
            'objeto_imp': c['objeto_imp']
        }

        # Add Taxes if ObjetoImp is 02
        if c['objeto_imp'] == '02':
            traslados = []
            retenciones = []

            # IVA 16%
            traslados.append({
                'Impuesto': '002',
                'TasaOCuota': Decimal('0.160000'),
                'TipoFactor': 'Tasa'
            })

            if is_moral:
                # ISR 10%
                retenciones.append({
                    'Impuesto': '001',
                    'TasaOCuota': Decimal('0.100000'),
                    'TipoFactor': 'Tasa'
                })
                # IVA Retention
                retenciones.append({
                    'Impuesto': '002',
                    'TasaOCuota': IVA_RETENTION_RATE_DIRECT,
                    'TipoFactor': 'Tasa'
                })

            c_args['impuestos'] = {
                'Traslados': traslados,
                'Retenciones': retenciones
            }

        concepts.append(cfdi40.Concepto(**c_args))

    # 3. Construct Comprobante
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
                'RegimenFiscalReceptor': invoice_data['receptor'].get('regimen_fiscal', '601')
            },
            conceptos=concepts,
            moneda='MXN',
            lugar_expedicion='28200',
            tipo_de_comprobante='I',
            exportacion='01',
            complemento=complemento
        )

        # 5. Signing
        signer = load_signer_from_secret_manager()

        if signer:
             cfdi.sign(signer)
        else:
             logger.warning("No signer available (MOCK_SIGNER=True or no creds), returning XML unsigned.")
             # If unsigned, the XML structure is valid but lacks Sello.

        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e
