from decimal import Decimal
import logging

from .fiscal_engine import validate_copropiedad, calculate_retentions, sanitize_name
from .security import load_signer_from_secret_manager

# Check for satcfdi availability
try:
    from satcfdi.create.cfd import cfdi40
except ImportError:
    cfdi40 = None

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
    # We re-calculate to ensure consistency with the fiscal engine
    retentions = calculate_retentions(invoice_data['receptor']['rfc'], Decimal(str(invoice_data['subtotal'])))

    # In CFDI 4.0, Impuestos on the root are calculated from Conceptos.
    # Therefore we must attach the Retenciones/Traslados to the Conceptos directly.
    conceptos_list = []

    for c in invoice_data['conceptos']:
        impuestos_concepto = {}
        # Apply retentions to honorarios (02) if applicable
        if retentions['is_moral'] and c['objeto_imp'] == '02':
            # Calculate proportionally or directly on the concept's value
            c_val = Decimal(str(c['importe']))
            c_isr = (c_val * Decimal("0.10")).quantize(Decimal("0.01"))
            # According to fiscal engine IVA_RETENTION_RATE_DIRECT is 0.106667
            c_iva_ret = (c_val * Decimal("0.106667")).quantize(Decimal("0.01"))
            c_iva_tras = (c_val * Decimal("0.16")).quantize(Decimal("0.01"))

            impuestos_concepto = {
                'Retenciones': [
                    {'Impuesto': '001', 'TipoFactor': 'Tasa', 'TasaOCuota': Decimal('0.100000'), 'Importe': c_isr, 'Base': c_val},
                    {'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': Decimal('0.106667'), 'Importe': c_iva_ret, 'Base': c_val}
                ],
                'Traslados': [
                    {'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': Decimal('0.160000'), 'Importe': c_iva_tras, 'Base': c_val}
                ]
            }
        elif c['objeto_imp'] == '02':
            c_val = Decimal(str(c['importe']))
            c_iva_tras = (c_val * Decimal("0.16")).quantize(Decimal("0.01"))
            impuestos_concepto = {
                'Traslados': [
                    {'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': Decimal('0.160000'), 'Importe': c_iva_tras, 'Base': c_val}
                ]
            }

        concepto = cfdi40.Concepto(
            clave_prod_serv=c['clave_prod_serv'],
            cantidad=Decimal(str(c['cantidad'])),
            clave_unidad=c['clave_unidad'],
            descripcion=c['descripcion'],
            valor_unitario=Decimal(str(c['valor_unitario'])),
            objeto_imp=c['objeto_imp']
            # Importe is calculated by satcfdi
        )
        if impuestos_concepto:
            concepto['Impuestos'] = impuestos_concepto

        conceptos_list.append(concepto)

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
                'Nombre': sanitize_name(invoice_data['receptor']['nombre']),
                'UsoCFDI': invoice_data['receptor']['uso_cfdi'],
                'DomicilioFiscalReceptor': invoice_data['receptor']['domicilio_fiscal'],
                'RegimenFiscalReceptor': invoice_data['receptor'].get('regimen_fiscal', '601')
            },
            conceptos=conceptos_list,
            tipo_de_comprobante='I',
            lugar_expedicion='28200',
            exportacion='01'
        )

        # 4. Complemento Notarios
        if 'complemento_notarios' in invoice_data and invoice_data['complemento_notarios']:
            # Lazy import to isolate satcfdi dependency handling
            from .complement_notarios import create_complemento_notarios
            from .api_models import ComplementoNotariosModel

            comp_model = ComplementoNotariosModel(**invoice_data['complemento_notarios'])
            complemento = create_complemento_notarios(comp_model)
            cfdi['Complemento'] = complemento

        # 5. Signing
        signer = load_signer_from_secret_manager()
        if signer:
            cfdi.sign(signer)
        else:
            logger.warning("No signer available. Returning unsigned XML bytes.")

        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e
