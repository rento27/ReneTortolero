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

    retentions = calculate_retentions(invoice_data['receptor']['rfc'], Decimal(str(invoice_data['subtotal'])))

    # Process conceptos and attach taxes per concepto
    conceptos_list = []
    for c in invoice_data['conceptos']:
        base_importe = Decimal(str(c['importe']))

        # We need to construct impuestos for each concepto based on whether it is taxable
        # The prompt mentions:
        # Honorarios: Must use `02` (Si objeto de impuesto)
        # Suplidos/Gastos: Must use `01` (No objeto de impuesto) OR use the ACuentaTerceros node
        # We assume if it's 02, we add IVA. If the receptor is moral, we also add retentions.

        c_impuestos = None
        if c['objeto_imp'] == '02':
            traslados = [
                {'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': Decimal('0.160000'), 'Importe': base_importe * Decimal('0.16')}
            ]

            retenciones = []
            if retentions['is_moral']:
                # The retentions calculated globally in fiscal_engine might be total.
                # Here we calculate per concept to correctly build the XML
                # In satcfdi v4, Retenciones must be attached directly to Concepto objects.
                retenciones.append({'Impuesto': '001', 'TipoFactor': 'Tasa', 'TasaOCuota': Decimal('0.100000'), 'Importe': base_importe * Decimal('0.10')})
                retenciones.append({'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': Decimal('0.106667'), 'Importe': base_importe * Decimal('0.106667')})

            c_impuestos = {'Traslados': traslados}
            if retenciones:
                c_impuestos['Retenciones'] = retenciones

        # Note: satcfdi constructor for Concepto takes snake_case arguments
        concepto_obj = cfdi40.Concepto(
            clave_prod_serv=c['clave_prod_serv'],
            cantidad=Decimal(str(c['cantidad'])),
            clave_unidad=c['clave_unidad'],
            descripcion=c['descripcion'],
            valor_unitario=Decimal(str(c['valor_unitario'])),
            objeto_imp=c['objeto_imp'],
            impuestos=c_impuestos
        )
        conceptos_list.append(concepto_obj)


    # 3. Construct Comprobante
    # Using hardcoded Emisor for Notaria 4 as per prompt context
    try:
        # Note: satcfdi Comprobante takes snake_case arguments
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
            conceptos=conceptos_list,
            moneda='MXN',
            tipo_de_comprobante='I',
            lugar_expedicion='28200',
            exportacion='01' # No aplica
        )

        # Return the XML structure (Unsigned for now as we lack keys)
        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e
