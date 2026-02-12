from decimal import Decimal, ROUND_HALF_UP
import logging
import os

# Check for satcfdi availability
try:
    from satcfdi.create.cfd import cfdi40
    from satcfdi.models import Signer
except ImportError:
    cfdi40 = None
    Signer = None

from .fiscal_engine import (
    validate_copropiedad,
    sanitize_name,
    IVA_RATE,
    ISR_RETENTION_RATE,
    IVA_RETENTION_RATE_DIRECT
)
from .api_models import ComplementoNotarios
from .complement_notarios import create_complemento_notarios
from .security import load_signer_from_secret_manager

logger = logging.getLogger(__name__)

def generate_signed_xml(invoice_data: dict, project_id: str = "notaria4") -> bytes:
    """
    Generates a CFDI 4.0 XML object.

    Current implementation builds the Comprobante structure using satcfdi.
    """

    # 0. Sanitize Receptor Name (Critical Requirement)
    # Ensure corporate regime is stripped even if called outside main API flow
    if 'receptor' in invoice_data and 'nombre' in invoice_data['receptor']:
        invoice_data['receptor']['nombre'] = sanitize_name(invoice_data['receptor']['nombre'])

    # 1. Pre-generation Validation
    if 'copropietarios' in invoice_data and invoice_data['copropietarios']:
        percentages = [Decimal(str(p['porcentaje'])) for p in invoice_data['copropietarios']]
        validate_copropiedad(percentages)

    if not cfdi40:
        logger.error("satcfdi library not found")
        return b"<error>satcfdi not available</error>"

    is_moral = len(invoice_data['receptor']['rfc']) == 12
    conceptos_list = []

    for c in invoice_data['conceptos']:
        cantidad = Decimal(str(c['cantidad']))
        valor_unitario = Decimal(str(c['valor_unitario']))
        # Importe calculated by satcfdi or we can pass it if we want to force it.
        # However, for tax calculation we calculate it locally.
        importe = (cantidad * valor_unitario).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        concepto_dict = {
            'ClaveProdServ': c['clave_prod_serv'],
            'Cantidad': cantidad,
            'ClaveUnidad': c['clave_unidad'],
            'Descripcion': c['descripcion'],
            'ValorUnitario': valor_unitario,
            'ObjetoImp': c['objeto_imp']
        }

        if c['objeto_imp'] == '02':
             # Calculate IVA
             iva_importe = (importe * IVA_RATE).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

             traslados = [
                 {'Base': importe, 'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': IVA_RATE, 'Importe': iva_importe}
             ]

             retenciones = []
             if is_moral:
                 # ISR
                 isr_importe = (importe * ISR_RETENTION_RATE).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                 retenciones.append({'Base': importe, 'Impuesto': '001', 'TipoFactor': 'Tasa', 'TasaOCuota': ISR_RETENTION_RATE, 'Importe': isr_importe})

                 # IVA Ret
                 iva_ret_importe = (importe * IVA_RETENTION_RATE_DIRECT).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                 retenciones.append({'Base': importe, 'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': IVA_RETENTION_RATE_DIRECT, 'Importe': iva_ret_importe})

             concepto_dict['Impuestos'] = {
                 'Traslados': traslados
             }
             if retenciones:
                 concepto_dict['Impuestos']['Retenciones'] = retenciones

        conceptos_list.append(concepto_dict)

    # Get regimen fiscal or default
    regimen_fiscal_receptor = invoice_data['receptor'].get('regimen_fiscal', '616') # Default to 'Sin obligaciones fiscales' if missing

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
                'RegimenFiscalReceptor': regimen_fiscal_receptor
            },
            conceptos=conceptos_list,
            moneda='MXN',
            tipo_de_comprobante='I',
            lugar_expedicion='28200',
            exportacion='01' # No aplica
            # impuestos, sub_total, total are calculated automatically by satcfdi from concepts
        )

        # 4. Complemento Notarios
        if 'complemento_notarios' in invoice_data and invoice_data['complemento_notarios']:
            # Convert dict back to Pydantic model for validation/processing
            # Since model_dump() keeps nested dicts, we pass them to Pydantic to reconstruct
            comp_data = ComplementoNotarios(**invoice_data['complemento_notarios'])
            complemento = create_complemento_notarios(comp_data)

            # Attach to CFDI
            cfdi['Complemento'] = complemento

        # 5. Signing
        # Load signer from Secret Manager
        # We pass project_id to the function. Defaults to 'notaria4'.
        signer = load_signer_from_secret_manager(project_id)

        if signer:
            cfdi.sign(signer)
        else:
            logger.warning("CFDI generated without signature (Mock/Dev Mode)")

        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e
