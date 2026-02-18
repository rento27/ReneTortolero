from decimal import Decimal
import logging
import os

# Check for satcfdi availability
try:
    from satcfdi.create.cfd import cfdi40
    from satcfdi.models import Signer
except ImportError:
    cfdi40 = None
    Signer = None

from .fiscal_engine import validate_copropiedad, calculate_retentions, sanitize_name
from .complement_notarios import create_complemento_notarios
from .api_models import ComplementoNotariosModel

logger = logging.getLogger(__name__)

def load_signer_from_secret_manager():
    """
    Mocks loading the signer from Google Secret Manager.
    In production, this would use google-cloud-secret-manager.
    For now, returns None or a mock if environment variable MOCK_SIGNER is set.
    """
    # In a real implementation, we would fetch secrets here.
    return None

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
    impuestos = None
    retentions = calculate_retentions(invoice_data['receptor']['rfc'], Decimal(str(invoice_data['subtotal'])))

    if retentions['is_moral']:
        # Construct Impuestos node
        impuestos = {
            'Retenciones': [
                {'Impuesto': '001', 'Importe': retentions['isr']}, # ISR
                {'Impuesto': '002', 'Importe': retentions['iva']}  # IVA
            ]
        }
        # Note: satcfdi automatically calculates totals if structure is correct,
        # but passing explicit dictionaries is supported.

    # 3. Generate Complemento Notarios if present
    complemento = None
    if 'complemento_notarios' in invoice_data and invoice_data['complemento_notarios']:
        try:
            # Re-instantiate the model from the dict
            comp_model = ComplementoNotariosModel(**invoice_data['complemento_notarios'])
            complemento = create_complemento_notarios(comp_model)
        except Exception as e:
             logger.error(f"Error creating Complemento Notarios: {e}")
             raise ValueError(f"Error creating Complemento Notarios: {e}")

    # 4. Construct Comprobante
    try:
        cfdi = cfdi40.Comprobante(
            Emisor={
                'Rfc': 'TOSR520601AZ4',
                'RegimenFiscal': '612',
                'Nombre': 'RENE MANUEL TORTOLERO SANTILLANA'
            },
            Receptor={
                'Rfc': invoice_data['receptor']['rfc'],
                'Nombre': sanitize_name(invoice_data['receptor']['nombre']), # Double sanitize to be safe
                'UsoCFDI': invoice_data['receptor']['uso_cfdi'],
                'DomicilioFiscalReceptor': invoice_data['receptor']['domicilio_fiscal'],
                'RegimenFiscalReceptor': invoice_data['receptor'].get('regimen_fiscal', '601') # Default to General de Ley PM if not provided? Or 616?
                # Ideally this should be mandatory. For now using get.
            },
            Conceptos=[
                {
                    'ClaveProdServ': c['clave_prod_serv'],
                    'Cantidad': Decimal(str(c['cantidad'])),
                    'ClaveUnidad': c['clave_unidad'],
                    'Descripcion': c['descripcion'],
                    'ValorUnitario': Decimal(str(c['valor_unitario'])),
                    'Importe': Decimal(str(c['importe'])),
                    'ObjetoImp': c['objeto_imp']
                } for c in invoice_data['conceptos']
            ],
            SubTotal=Decimal(str(invoice_data['subtotal'])),
            Moneda='MXN',
            Total=Decimal(str(invoice_data['total'])),
            TipoDeComprobante='I',
            LugarExpedicion='28200',
            Impuestos=impuestos,
            Exportacion='01', # No aplica
            Complemento=complemento
        )

        # 5. Signing
        signer = load_signer_from_secret_manager()
        if signer:
            cfdi.sign(signer)
        else:
            # If no signer, we can't generate the Sello/Certificado attributes fully,
            # but we can output the XML structure.
            pass

        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e
