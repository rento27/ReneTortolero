from satcfdi.create.cfd import cfdi40
from decimal import Decimal
from typing import Dict, Any, Optional

def generar_xml(datos_factura: Dict[str, Any], datos_notario: Dict[str, Any], signer=None) -> cfdi40.Comprobante:
    """
    Generates a CFDI 4.0 XML based on sanitized input data.

    Args:
        datos_factura: Dictionary containing issuer, receiver, concepts, and taxes.
        datos_notario: Dictionary containing notary specific data (complemento).
        signer: Optional satcfdi.models.Signer object. If None, the XML is not signed.

    Returns:
        cfdi40.Comprobante object.
    """

    # 1. Construct Taxes (Impuestos) Logic
    # In a real scenario, this comes pre-calculated from fiscal_engine,
    # but satcfdi can also help structure it.
    impuestos = None
    if datos_factura.get("impuestos_retencion"):
        # Example structure for retentions
        impuestos = {
            "Retenciones": datos_factura["impuestos_retencion"]
            # e.g. [{'Impuesto': '001', 'Importe': Decimal('...')}, ...]
        }

    # 2. Create the Comprobante
    # Note: satcfdi calculates global Impuestos automatically from Conceptos
    cfdi = cfdi40.Comprobante(
        emisor=datos_factura["emisor"],
        receptor=datos_factura["receptor"],
        conceptos=datos_factura["conceptos"],
        moneda=datos_factura.get("moneda", "MXN"),
        forma_pago=datos_factura.get("forma_pago", "03"), # Transferencia
        metodo_pago=datos_factura.get("metodo_pago", "PUE"),
        lugar_expedicion=datos_factura.get("lugar_expedicion", "28219"), # Manzanillo
        # Complemento=generar_complemento_notarios(datos_notario) # Placeholder for complex Notarios implementation
    )

    # 3. Sign if signer is provided
    if signer:
        cfdi.sign(signer)

    return cfdi

def generar_complemento_notarios(data: Dict[str, Any]):
    """
    Placeholder for the complex Complemento de Notarios Públicos.
    This requires mapping to the 'notariospublicos.xsd'.
    """
    # TODO: Implement full mapping for Complemento Notarios
    pass
