from satcfdi.create.cfd import cfdi40
from satcfdi.create.cfd.catalogos import RegimenFiscal, UsoCFDI
from decimal import Decimal

def generar_complemento_notarios(datos_notario: dict) -> dict:
    """
    Generates the 'Complemento de Notarios Públicos' dictionary structure.
    This mimics the structure required by satcfdi to serialize into the correct XML.
    """
    # Placeholder for the complex structure
    # This must match the XSD definition
    complemento = {
        "Version": "1.0",
        "DatosNotario": {
            "NumNotaria": 4,
            "EntidadFederativa": "06", # Colima
            "Adscripcion": "MANZANILLO COLIMA"
        },
        "DatosOperacion": {
            "FechaInstNotarial": datos_notario.get("fecha_firma"),
            "NumInstrumentoNotarial": datos_notario.get("numero_escritura"),
            "MontoOperacion": Decimal(datos_notario.get("monto_operacion", 0)),
            "Subtotal": Decimal(datos_notario.get("subtotal", 0)),
            "IVA": Decimal(datos_notario.get("iva", 0))
        },
        "DatosNotarial": {
             # ... Detailed nodes for DescInmuebles, DatosAdquirientes, etc.
             "DescInmuebles": {
                 "Inmuebles": [
                     {
                         "TipoInmueble": "03", # Casa habitacion example
                         "Calle": datos_notario.get("calle"),
                         # ...
                     }
                 ]
             }
        }
    }

    return complemento

def generar_cfdi_notaria(emisor: dict, receptor: dict, conceptos: list, formas_pago: str = "03"):
    """
    Creates a CFDI 4.0 object using satcfdi.
    """
    # Calculate global tax logic if needed, but satcfdi usually handles it from concepts

    cfdi = cfdi40.Comprobante(
        Emisor=emisor,
        Receptor=receptor,
        Conceptos=conceptos,
        FormaPago=formas_pago,
        MetodoPago="PUE",
        LugarExpedicion="28200", # Manzanillo
        Moneda="MXN",
        # Complemento=... # Would be added here
    )

    return cfdi
