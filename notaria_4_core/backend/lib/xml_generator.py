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

from .api_models import InvoiceRequest
from .fiscal_engine import sanitize_name, calculate_retentions, IVA_RETENTION_RATE_DIRECT, ISR_RETENTION_RATE
from .complement_notarios import create_complemento_notarios

logger = logging.getLogger(__name__)

# Mock Signer for Development/Testing
MOCK_SIGNER_KEY = "mock_key"

def get_signer():
    """
    Loads the Signer from Secret Manager or returns a mock.
    """
    # In a real implementation, this would access Google Secret Manager
    # For this environment/stub, we return None or a dummy if satcfdi allows
    # satcfdi requires a valid certificate to sign.
    # If we want to generate valid XML structure without signing, we can omit signing step.
    return None

def generate_signed_xml(request: InvoiceRequest) -> bytes:
    """
    Generates a CFDI 4.0 XML object from the InvoiceRequest.
    """
    if not cfdi40:
        logger.error("satcfdi library not found")
        return b"<error>satcfdi not available</error>"

    data = request

    # 1. Sanitize Receptor Name
    clean_nombre_receptor = sanitize_name(data.receptor.nombre)

    # 2. Determine Fiscal Regime for Receptor
    # If not provided or needs logic, handle here. We assume it comes in request.

    # 3. Process Concepts and Retentions
    conceptos_xml = []

    is_persona_moral = len(data.receptor.rfc) == 12

    for c in data.conceptos:
        # Create base concept dict
        concepto_args = {
            'clave_prod_serv': c.clave_prod_serv,
            'cantidad': c.cantidad,
            'clave_unidad': c.clave_unidad,
            'descripcion': c.descripcion,
            'valor_unitario': c.valor_unitario,
            # 'importe': c.importe, # Calculated by satcfdi
            'objeto_imp': c.objeto_imp,
            'no_identificacion': c.no_identificacion,
            'unidad': c.unidad,
            'descuento': c.descuento
        }

        # Taxes Logic
        # If ObjetoImp is '02' (Yes), we expect Traslados (IVA 16%).
        # If Persona Moral, we add Retenciones.

        if c.objeto_imp == '02':
            # Base for taxes is usually the Importe (Amount)
            # We calculate it to match satcfdi logic (Quantity * Unit Value)
            base = (c.cantidad * c.valor_unitario).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Traslados (IVA 16%)
            traslados = [
                {
                    'Base': base,
                    'Impuesto': '002', # IVA
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': Decimal('0.160000'),
                    'Importe': (base * Decimal('0.16')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                }
            ]

            retenciones = []
            if is_persona_moral:
                # ISR Retention (10%)
                ret_isr_amount = (base * ISR_RETENTION_RATE).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                retenciones.append({
                    'Base': base,
                    'Impuesto': '001', # ISR
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': Decimal('0.100000'),
                    'Importe': ret_isr_amount
                })

                # IVA Retention (2/3 of 16% = 10.6667%)
                # satcfdi/PAC might require precise rate matching.
                # Standard is 0.106666 or 0.106667.
                # fiscal_engine uses 0.106667.
                ret_iva_amount = (base * IVA_RETENTION_RATE_DIRECT).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                retenciones.append({
                    'Base': base,
                    'Impuesto': '002', # IVA
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': Decimal('0.106667'),
                    'Importe': ret_iva_amount
                })

            impuestos_dict = {
                'Traslados': traslados
            }
            if retenciones:
                impuestos_dict['Retenciones'] = retenciones

            concepto_args['impuestos'] = impuestos_dict

        conceptos_xml.append(cfdi40.Concepto(**concepto_args))

    # 4. Create Comprobante
    # Note: satcfdi calculates SubTotal, Total, and Impuestos (Root) automatically from Conceptos.
    # We pass explicit None for them to trigger calculation, OR we don't pass them.

    cfdi = cfdi40.Comprobante(
        emisor={
            'Rfc': 'TOSR520601AZ4',
            'RegimenFiscal': '612',
            'Nombre': 'RENE MANUEL TORTOLERO SANTILLANA'
        },
        receptor={
            'Rfc': data.receptor.rfc,
            'Nombre': clean_nombre_receptor,
            'UsoCFDI': data.receptor.uso_cfdi,
            'DomicilioFiscalReceptor': data.receptor.domicilio_fiscal,
            'RegimenFiscalReceptor': data.receptor.regimen_fiscal
        },
        conceptos=conceptos_xml,
        moneda='MXN',
        tipo_de_comprobante='I',
        lugar_expedicion='28200',
        forma_pago=data.forma_pago,
        metodo_pago=data.metodo_pago,
        serie=data.serie,
        folio=data.folio,
        exportacion='01' # No aplica
    )

    # 5. Add Complemento Notarios
    if data.complemento_notarios:
        complemento_obj = create_complemento_notarios(data.complemento_notarios)
        cfdi['Complemento'] = complemento_obj

    # 6. Signing
    # In this environment, we skip actual signing if no key is present.
    # returning the XML bytes.
    # If we had a signer: cfdi.sign(signer)

    return cfdi.xml_bytes()
