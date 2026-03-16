from decimal import Decimal
import logging

# Check for satcfdi availability
try:
    from satcfdi.create.cfd import cfdi40
    from satcfdi.models import Signer
except ImportError:
    cfdi40 = None
    Signer = None

import base64
from .fiscal_engine import validate_copropiedad, calculate_retentions
from .api_models import ComplementoNotariosModel

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

    # 2. Build Conceptos with Taxes per concept
    conceptos = []
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

        if c['objeto_imp'] == '02':
            # Calculate retentions specifically for this concept's importe
            concept_retentions = calculate_retentions(invoice_data['receptor']['rfc'], importe)

            impuestos_concepto = {
                'Traslados': [
                    {'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': '0.160000', 'Base': importe, 'Importe': (importe * Decimal('0.16')).quantize(Decimal("0.01"))}
                ]
            }
            if concept_retentions['is_moral']:
                impuestos_concepto['Retenciones'] = [
                    {'Impuesto': '001', 'TipoFactor': 'Tasa', 'TasaOCuota': '0.100000', 'Base': importe, 'Importe': concept_retentions['isr']},
                    {'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': '0.106667', 'Base': importe, 'Importe': concept_retentions['iva']}
                ]

            concepto['Impuestos'] = impuestos_concepto

        conceptos.append(concepto)

    # 3. Construct Complemento Notarios (if available)
    complemento_node = None
    if 'complemento_notarios' in invoice_data:
        from .complement_notarios import create_complemento_notarios
        comp_model = ComplementoNotariosModel(**invoice_data['complemento_notarios'])
        complemento_node = create_complemento_notarios(comp_model)

    # 4. Construct Comprobante
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
                'RegimenFiscalReceptor': '601' # Default to General de Ley PM
            },
            conceptos=conceptos,
            moneda='MXN',
            tipo_de_comprobante='I',
            lugar_expedicion='28200',
            exportacion='01',
            complemento=complemento_node
        )

        # 5. Signing
        from .security import load_signer_from_secret_manager
        signer = load_signer_from_secret_manager()
        if signer:
            cfdi.sign(signer)

        # Return the base64 XML structure
        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e
