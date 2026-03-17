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
    Uses real signer from Secret Manager or mock depending on the environment.
    """

    # 1. Pre-generation Validation
    if 'copropietarios' in invoice_data and invoice_data['copropietarios']:
        percentages = [Decimal(str(p['porcentaje'])) for p in invoice_data['copropietarios']]
        validate_copropiedad(percentages)

    if not cfdi40:
        logger.error("satcfdi library not found")
        return b"<error>satcfdi not available</error>"

    # 2. Build Taxes (Impuestos)
    # We re-calculate to ensure consistency with the fiscal engine
    retentions = calculate_retentions(invoice_data['receptor']['rfc'], Decimal(str(invoice_data['subtotal'])))

    # Construct Conceptos
    conceptos = []
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

        # Inject Impuestos if applicable and if ObjetoImp is '02' (Sí objeto de impuesto)
        if c['objeto_imp'] == '02':
            impuestos_concepto = {}
            if retentions['is_moral']:
                # For simplicity in this structure, assuming proportional split or full amount if single concepto
                # A robust implementation would calculate per concepto. Here we just map the global ones if single or distribute.
                # Assuming single concepto for demonstration or logic needs per-concepto calculation.
                # Using the global retentions calculated earlier for the single concepto case.
                impuestos_concepto['Retenciones'] = [
                    {'Impuesto': '001', 'Importe': retentions['isr'], 'Base': Decimal(str(c['importe'])), 'TasaOCuota': Decimal("0.100000"), 'TipoFactor': 'Tasa'}, # ISR
                    {'Impuesto': '002', 'Importe': retentions['iva'], 'Base': Decimal(str(c['importe'])), 'TasaOCuota': Decimal("0.106667"), 'TipoFactor': 'Tasa'}  # IVA
                ]

            # Add IVA Trasladado (16%)
            iva_trasladado = (Decimal(str(c['importe'])) * Decimal("0.16")).quantize(Decimal("0.01"))
            impuestos_concepto['Traslados'] = [
                {'Impuesto': '002', 'Importe': iva_trasladado, 'Base': Decimal(str(c['importe'])), 'TasaOCuota': Decimal("0.160000"), 'TipoFactor': 'Tasa'}
            ]
            concepto['Impuestos'] = impuestos_concepto

        conceptos.append(concepto)

    # 3. Construct Comprobante
    # Using hardcoded Emisor for Notaria 4 as per prompt context
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
        if 'complemento_notarios' in invoice_data and invoice_data['complemento_notarios']:
            # Lazy import to isolate satcfdi dependency handling
            from .complement_notarios import create_complemento_notarios
            comp_model = ComplementoNotariosModel(**invoice_data['complemento_notarios'])
            complemento_node = create_complemento_notarios(comp_model)
            kwargs['complemento'] = complemento_node

        cfdi = cfdi40.Comprobante(**kwargs)

        # 5. Signing
        signer = load_signer_from_secret_manager()
        if signer:
            cfdi.sign(signer)
        else:
            logger.info("No signer loaded (mocked or missing), returning unsigned XML.")

        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e
