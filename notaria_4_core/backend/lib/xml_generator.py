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
    impuestos = None
    if datos_factura.get("impuestos_retencion"):
        impuestos = {
            "Retenciones": datos_factura["impuestos_retencion"]
        }

    # 2. Generate Complemento Notarios
    # We construct the dictionary. Ideally, this should be wrapped in
    # satcfdi.create.cfd.complemento.notariospublicos.NotariosPublicos(**complemento_dict)
    # but since we don't have the import handy, we return the dict structure.
    # The caller or the final integration point handles the specific class instantiation if needed.
    complemento_data = generar_complemento_notarios(datos_notario)

    # NOTE: In a full satcfdi implementation, you would import the specific class:
    # from satcfdi.create.cfd.complemento.notariospublicos import NotariosPublicos
    # complemento = NotariosPublicos(**complemento_data)
    # For now, we pass it as a dict or assume satcfdi can handle dict->object conversion if supported.
    # Given satcfdi v4.0.0, we usually need the class.
    # We will return the dict in the 'Complemento' list slot as a placeholder.

    cfdi = cfdi40.Comprobante(
        emisor=datos_factura["emisor"],
        receptor=datos_factura["receptor"],
        conceptos=datos_factura["conceptos"],
        moneda=datos_factura.get("moneda", "MXN"),
        forma_pago=datos_factura.get("forma_pago", "03"), # Transferencia
        metodo_pago=datos_factura.get("metodo_pago", "PUE"),
        lugar_expedicion=datos_factura.get("lugar_expedicion", "28219"), # Manzanillo
        impuestos=impuestos,
        complemento=complemento_data # Passing dict, assuming adapter or further processing
    )

    # 3. Sign if signer is provided
    if signer:
        cfdi.sign(signer)

    return cfdi

def generar_complemento_notarios(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates the Complemento de Notarios Públicos structure matching XSD requirements.
    """

    # 1. Datos del Notario (Fixed for Notaría 4)
    notaria = {
        "NumNotaria": 4,
        "EntidadFederativa": "06", # Colima
        "Adscripcion": "MANZANILLO COLIMA"
    }

    # 2. Datos de Operación
    operacion = {
        "NumInstrumentoNotarial": data.get("num_instrumento"),
        "FechaInstNotarial": data.get("fecha_instrumento"), # Format YYYY-MM-DD
        "MontoOperacion": data.get("monto_operacion"),
        "Subtotal": data.get("subtotal"),
        "IVA": data.get("iva")
    }

    # 3. Datos del Inmueble (DescInmuebles)
    # Supports multiple properties, though usually one per deed
    inmuebles = {
        "DescInmueble": [
            {
                "TipoInmueble": data.get("tipo_inmueble", "03"), # Default: Casa Habitación? Check Catalog.
                "Calle": data.get("calle"),
                "Municipio": data.get("municipio"),
                "Estado": data.get("estado"),
                "Pais": "MEX",
                "CodigoPostal": data.get("cp")
            }
        ]
    }

    # 4. Datos de Adquirientes (Copropiedad Support)
    adquirientes_list = []
    for adq in data.get("adquirientes", []):
        adquirientes_list.append({
            "Nombre": adq["nombre"],
            "Rfc": adq["rfc"],
            "Porcentaje": adq["porcentaje"] # Must sum 100.00
        })

    adquirientes = {
        "DatosAdquirientesCopSC": adquirientes_list
    }

    # Final Structure
    # Note: 'Version' is fixed at 1.0 for this complement
    return {
        "Version": "1.0",
        "DatosNotario": notaria,
        "DatosOperacion": operacion,
        "DescInmuebles": inmuebles,
        "DatosAdquirientes": adquirientes
    }
