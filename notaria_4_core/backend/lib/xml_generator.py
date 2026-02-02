from satcfdi.create.cfd import cfdi40
from satcfdi.create.cfd.catalogos import RegimenFiscal, UsoCFDI, MetodoPago, FormaPago, TipoDeComprobante
from decimal import Decimal
from typing import Dict, Any, Optional
from .fiscal_engine import calculate_retentions, sanitize_name

def generar_complemento_notarios(datos_notario: Dict, datos_operacion: Dict, inmueble: Dict, adquirientes: list) -> Dict:
    """
    Generates the 'Complemento de Notarios Públicos'.
    This returns the dictionary structure expected by satcfdi or the XML node.

    Note: The specific class/structure depends on satcfdi's implementation of this specific complement.
    If not natively supported, we construct the dict conforming to the XSD.
    """
    # Placeholder structure based on XSD requirements
    complemento = {
        "Version": "1.0",
        "DatosNotario": {
            "NumNotaria": 4,
            "EntidadFederativa": "06", # Colima
            "Adscripcion": "MANZANILLO COLIMA"
        },
        "DatosOperacion": {
            "FechaInstNotarial": datos_operacion['fecha_firma'],
            "MontoOperacion": datos_operacion['monto'],
            "SubTotal": datos_operacion['subtotal'],
            "IVA": datos_operacion['iva']
        },
        "DatosInmueble": {
            "TipoInmueble": inmueble['tipo'], # e.g., 03 Casa Habitacion
            "Calle": inmueble['calle'],
            # ... other address fields
        },
        "DatosAdquirientes": {
            "DatosAdquirientesCopSC": [
                {
                    "Nombre": a['nombre'],
                    "RFC": a['rfc'],
                    "Porcentaje": a['porcentaje']
                } for a in adquirientes
            ]
        }
    }
    return complemento

def generar_xml(datos_factura: Dict, signer=None) -> cfdi40.Comprobante:
    """
    Orchestrates the creation of the CFDI 4.0.
    """

    # Sanitize Receptor Name
    receptor_name = sanitize_name(datos_factura['receptor']['razon_social'])
    rfc_receptor = datos_factura['receptor']['rfc']
    subtotal = Decimal(str(datos_factura['subtotal']))

    # Calculate Retentions (Logic from Fiscal Engine)
    retentions = calculate_retentions(subtotal, rfc_receptor)

    # Prepare Impuestos block for Concepto
    impuestos_concepto = {
        "Traslados": [
            {"Base": subtotal, "Impuesto": "002", "TipoFactor": "Tasa", "TasaOCuota": Decimal("0.160000"), "Importe": subtotal * Decimal("0.16")}
        ]
    }

    if retentions["ISR"] > 0 or retentions["IVA"] > 0:
        impuestos_concepto["Retenciones"] = []
        if retentions["ISR"] > 0:
            impuestos_concepto["Retenciones"].append({
                "Base": subtotal, "Impuesto": "001", "TipoFactor": "Tasa", "TasaOCuota": Decimal("0.100000"), "Importe": retentions["ISR"]
            })
        if retentions["IVA"] > 0:
            impuestos_concepto["Retenciones"].append({
                "Base": subtotal, "Impuesto": "002", "TipoFactor": "Tasa", "TasaOCuota": Decimal("0.106667"), "Importe": retentions["IVA"]
            })

    # Create Concepto
    concepto = {
        "ClaveProdServ": "80131600", # Servicios Notariales (Example)
        "NoIdentificacion": "HONORARIOS",
        "Cantidad": Decimal("1"),
        "ClaveUnidad": "E48",
        "Unidad": "SERVICIO",
        "Descripcion": "HONORARIOS NOTARIALES",
        "ValorUnitario": subtotal,
        "Importe": subtotal,
        "ObjetoImp": "02", # Sí objeto de impuesto
        "Impuestos": impuestos_concepto
    }

    # Construct Comprobante
    # Note: satcfdi automatically calculates SubTotal, Total, and global Impuestos based on Conceptos
    # We pass the signer to sign it immediately if provided

    cfdi = cfdi40.Comprobante(
        Emisor={
            "Rfc": "TOSR520601AZ4", # Lic. Tortolero
            "Nombre": "RENE MANUEL TORTOLERO SANTILLANA",
            "RegimenFiscal": "612" # Personas Físicas con Actividades Empresariales y Profesionales
        },
        Receptor={
            "Rfc": rfc_receptor,
            "Nombre": receptor_name,
            "UsoCFDI": datos_factura['receptor'].get('uso_cfdi', 'G03'),
            "DomicilioFiscalReceptor": datos_factura['receptor']['cp'],
            "RegimenFiscalReceptor": datos_factura['receptor']['regimen_fiscal']
        },
        LugarExpedicion="28200", # Manzanillo
        MetodoPago="PUE",
        FormaPago="03", # Transferencia (Example, should be dynamic)
        Conceptos=[concepto],
        Moneda="MXN",
        TipoDeComprobante="I",
        Exportacion="01",
    )

    if signer:
        cfdi.sign(signer)

    return cfdi
