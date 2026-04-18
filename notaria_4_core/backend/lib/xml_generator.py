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

    # Process each concept to inject taxes
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

        impuestos_concepto = {}
        # If the concept is subject to tax
        if c['objeto_imp'] == '02':
            # Base for Traslados and Retenciones is the 'importe' of the concept
            base = importe

            # Traslados (IVA 16%)
            traslados = [{
                'Base': base,
                'Impuesto': '002',
                'TipoFactor': 'Tasa',
                'TasaOCuota': '0.160000',
                'Importe': base * Decimal('0.16')
            }]
            impuestos_concepto['Traslados'] = traslados

            # Retenciones (If applicable for Persona Moral)
            if retentions['is_moral']:
                ret_isr = base * Decimal("0.10")
                ret_iva = (base * Decimal("0.16")) * (Decimal("2") / Decimal("3"))
                retenciones = [
                    {
                        'Base': base,
                        'Impuesto': '001',
                        'TipoFactor': 'Tasa',
                        'TasaOCuota': '0.100000',
                        'Importe': ret_isr
                    },
                    {
                        'Base': base,
                        'Impuesto': '002',
                        'TipoFactor': 'Tasa',
                        'TasaOCuota': '0.106667',
                        'Importe': ret_iva
                    }
                ]
                impuestos_concepto['Retenciones'] = retenciones

        if impuestos_concepto:
            concepto_dict['Impuestos'] = impuestos_concepto

        conceptos.append(concepto_dict)

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
                'RegimenFiscalReceptor': '601' # Default
            },
            'conceptos': conceptos,
            'moneda': 'MXN',
            'tipo_de_comprobante': 'I',
            'lugar_expedicion': '28200',
            'exportacion': '01'
        }

        # 4. Complemento Notarios
        if invoice_data.get('complemento_notarios'):
            from .complement_notarios import create_complemento_notarios

            # Re-instantiate Pydantic model to ensure validation
            comp_model = ComplementoNotariosModel(**invoice_data['complemento_notarios'])
            complemento = create_complemento_notarios(comp_model)
            # satcfdi uses pascal case in Comprobante constructor but memory explicitly states
            # "Because `cfdi40.Comprobante` is a dictionary-like object that requires its nested
            # complements to be passed during initialization as kwargs, adding a complement dynamically
            # requires setting `cfdi_kwargs['complemento'] = complemento`"
            # And "The satcfdi v4 Comprobante constructor requires arguments to be in snake_case... unlike older versions"
            # However the code review suggests I should use Complemento if it matches the memory or schema. Wait, memory says:
            # "The satcfdi v4 Comprobante constructor requires arguments to be in snake_case (e.g., emisor, receptor, conceptos, lugar_expedicion), unlike older versions or XML node names which use PascalCase."
            cfdi_kwargs['complemento'] = complemento

        cfdi = cfdi40.Comprobante(**cfdi_kwargs)

        # 5. Signing
        signer = load_signer_from_secret_manager()
        if signer is None:
            raise ValueError("Signer could not be loaded from Secret Manager.")

        cfdi.sign(signer)
        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e
