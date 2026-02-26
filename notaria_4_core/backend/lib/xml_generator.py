from decimal import Decimal, ROUND_HALF_UP
import logging

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
from .security import load_signer_from_secret_manager

logger = logging.getLogger(__name__)

def generate_signed_xml(invoice_data: dict) -> bytes:
    """
    Generates a CFDI 4.0 XML object.
    """

    if not cfdi40:
        logger.error("satcfdi library not found")
        return b"<error>satcfdi not available</error>"

    # 1. Determine if Persona Moral (for retentions)
    rfc_receptor = invoice_data['receptor']['rfc']
    is_moral = len(rfc_receptor.strip()) == 12

    # 2. Build Conceptos
    conceptos = []
    for c in invoice_data['conceptos']:
        importe = Decimal(str(c['importe']))
        valor_unitario = Decimal(str(c['valor_unitario']))
        cantidad = Decimal(str(c['cantidad']))
        objeto_imp = c['objeto_imp']

        concept_dict = {
            'ClaveProdServ': c['clave_prod_serv'],
            'Cantidad': cantidad,
            'ClaveUnidad': c['clave_unidad'],
            'Descripcion': c['descripcion'],
            'ValorUnitario': valor_unitario,
            'Importe': importe,
            'ObjetoImp': objeto_imp
        }

        # Apply Taxes if ObjetoImp is 02
        if objeto_imp == '02':
            # Base is Importe
            base = importe

            # Traslados (Standard IVA 16%)
            traslados = [
                {
                    'Base': base,
                    'Impuesto': '002',
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': Decimal('0.160000'),
                    'Importe': (base * Decimal('0.16')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                }
            ]

            retenciones = []
            if is_moral:
                # ISR Retention (10%)
                isr_amount = (base * Decimal('0.10')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                retenciones.append({
                    'Base': base,
                    'Impuesto': '001',
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': Decimal('0.100000'),
                    'Importe': isr_amount
                })

                # IVA Retention (10.6667%)
                iva_ret_amount = (base * Decimal('0.106667')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                retenciones.append({
                    'Base': base,
                    'Impuesto': '002',
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': Decimal('0.106667'),
                    'Importe': iva_ret_amount
                })

            impuestos_concept = {'Traslados': traslados}
            if retenciones:
                impuestos_concept['Retenciones'] = retenciones

            concept_dict['Impuestos'] = impuestos_concept

        conceptos.append(concept_dict)

    # 3. Construct Comprobante
    # Using hardcoded Emisor for Notaria 4 as per prompt context
    try:
            # satcfdi v4 auto-calculates SubTotal, Total, Impuestos
        cfdi = cfdi40.Comprobante(
                emisor={
                'Rfc': 'TOSR520601AZ4',
                'RegimenFiscal': '612',
                'Nombre': 'RENE MANUEL TORTOLERO SANTILLANA'
            },
                receptor={
                'Rfc': rfc_receptor,
                'Nombre': sanitize_name(invoice_data['receptor']['nombre']), # Ensure sanitized
                'UsoCFDI': invoice_data['receptor']['uso_cfdi'],
                'DomicilioFiscalReceptor': invoice_data['receptor']['domicilio_fiscal'],
                'RegimenFiscalReceptor': invoice_data['receptor'].get('regimen_fiscal', '616') # Default to Sin Obligaciones or passed
            },
                conceptos=conceptos,
                moneda='MXN',
                tipo_de_comprobante='I',
                lugar_expedicion='28200',
                exportacion='01'
        )

        # 4. Complemento Notarios
        if 'complemento_notarios' in invoice_data and invoice_data['complemento_notarios']:
            # Convert dict to model to use strict validation logic
            comp_model = ComplementoNotariosModel(**invoice_data['complemento_notarios'])
            # satcfdi handles Complemento assignment properly
            cfdi['Complemento'] = create_complemento_notarios(comp_model)

        # 5. Signing
        signer = load_signer_from_secret_manager()
        if signer:
            try:
                cfdi.sign(signer)
                logger.info("CFDI signed successfully")
            except Exception as e:
                logger.error(f"Error signing CFDI: {e}")
                # We raise error as per fiscal strictness, but if mocked/dev, we might continue.
                # Here we raise to ensure integrity in production logic.
                raise e
        else:
            logger.warning("No signer available, returning unsigned XML")

        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e
