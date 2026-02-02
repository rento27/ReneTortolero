from satcfdi.create.cfd import cfdi40
from satcfdi.create.cfd.catalogos import RegimenFiscal, UsoCFDI, MetodoPago, FormaPago, TipoDeComprobante
from decimal import Decimal
from typing import Dict, List, Any
from .fiscal_engine import calculate_retentions, sanitize_name

# Placeholder for the Complemento de Notarios logic
# In a real implementation, we would map the dictionary to the XSD structure provided by satcfdi or custom classes
def generar_complemento_notarios(datos_notario: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates the 'Complemento de Notarios Públicos' structure.

    Hardcoded Notary 4 Data:
    - NumNotaria: 4
    - EntidadFederativa: 06 (Colima)
    - Adscripcion: MANZANILLO COLIMA
    """
    # This is a stub. The actual satcfdi implementation requires specific object structures.
    # Returning a dictionary representation for now.
    return {
        "Version": "1.0",
        "DatosNotario": {
            "NumNotaria": 4,
            "EntidadFederativa": "06",
            "Adscripcion": "MANZANILLO COLIMA"
        },
        "DatosOperacion": datos_notario.get("datos_operacion", {}),
        "DatosInmueble": datos_notario.get("datos_inmueble", {}),
        # ... logic for Copropiedad ...
    }

def generar_xml(datos_factura: Dict[str, Any], datos_notario: Dict[str, Any] = None) -> cfdi40.Comprobante:
    """
    Orchestrates the creation of the CFDI 4.0 XML.
    """

    receptor_data = datos_factura['receptor']
    receptor_rfc = receptor_data.get('rfc', '').strip().upper()
    subtotal = Decimal(str(datos_factura['subtotal']))

    # Calculate taxes and retentions
    # IVA 16% is standard for these operations unless specified otherwise
    iva_traslado = (subtotal * Decimal("0.16")).quantize(Decimal("0.01"))

    retentions = calculate_retentions(subtotal, receptor_rfc)
    isr_ret = retentions["isr_retention"]
    iva_ret = retentions["iva_retention"]

    impuestos_args = {
        "Traslados": [
            {"Impuesto": "002", "TipoFactor": "Tasa", "TasaOCuota": "0.160000", "Importe": iva_traslado}
        ]
    }

    if isr_ret > 0 or iva_ret > 0:
        impuestos_args["Retenciones"] = []
        if isr_ret > 0:
            impuestos_args["Retenciones"].append(
                {"Impuesto": "001", "Importe": isr_ret}
            )
        if iva_ret > 0:
            impuestos_args["Retenciones"].append(
                {"Impuesto": "002", "Importe": iva_ret}
            )

    # Sanitize Receptor Name
    razon_social = sanitize_name(receptor_data.get('nombre'))

    # Construct the Comprobante
    cfdi = cfdi40.Comprobante(
        Emisor={
            "Rfc": "TOSR520601AZ4", # Lic. Tortolero RFC
            "Nombre": "RENE MANUEL TORTOLERO SANTILLANA",
            "RegimenFiscal": "612" # Personas Físicas con Actividades Empresariales y Profesionales (Check specific regime)
        },
        Receptor={
            "Rfc": receptor_rfc,
            "Nombre": razon_social,
            "UsoCFDI": receptor_data.get("uso_cfdi", UsoCFDI.GASTOS_EN_GENERAL),
            "DomicilioFiscalReceptor": receptor_data.get("cp"),
            "RegimenFiscalReceptor": receptor_data.get("regimen_fiscal")
        },
        LugarExpedicion="28219", # Manzanillo
        MetodoPago=datos_factura.get("metodo_pago", MetodoPago.PAGO_EN_UNA_SOLA_EXHIBICION),
        FormaPago=datos_factura.get("forma_pago", FormaPago.TRANSFERENCIA_ELECTRONICA_DE_FONDOS),
        TipoDeComprobante=TipoDeComprobante.INGRESO,
        Moneda="MXN",
        SubTotal=subtotal,
        Total=subtotal + iva_traslado - isr_ret - iva_ret,
        Conceptos=datos_factura['conceptos'],
        Impuestos=impuestos_args
    )

    if datos_notario:
        # cfdi['Complemento'] = generar_complemento_notarios(datos_notario)
        # Note: integration of the complement requires specific satcfdi object structure
        pass

    return cfdi
