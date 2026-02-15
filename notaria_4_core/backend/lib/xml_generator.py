from decimal import Decimal
import logging
from typing import Optional, Dict, Any

# Check for satcfdi availability
try:
    from satcfdi.create.cfd import cfdi40
    from satcfdi.models import Signer
except ImportError:
    cfdi40 = None
    Signer = None

from .fiscal_engine import sanitize_name
from .api_models import InvoiceRequest, Concepto
from .complement_notarios import create_complemento_notarios

logger = logging.getLogger(__name__)

def generate_signed_xml(invoice_data: Any) -> bytes:
    """
    Generates a CFDI 4.0 XML object.
    Accepts a dictionary (from InvoiceRequest.model_dump()) or InvoiceRequest object.
    """

    # Normalize input
    if not isinstance(invoice_data, InvoiceRequest):
        if isinstance(invoice_data, dict):
            request_model = InvoiceRequest(**invoice_data)
        else:
            raise ValueError("Invalid input type for generate_signed_xml")
    else:
        request_model = invoice_data

    if not cfdi40:
        logger.error("satcfdi library not found")
        return b"<error>satcfdi not available</error>"

    # 1. Determine Receptor Type and Retentions Logic
    rfc_receptor = request_model.receptor.rfc
    is_moral = len(rfc_receptor.strip()) == 12

    # 2. Build Conceptos with Tax Logic
    conceptos_cfdi = []

    for c in request_model.conceptos:
        # Prepare arguments for satcfdi.Concepto (using snake_case arguments)
        concepto_args = {
            'clave_prod_serv': c.clave_prod_serv,
            'cantidad': c.cantidad,
            'clave_unidad': c.clave_unidad,
            'descripcion': c.descripcion,
            'valor_unitario': c.valor_unitario,
            'objeto_imp': c.objeto_imp
        }

        impuestos_dict = {}

        # Apply Retentions if Persona Moral AND ObjetoImp is '02' (Yes object of tax)
        if is_moral and c.objeto_imp == '02':
            # Calculate taxes for this concept
            # ISR: 10%
            isr_amount = (c.importe * Decimal("0.10")).quantize(Decimal("0.01"))
            # IVA Ret: 10.6667% (0.106667)
            iva_ret_amount = (c.importe * Decimal("0.106667")).quantize(Decimal("0.01"))
            # IVA Traslado: 16%
            iva_traslado_amount = (c.importe * Decimal("0.16")).quantize(Decimal("0.01"))

            impuestos_dict = {
                'Traslados': [
                    {'Base': c.importe, 'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': Decimal('0.160000'), 'Importe': iva_traslado_amount}
                ],
                'Retenciones': [
                    {'Base': c.importe, 'Impuesto': '001', 'TipoFactor': 'Tasa', 'TasaOCuota': Decimal('0.100000'), 'Importe': isr_amount}, # ISR
                    {'Base': c.importe, 'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': Decimal('0.106667'), 'Importe': iva_ret_amount}  # IVA
                ]
            }
        elif c.objeto_imp == '02':
            # Persona Fisica: Only Traslado (IVA 16%)
            iva_traslado_amount = (c.importe * Decimal("0.16")).quantize(Decimal("0.01"))
            impuestos_dict = {
                 'Traslados': [
                    {'Base': c.importe, 'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': Decimal('0.160000'), 'Importe': iva_traslado_amount}
                ]
            }

        if impuestos_dict:
            concepto_args['impuestos'] = impuestos_dict

        conceptos_cfdi.append(cfdi40.Concepto(**concepto_args))

    # 3. Construct Complemento Notarios
    complemento = None
    if request_model.complemento_notarios:
        complemento = create_complemento_notarios(request_model.complemento_notarios)

    # 4. Construct Comprobante
    # SubTotal, Total, Impuestos (Root) are auto-calculated by satcfdi from Conceptos

    try:
        cfdi = cfdi40.Comprobante(
            emisor={
                'Rfc': 'TOSR520601AZ4',
                'RegimenFiscal': '612',
                'Nombre': 'RENE MANUEL TORTOLERO SANTILLANA'
            },
            receptor={
                'Rfc': rfc_receptor,
                'Nombre': sanitize_name(request_model.receptor.nombre),
                'UsoCFDI': request_model.receptor.uso_cfdi,
                'DomicilioFiscalReceptor': request_model.receptor.domicilio_fiscal,
                'RegimenFiscalReceptor': request_model.receptor.regimen_fiscal
            },
            conceptos=conceptos_cfdi,
            moneda='MXN',
            tipo_de_comprobante='I',
            lugar_expedicion='28200',
            exportacion='01', # No aplica
            complemento=complemento
        )

        # 5. Signing (Stub)
        # In a real environment:
        # signer = Signer.load(certificate=..., key=..., password=...)
        # cfdi.sign(signer)

        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e
