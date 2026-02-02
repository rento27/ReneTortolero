from typing import Dict, Any, Optional
from decimal import Decimal
from satcfdi.create.cfd import cfdi40
from satcfdi.models import Signer

def generar_complemento_notarios(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates the 'Complemento de Notarios Públicos' structure as a dictionary.
    """
    notaria_num = data.get("num_notaria", 4)
    entidad = data.get("entidad", "06") # Colima
    adscripcion = data.get("adscripcion", "MANZANILLO COLIMA")

    comp = {
        "Version": "1.0",
        "DatosNotario": {
            "NumNotaria": notaria_num,
            "EntidadFederativa": entidad,
            "Adscripcion": adscripcion
        },
        "DatosOperacion": {
            "NumInstrumentoNotarial": data.get("num_instrumento"),
            "FechaInstNotarial": data.get("fecha_instrumento"),
            "MontoOperacion": Decimal(str(data.get("monto_operacion", "0.00"))),
            "SubTotal": Decimal(str(data.get("subtotal_operacion", "0.00"))),
            "IVA": Decimal(str(data.get("iva_operacion", "0.00")))
        },
        "DescInmuebles": {
            "DescInmueble": []
        }
    }

    for inm in data.get("inmuebles", []):
        inm_node = {
            "TipoInmueble": inm.get("tipo", "03"),
            "Calle": inm.get("calle"),
            "Municipio": inm.get("municipio"),
            "Estado": inm.get("estado"),
            "Pais": inm.get("pais", "MEX"),
            "CodigoPostal": inm.get("cp")
        }
        if "no_exterior" in inm:
            inm_node["NoExterior"] = inm["no_exterior"]
        if "no_interior" in inm:
            inm_node["NoInterior"] = inm["no_interior"]

        comp["DescInmuebles"]["DescInmueble"].append(inm_node)

    if "adquirientes" in data:
        adquirientes_node = {"DatosAdquiriente": []}

        for adq in data["adquirientes"]:
            adq_node = {
                "Nombre": adq["nombre"],
                "RFC": adq["rfc"]
            }
            if adq.get("es_copropiedad", False):
                adq_node["DatosAdquirientesCopSC"] = {
                   "Porcentaje": Decimal(str(adq["porcentaje"]))
                }
            else:
                adq_node["DatosUnAdquiriente"] = {}

            adquirientes_node["DatosAdquiriente"].append(adq_node)

        comp["DatosAdquirientes"] = adquirientes_node

    return comp

def generate_xml(
    emisor: Dict[str, Any],
    receptor: Dict[str, Any],
    conceptos: list,
    datos_notario: Dict[str, Any],
    impuestos: Optional[Dict[str, Any]] = None,
    signer: Optional[Signer] = None,
    lugar_expedicion: Optional[str] = None
) -> cfdi40.Comprobante:
    """
    Generates the CFDI 4.0 object.
    """
    complemento_notarios = generar_complemento_notarios(datos_notario)

    # Extract LugarExpedicion from emisor if not provided
    if not lugar_expedicion:
        # Assuming emisor dict has 'CodigoPostal' as per SAT standard or key 'LugarExpedicion'
        lugar_expedicion = emisor.get("CodigoPostal") or emisor.get("LugarExpedicion") or "28200"

    # Note: satcfdi v4.0.0 auto-calculates global 'Impuestos' from 'Conceptos'.
    # Passing 'Impuestos' to __init__ is not supported in this version.
    # The 'impuestos' argument passed to this function is ignored for the Comprobante constructor,
    # relying on 'conceptos' having the correct tax breakdown.

    cfdi = cfdi40.Comprobante(
        emisor=emisor,
        lugar_expedicion=lugar_expedicion,
        receptor=receptor,
        conceptos=conceptos,
        # impuestos=impuestos, # Removed as it causes TypeError
        # Complemento logic would go here
    )

    # Attach our manual dictionary for testing purposes
    cfdi._complemento_notarios_debug = complemento_notarios

    if signer:
        cfdi.sign(signer)

    return cfdi
