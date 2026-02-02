from decimal import Decimal
from satcfdi.create.cfd import cfdi40
from satcfdi.create.cfd.catalogos import RegimenFiscal, UsoCFDI, MetodoPago, FormaPago, TipoDeComprobante

class XMLGenerator:
    def __init__(self, emisor_rfc: str, emisor_name: str, emisor_regimen: str, lugar_expedicion: str):
        self.emisor = {
            "Rfc": emisor_rfc,
            "Nombre": emisor_name,
            "RegimenFiscal": emisor_regimen
        }
        self.lugar_expedicion = lugar_expedicion

    def generar_complemento_notarios(self, datos_operacion: dict) -> dict:
        """
        Generates the 'Complemento de Notarios Públicos'.
        Since satcfdi might not have a built-in high-level builder for this specific complement
        exposed easily, we construct the dictionary structure matching the XSD.

        datos_operacion expects:
        - num_escritura
        - fecha_inst_notarial
        - inmuebles: list of dicts with descriptions
        - copropiedad: dict with 'vendedores' and 'adquirientes' lists
        """

        # Static Notary Data for Notaría 4 Manzanillo
        datos_notario = {
            "NumNotaria": 4,
            "EntidadFederativa": "06", # Colima
            "Adscripcion": "MANZANILLO COLIMA"
        }

        desc_inmuebles = []
        for inm in datos_operacion.get('inmuebles', []):
            desc_inmuebles.append({
                "TipoInmueble": inm['tipo'], # e.g. 03 Casa Habitación
                "Calle": inm['calle'],
                "Municipio": inm['municipio'],
                "Estado": "06",
                "Pais": "MEX",
                "CodigoPostal": inm['cp']
            })

        # Construct the Complement Data
        # Note: This is a simplified structure. In satcfdi/CFDI 4.0, complements are passed
        # as objects or dicts to the 'complemento' argument.
        # We need to wrap it in the specific namespace/structure if using generic dicts.

        # TODO: integrate with actual satcfdi.create.cfd.notariospublicos10 if available
        # or construct the specific Export dict structure.

        # For now, returning the raw data structure which would be processed by a specific builder.
        # Assuming we return a dict that satcfdi can interpret or we attach manually.

        return {
            "DatosNotario": datos_notario,
            "DatosOperacion": {
                "NumInstrumentoNotarial": datos_operacion['num_escritura'],
                "FechaInstNotarial": datos_operacion['fecha_inst_notarial'],
                "MontoOperacion": datos_operacion['monto_operacion'],
                "Subtotal": datos_operacion['monto_operacion'], # Often same base
                "IVA": datos_operacion.get('iva_operacion', 0)
            },
            "DescInmuebles": {"DescInmueble": desc_inmuebles}
            # Copropiedad logic would go here under DatosAdquirientesCopSC if applicable
        }

    def generar_xml(self,
                    receptor_data: dict,
                    conceptos: list,
                    subtotal: Decimal,
                    is_persona_moral: bool,
                    datos_complemento: dict = None) -> cfdi40.Comprobante:
        """
        Generates a CFDI 4.0 Comprobante object.
        """

        # Determine Impuestos (Retentions) if Persona Moral
        # Note: In satcfdi, global taxes are calculated automatically if concepts have taxes defined.
        # However, for the Comprobante constructor, we can explicitly pass them if needed,
        # but the best practice with satcfdi is to define taxes at the Concepto level.

        # We will iterate over concepts to add taxes
        processed_conceptos = []
        for c in conceptos:
            traslados = []
            retenciones = []

            # IVA Traslado 16% (Base assumed to be amount)
            traslados.append({
                'Base': c['amount'],
                'Impuesto': '002', # IVA
                'TipoFactor': 'Tasa',
                'TasaOCuota': Decimal('0.160000'),
                'Importe': c['amount'] * Decimal('0.16')
            })

            if is_persona_moral:
                # ISR Retention 10%
                retenciones.append({
                    'Base': c['amount'],
                    'Impuesto': '001', # ISR
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': Decimal('0.100000'),
                    'Importe': c['amount'] * Decimal('0.10')
                })
                # IVA Retention 10.6667%
                retenciones.append({
                    'Base': c['amount'],
                    'Impuesto': '002', # IVA
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': Decimal('0.106667'),
                    'Importe': c['amount'] * Decimal('0.106667')
                })

            impuestos_concepto = {'Traslados': traslados}
            if retenciones:
                impuestos_concepto['Retenciones'] = retenciones

            concepto_args = {
                "ClaveProdServ": c['clave_prod_serv'],
                "Cantidad": Decimal(c['cantidad']),
                "ClaveUnidad": c['clave_unidad'],
                "Descripcion": c['descripcion'],
                "ValorUnitario": c['valor_unitario'],
                "Importe": c['amount'],
                "ObjetoImp": "02", # Sí objeto de impuesto
                "Impuestos": impuestos_concepto
            }
            # satcfdi handles dict conversion automatically
            processed_conceptos.append(concepto_args)

        # If Complemento is present
        complemento_obj = None
        if datos_complemento:
            # Here we would instantiate the specific Complemento class
            # For this MVP we are acknowledging the structure is passed.
            # In a full implementation we import notariospublicos10 from satcfdi
            pass

        cfdi = cfdi40.Comprobante(
            emisor=self.emisor,
            receptor={
                "Rfc": receptor_data['rfc'],
                "Nombre": receptor_data['nombre'],
                "DomicilioFiscalReceptor": receptor_data['cp'],
                "RegimenFiscalReceptor": receptor_data['regimen_fiscal'],
                "UsoCFDI": receptor_data['uso_cfdi']
            },
            lugar_expedicion=self.lugar_expedicion,
            metodo_pago=MetodoPago.PAGO_EN_UNA_SOLA_EXHIBICION,
            forma_pago=FormaPago.TRANSFERENCIA_ELECTRONICA_DE_FONDOS,
            tipo_de_comprobante=TipoDeComprobante.INGRESO,
            exportacion="01",
            moneda="MXN",
            conceptos=processed_conceptos,
            complemento=complemento_obj
        )

        # Satcfdi calculates totals automatically upon build/sign
        return cfdi
