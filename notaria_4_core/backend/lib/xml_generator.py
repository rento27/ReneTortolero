from decimal import Decimal
import logging
from .security import load_signer_from_secret_manager

# Check for satcfdi availability
try:
    from satcfdi.create.cfd import cfdi40
except ImportError:
    cfdi40 = None

from .fiscal_engine import validate_copropiedad, calculate_retentions

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

    # Retrieve signer
    # signer = load_signer_from_secret_manager()
    # if signer is None:
    #    # For now in this environment without proper secrets, we bypass this if mock is not set,
    #    # but to be strict, if it's meant to be strict we raise:
    #    # raise ValueError("Signer could not be loaded from Secret Manager.")
    #    pass
    # We enforce strict check as requested: "raise a ValueError if load_signer_from_secret_manager() returns None to prevent silently generating unsigned XMLs."
    signer = load_signer_from_secret_manager()
    if signer is None:
        raise ValueError("Signer could not be loaded from Secret Manager.")

    retentions = calculate_retentions(invoice_data['receptor']['rfc'], Decimal(str(invoice_data['subtotal'])))

    # 2. Build Conceptos with Taxes injected inside
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

        impuestos_concepto = {}
        # Apply IVA Traslado if ObjetoImp is '02'
        if c['objeto_imp'] == '02':
            importe = Decimal(str(c['importe']))
            impuestos_concepto['Traslados'] = [{
                'Base': importe,
                'Impuesto': '002',
                'TipoFactor': 'Tasa',
                'TasaOCuota': '0.160000',
                'Importe': (importe * Decimal('0.16')).quantize(Decimal("0.01"))
            }]

            # Apply retentions proportionally if Persona Moral
            if retentions['is_moral']:
                impuestos_concepto['Retenciones'] = [
                    {
                        'Base': importe,
                        'Impuesto': '001',
                        'TipoFactor': 'Tasa',
                        'TasaOCuota': '0.100000',
                        'Importe': (importe * Decimal('0.10')).quantize(Decimal("0.01"))
                    },
                    {
                        'Base': importe,
                        'Impuesto': '002',
                        'TipoFactor': 'Tasa',
                        'TasaOCuota': '0.106667',
                        'Importe': (importe * Decimal('0.106667')).quantize(Decimal("0.01"))
                    }
                ]

        if impuestos_concepto:
            concepto_dict['Impuestos'] = impuestos_concepto

        conceptos.append(concepto_dict)


    # 3. Construct Comprobante
    # Using hardcoded Emisor for Notaria 4 as per prompt context
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
                'RegimenFiscalReceptor': '601' # Default to General de Ley PM or logic needed
            },
            conceptos=conceptos,
            moneda='MXN',
            tipo_de_comprobante='I',
            lugar_expedicion='28200',
            exportacion='01' # No aplica
        )

        # 4. Complemento Notarios
        if invoice_data.get('complemento_notarios'):
            # Lazy import
            from .complement_notarios import create_complemento_notarios
            from .api_models import ComplementoNotariosModel
            # Re-instantiate to ensure Pydantic validation
            comp_model = ComplementoNotariosModel(**invoice_data['complemento_notarios'])
            cfdi['Complemento'] = create_complemento_notarios(comp_model)

        # 5. Signing
        cfdi.sign(signer)

        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e
