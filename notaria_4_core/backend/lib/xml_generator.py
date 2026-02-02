from satcfdi.create.cfd import cfdi40
from satcfdi.create.cfd.catalogos import RegimenFiscal, UsoCFDI, MetodoPago, FormaPago, TipoDeComprobante, Impuesto
from decimal import Decimal

class XMLGenerator:
    def __init__(self, signer=None):
        self.signer = signer

    def generar_complemento_notarios(self, data: dict):
        """
        Generates the 'Complemento de Notarios Públicos'.
        Structure aligned with notariospublicos.xsd.
        """
        # Hardcoded constants for Notaria 4
        complemento = {
            "Version": "1.0",
            "DatosNotario": {
                "NumNotaria": 4,
                "EntidadFederativa": "06", # Colima
                "Adscripcion": "MANZANILLO COLIMA"
            },
            "DatosOperacion": {
                "NumInstrumentoNotarial": data.get("numero_escritura"),
                "FechaInstNotarial": data.get("fecha_firma"),
                "MontoOperacion": data.get("monto_operacion"),
                "Subtotal": data.get("monto_operacion"),
                "IVA": "0.00"
            },
            # Mandatory Node: DescInmuebles
            "DescInmuebles": {
                 "DescInmueble": []
            },
            "DatosAdquirientes": {
                "DatosAdquirientesCopSC": []
            }
        }

        # Add Properties (DescInmueble)
        for inmueble in data.get("inmuebles", []):
            complemento["DescInmuebles"]["DescInmueble"].append({
                "TipoInmueble": inmueble.get("tipo_inmueble", "01"),
                "Calle": inmueble.get("calle"),
                "NoExterior": inmueble.get("no_exterior", ""),
                "Municipio": inmueble.get("municipio", "MANZANILLO"),
                "Estado": "06",
                "Pais": "MEX",
                "CodigoPostal": inmueble.get("cp")
            })

        # Add copropietarios (DatosAdquirientesCopSC)
        for acquirer in data.get("adquirientes", []):
             complemento["DatosAdquirientes"]["DatosAdquirientesCopSC"].append({
                 "Nombre": acquirer["nombre"],
                 "ApellidoPaterno": acquirer["paterno"],
                 "ApellidoMaterno": acquirer["materno"],
                 "RFC": acquirer["rfc"],
                 "Porcentaje": acquirer["porcentaje"]
             })

        return complemento

    def generar_xml(self, invoice_data: dict, complemento_data: dict = None):
        """
        Generates the CFDI 4.0 object.
        Applies retentions if calculated by modifying Conceptos.
        """
        receptor = {
            "Rfc": invoice_data["receptor"]["rfc"],
            "Nombre": invoice_data["receptor"]["nombre"], # Already sanitized
            "DomicilioFiscalReceptor": invoice_data["receptor"]["cp"],
            "RegimenFiscalReceptor": invoice_data["receptor"]["regimen"],
            "UsoCFDI": invoice_data["receptor"]["uso_cfdi"]
        }

        conceptos = invoice_data.get("conceptos", [])

        # Inject retentions into concepts if persona moral
        retentions_data = invoice_data.get("retentions", {})

        if retentions_data.get("is_persona_moral") and conceptos:
            for concept in conceptos:
                # ONLY apply retentions to concepts marked as "02" (Objeto de impuesto)
                if concept.get("ObjetoImp") == "02":

                    if "Impuestos" not in concept:
                        concept["Impuestos"] = {}

                    if "Retenciones" not in concept["Impuestos"]:
                        concept["Impuestos"]["Retenciones"] = []

                    # Calculate amount for THIS concept specifically
                    # Since the engine calculated global retentions based on global subtotal,
                    # we need to be careful.
                    # Correct logic: Apply Rates to the concept amount.

                    amount = Decimal(str(concept["Importe"]))

                    # ISR 10%
                    isr_amount = (amount * Decimal("0.10")).quantize(Decimal("0.01"))
                    concept["Impuestos"]["Retenciones"].append({
                        "Base": amount,
                        "Impuesto": Impuesto.ISR,
                        "TipoFactor": "Tasa",
                        "TasaOCuota": Decimal("0.100000"),
                        "Importe": isr_amount
                    })

                    # IVA 10.6667% (2/3 of 0.16)
                    # Note: We use the factor 0.106667 directly as accepted by SAT (usually 0.106666 or 0.106667 depending on strictness)
                    # Or we calculate amount manually to match the engine.
                    # SAT requires TasaOCuota to match the Importe calculation within tolerance.

                    iva_amount = (amount * Decimal("0.16") * Decimal("2") / Decimal("3")).quantize(Decimal("0.01"))

                    concept["Impuestos"]["Retenciones"].append({
                        "Base": amount,
                        "Impuesto": Impuesto.IVA,
                        "TipoFactor": "Tasa",
                        "TasaOCuota": Decimal("0.106667"),
                        "Importe": iva_amount
                    })


        complemento = None
        if complemento_data:
            complemento = self.generar_complemento_notarios(complemento_data)

        cfdi = cfdi40.Comprobante(
            emisor={
                "Rfc": "TOSR520601AZ4",
                "Nombre": "RENE MANUEL TORTOLERO SANTILLANA",
                "RegimenFiscal": "612"
            },
            receptor=receptor,
            lugar_expedicion="28200",
            metodo_pago=MetodoPago.PAGO_EN_UNA_SOLA_EXHIBICION,
            forma_pago=FormaPago.TRANSFERENCIA_ELECTRONICA_DE_FONDOS,
            tipo_de_comprobante=TipoDeComprobante.INGRESO,
            exportacion="01",
            moneda="MXN",
            conceptos=conceptos,
            complemento=complemento
        )

        if self.signer:
            cfdi.sign(self.signer)

        return cfdi
