from decimal import Decimal
import logging

# Check for satcfdi availability
try:
    from satcfdi.create.cfd import cfdi40
except ImportError:
    cfdi40 = None

from decimal import ROUND_HALF_UP
from .fiscal_engine import validate_copropiedad, calculate_retentions, ISR_RETENTION_RATE, IVA_RETENTION_RATE_DIRECT
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

    # 2. Construct Conceptos with injected Taxes
    is_moral = len(invoice_data['receptor']['rfc'].strip()) == 12

    conceptos_list = []
    for c in invoice_data['conceptos']:
        importe = Decimal(str(c['importe']))
        concepto = {
            'ClaveProdServ': c['clave_prod_serv'],
            'Cantidad': Decimal(str(c['cantidad'])),
            'ClaveUnidad': c['clave_unidad'],
            'Descripcion': c['descripcion'],
            'ValorUnitario': Decimal(str(c['valor_unitario'])),
            'Importe': importe,
            'ObjetoImp': c['objeto_imp']
        }

        # Inject Impuestos if applicable and if ObjetoImp is 02
        if c['objeto_imp'] == '02':
            # Always add Traslados for ObjetoImp = 02
            iva_traslado = (importe * Decimal("0.16")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            impuestos_dict = {
                'Traslados': [
                    {
                        'Base': importe,
                        'Impuesto': '002',
                        'TipoFactor': 'Tasa',
                        'TasaOCuota': Decimal("0.160000"),
                        'Importe': iva_traslado
                    }
                ]
            }

            if is_moral:
                # Concept-level retentions with required CFDI 4.0 attributes
                isr_ret = (importe * ISR_RETENTION_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                # Base for IVA retention is the subtotal (importe), not the tax amount.
                iva_ret = (importe * IVA_RETENTION_RATE_DIRECT).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                impuestos_dict['Retenciones'] = [
                    {
                        'Base': importe,
                        'Impuesto': '001',
                        'TipoFactor': 'Tasa',
                        'TasaOCuota': ISR_RETENTION_RATE.quantize(Decimal("0.000000")),
                        'Importe': isr_ret
                    },
                    {
                        'Base': importe,
                        'Impuesto': '002',
                        'TipoFactor': 'Tasa',
                        'TasaOCuota': Decimal("0.106667"),
                        'Importe': iva_ret
                    }
                ]

            concepto['Impuestos'] = impuestos_dict
        conceptos_list.append(concepto)

    # 3. Construct Comprobante
    try:
        cfdi_kwargs = {
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
            'conceptos': conceptos_list,
            'moneda': 'MXN',
            'tipo_de_comprobante': 'I',
            'lugar_expedicion': '28200',
            'exportacion': '01'
        }

        cfdi = cfdi40.Comprobante(**cfdi_kwargs)

        # 4. Complemento Notarios
        if invoice_data.get('complemento_notarios'):
            # Lazy import
            from .complement_notarios import create_complemento_notarios
            comp_data = invoice_data['complemento_notarios']
            if isinstance(comp_data, dict):
                comp_model = ComplementoNotariosModel(**comp_data)
            else:
                comp_model = comp_data # Already a Pydantic model
            cfdi['Complemento'] = create_complemento_notarios(comp_model)

        # 5. Signing
        signer = load_signer_from_secret_manager()
        if signer is None and not __import__('os').environ.get("MOCK_SIGNER"):
             raise ValueError("Failed to load signer. XML cannot be signed.")

        if signer is not None:
             cfdi.sign(signer)

        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e
