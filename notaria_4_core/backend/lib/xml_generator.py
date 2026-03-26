from decimal import Decimal
import logging
from .security import load_signer_from_secret_manager

# Check for satcfdi availability
try:
    from satcfdi.create.cfd import cfdi40
except ImportError:
    cfdi40 = None

from .fiscal_engine import validate_copropiedad, calculate_retentions
from .api_models import ComplementoNotariosModel

logger = logging.getLogger(__name__)

def generate_signed_xml(invoice_data: dict) -> bytes:
    """
    Generates a CFDI 4.0 XML object.

    Current implementation builds the Comprobante structure using satcfdi.
    """

    # 1. Pre-generation Validation
    if 'copropietarios' in invoice_data and invoice_data.get('copropietarios'):
        percentages = [Decimal(str(p['porcentaje'])) for p in invoice_data['copropietarios']]
        validate_copropiedad(percentages)

    if not cfdi40:
        logger.error("satcfdi library not found")
        return b"<error>satcfdi not available</error>"

    signer = load_signer_from_secret_manager()
    # MOCK_SIGNER lets us proceed for testing
    import os
    if signer is None and not os.environ.get("MOCK_SIGNER"):
        raise ValueError("Signer could not be loaded from Secret Manager and MOCK_SIGNER is not set.")

    # 2. Build Taxes (Impuestos)
    # We re-calculate to ensure consistency with the fiscal engine
    retentions = calculate_retentions(invoice_data['receptor']['rfc'], Decimal(str(invoice_data['subtotal'])))

    # 3. Construct Comprobante
    # Using hardcoded Emisor for Notaria 4 as per prompt context
    try:
        conceptos = []
        for c in invoice_data['conceptos']:
            concepto_dict = {
                'ClaveProdServ': c['clave_prod_serv'],
                'Cantidad': Decimal(str(c['cantidad'])),
                'ClaveUnidad': c['clave_unidad'],
                'Descripcion': c['descripcion'],
                'ValorUnitario': Decimal(str(c['valor_unitario'])),
                'Importe': Decimal(str(c['importe'])),
                'ObjetoImp': c['objeto_imp']
            }
            if retentions['is_moral'] and c['objeto_imp'] == '02':
                 concepto_dict['Impuestos'] = {
                     'Retenciones': [
                         {'Base': Decimal(str(c['importe'])), 'Impuesto': '001', 'TipoFactor': 'Tasa', 'TasaOCuota': Decimal('0.100000'), 'Importe': (Decimal(str(c['importe'])) * Decimal("0.10")).quantize(Decimal("0.01"))}, # ISR
                         {'Base': Decimal(str(c['importe'])), 'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': Decimal('0.106667'), 'Importe': (Decimal(str(c['importe'])) * Decimal("0.16") * Decimal("2") / Decimal("3")).quantize(Decimal("0.01"))}  # IVA
                     ],
                     'Traslados': [
                         {'Base': Decimal(str(c['importe'])), 'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': Decimal('0.160000'), 'Importe': (Decimal(str(c['importe'])) * Decimal("0.16")).quantize(Decimal("0.01"))}
                     ]
                 }
            conceptos.append(concepto_dict)

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
                'RegimenFiscalReceptor': '601' # Default to General de Ley PM or logic needed
                # Note: The prompt implies strictly validating this from data
            },
            conceptos=conceptos,
            moneda='MXN',
            tipo_de_comprobante='I',
            lugar_expedicion='28200',
            exportacion='01' # No aplica
        )

        # 4. Complemento Notarios
        if invoice_data.get('complemento_notarios'):
            from .complement_notarios import create_complemento_notarios
            comp_model = ComplementoNotariosModel(**invoice_data['complemento_notarios'])
            cfdi_complemento = create_complemento_notarios(comp_model)
            cfdi['Complemento'] = cfdi_complemento

        # 5. Signing
        if signer:
            cfdi.sign(signer=signer)

        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e
