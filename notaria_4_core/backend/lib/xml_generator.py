from decimal import Decimal
from satcfdi.create.cfd import cfdi40
from satcfdi.create.cfd.catalogos import RegimenFiscal, UsoCFDI, MetodoPago, FormaPago, TipoDeComprobante
from .fiscal_engine import calculate_retentions, sanitize_name

def generar_complemento_notarios(datos_notario: dict, datos_operacion: dict, inmuebles: list, adquirientes: list, enajenantes: list) -> dict:
    """
    Constructs the 'Complemento de Notarios Públicos' structure manually as a dictionary.
    This matches the XSD requirements.
    """

    # Base structure
    complemento = {
        "Version": "1.0",
        "DatosNotario": {
            "NumNotaria": datos_notario.get("num_notaria", 4),
            "EntidadFederativa": datos_notario.get("entidad_federativa", "06"), # Colima
            "Adscripcion": datos_notario.get("adscripcion", "MANZANILLO COLIMA")
        },
        "DatosOperacion": {
            "NumInstrumentoNotarial": datos_operacion["num_instrumento"],
            "FechaInstNotarial": datos_operacion["fecha_instrumento"],
            "MontoOperacion": datos_operacion["monto_operacion"],
            "Subtotal": datos_operacion["subtotal"],
            "IVA": datos_operacion["iva"]
        },
        "DescInmuebles": {
            "DescInmueble": inmuebles # List of dicts with Calle, Municipio, TipoInmueble
        },
        "DatosAdquirientes": {
            "DatosAdquiriente": adquirientes # List of dicts
        },
        "DatosEnajenantes": {
            "DatosEnajenante": enajenantes # List of dicts
        }
    }

    return complemento

def generate_xml(
    emisor: dict,
    receptor: dict,
    conceptos: list,
    folio: str,
    datos_complemento: dict = None,
    signer = None
):
    """
    Generates the CFDI 4.0 XML.
    Uses satcfdi to auto-calculate totals and taxes by injecting tax objects into Concepts.
    """

    # Sanitize Receptor Name
    receptor_name = sanitize_name(receptor.get("Nombre", ""))

    # Determine if we need to apply retentions (Persona Moral)
    # Check strict 12 chars length
    is_moral = (len(receptor['Rfc']) == 12)

    modified_conceptos = []

    for c in conceptos:
        new_c = c.copy()

        # Only apply taxes if ObjectImp is '02'
        if new_c.get('ObjetoImp') == '02':
            importe = new_c['Importe']

            # Traslados (IVA 16%)
            traslados = [{
                'Base': importe,
                'Impuesto': '002',
                'TipoFactor': 'Tasa',
                'TasaOCuota': Decimal('0.160000'),
                'Importe': (importe * Decimal("0.16")).quantize(Decimal("0.01"))
            }]

            retenciones = []
            if is_moral:
                # ISR 10%
                retenciones.append({
                    'Base': importe,
                    'Impuesto': '001',
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': Decimal('0.100000'),
                    'Importe': (importe * Decimal("0.10")).quantize(Decimal("0.01"))
                })
                # IVA 2/3 of 16% (~10.6667%)
                # satcfdi expects exact decimals usually, let's use 0.106666 or 0.106667
                # Standard practice is 0.106667
                retenciones.append({
                    'Base': importe,
                    'Impuesto': '002',
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': Decimal('0.106667'),
                    'Importe': (importe * Decimal("0.106667")).quantize(Decimal("0.01"))
                })

            new_c['Impuestos'] = {
                'Traslados': traslados
            }
            if retenciones:
                new_c['Impuestos']['Retenciones'] = retenciones

        modified_conceptos.append(new_c)

    cfdi = cfdi40.Comprobante(
        emisor=emisor,
        receptor={
            "Rfc": receptor["Rfc"],
            "Nombre": receptor_name,
            "RegimenFiscalReceptor": receptor["RegimenFiscal"],
            "DomicilioFiscalReceptor": receptor["DomicilioFiscal"],
            "UsoCFDI": receptor["UsoCFDI"]
        },
        conceptos=modified_conceptos,
        moneda="MXN",
        tipo_de_comprobante=TipoDeComprobante.INGRESO,
        exportacion="01", # No aplica
        folio=folio,
        lugar_expedicion="28200", # Manzanillo default
        metodo_pago=MetodoPago.PAGO_EN_UNA_SOLA_EXHIBICION,
        forma_pago=FormaPago.POR_DEFINIR,
        # satcfdi will auto-calculate SubTotal, Total, and Global Impuestos based on modified_conceptos
    )

    if signer:
        cfdi.sign(signer)

    return cfdi
