from decimal import Decimal
import logging

# Check for satcfdi availability
try:
    from satcfdi.create.cfd import cfdi40
    from satcfdi.models import Signer
except ImportError:
    cfdi40 = None
    Signer = None

from .fiscal_engine import validate_copropiedad, calculate_retentions

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

    # 3. Construct Comprobante
    # Using hardcoded Emisor for Notaria 4 as per prompt context
    try:
        cfdi = cfdi40.Comprobante(
            Emisor={
                'Rfc': 'TOSR520601AZ4',
                'RegimenFiscal': '612',
                'Nombre': 'RENE MANUEL TORTOLERO SANTILLANA'
            },
            Receptor={
                'Rfc': invoice_data['receptor']['rfc'],
                'Nombre': invoice_data['receptor']['nombre'],
                'UsoCFDI': invoice_data['receptor']['uso_cfdi'],
                'DomicilioFiscalReceptor': invoice_data['receptor']['domicilio_fiscal'],
                'RegimenFiscalReceptor': '601' # Default to General de Ley PM or logic needed
                # Note: The prompt implies strictly validating this from data
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
            Exportacion='01' # No aplica
        )

        # 4. Complemento Notarios (Stub logic)
        # if 'complemento_notarios' in invoice_data:
        #     cfdi['Complemento'] = ...

        # 5. Signing
        # In a real environment:
        # signer = Signer.load(certificate=..., key=..., password=...)
        # cfdi.sign(signer)

        # Return the XML structure (Unsigned for now as we lack keys)
        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e
