from decimal import Decimal
import logging

from .fiscal_engine import validate_copropiedad, calculate_retentions
from .fiscal_engine import sanitize_name

logger = logging.getLogger(__name__)

def generate_signed_xml(invoice_data: dict) -> bytes:
    # Check for satcfdi availability
    try:
        from satcfdi.create.cfd import cfdi40
        from satcfdi.models import Signer
    except ImportError:
        cfdi40 = None
        Signer = None

    try:
        from .complement_notarios import create_complemento_notarios
        from .api_models import ComplementoNotariosModel
    except ImportError:
        create_complemento_notarios = None

    from .security import load_signer_from_secret_manager

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
    # Re-calculate retentions for Persona Moral
    subtotal = Decimal(str(invoice_data['subtotal']))
    retentions = calculate_retentions(invoice_data['receptor']['rfc'], subtotal)

    conceptos = []
    for c in invoice_data['conceptos']:
        cantidad = Decimal(str(c['cantidad']))
        valor_unitario = Decimal(str(c['valor_unitario']))

        # Determine base for this concept
        base = cantidad * valor_unitario

        concepto_dict = {
            'ClaveProdServ': c['clave_prod_serv'],
            'Cantidad': cantidad,
            'ClaveUnidad': c['clave_unidad'],
            'Descripcion': c['descripcion'],
            'ValorUnitario': valor_unitario,
            'ObjetoImp': c['objeto_imp']
        }

        # Attach retentions for PM directly to the Concepto if it's PM
        if retentions['is_moral'] and c['objeto_imp'] == '02':
            # This is an approximation. Retentions should be calculated per concept base
            concepto_retentions = calculate_retentions(invoice_data['receptor']['rfc'], base)
            concepto_dict['impuestos'] = {
                'Retenciones': [
                    {'Impuesto': '001', 'Importe': concepto_retentions['isr'], 'TasaOCuota': Decimal('0.100000'), 'Base': base, 'TipoFactor': 'Tasa'},
                    {'Impuesto': '002', 'Importe': concepto_retentions['iva'], 'TasaOCuota': Decimal('0.106667'), 'Base': base, 'TipoFactor': 'Tasa'}
                ],
                'Traslados': [
                    {'Impuesto': '002', 'Importe': (base * Decimal('0.16')).quantize(Decimal("0.01")), 'TasaOCuota': Decimal('0.160000'), 'Base': base, 'TipoFactor': 'Tasa'}
                ]
            }
        elif c['objeto_imp'] == '02':
            concepto_dict['impuestos'] = {
                'Traslados': [
                    {'Impuesto': '002', 'Importe': (base * Decimal('0.16')).quantize(Decimal("0.01")), 'TasaOCuota': Decimal('0.160000'), 'Base': base, 'TipoFactor': 'Tasa'}
                ]
            }

        conceptos.append(concepto_dict)

    # 3. Construct Comprobante using snake_case args
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
            conceptos=conceptos,
            moneda='MXN',
            tipo_de_comprobante='I',
            lugar_expedicion='28200',
            exportacion='01'
        )

        # 4. Complemento Notarios
        if 'complemento_notarios' in invoice_data and invoice_data['complemento_notarios'] is not None and create_complemento_notarios:
            comp_model = ComplementoNotariosModel(**invoice_data['complemento_notarios'])
            complemento = create_complemento_notarios(comp_model)
            cfdi.add_complemento(complemento)

        # 5. Signing
        signer = load_signer_from_secret_manager()
        if signer:
            cfdi.sign(signer)

        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e
