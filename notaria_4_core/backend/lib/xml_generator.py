from satcfdi.create.cfd import cfdi40
from satcfdi.models import Signer
from decimal import Decimal

class XMLGenerator:
    def __init__(self):
        self.signer = None

    def load_signer(self, certificate_bytes, key_bytes, password):
        """
        Loads the signer from bytes (retrieved from Secret Manager).
        """
        self.signer = Signer.load(
            certificate=certificate_bytes,
            key=key_bytes,
            password=password
        )

    def _generate_complemento_notarios(self, data: dict):
        """
        Generates the 'Complemento de Notarios Públicos' node.
        """
        # Note: In a full implementation, this would map to the specific XSD classes
        # provided by satcfdi or a custom binding.
        # Structure example based on standard XSD:

        datos_notario = {
            "NumNotaria": 4,
            "EntidadFederativa": "06", # Colima
            "Adscripcion": "MANZANILLO COLIMA"
        }

        datos_operacion = {
            "NumInstrumentoNotarial": data.get("numero_escritura"),
            "FechaInstNotarial": data.get("fecha_firma"),
            "MontoOperacion": Decimal(str(data.get("monto_operacion", 0))),
            "Subtotal": Decimal(str(data.get("subtotal", 0))),
            "IVA": Decimal(str(data.get("iva_trasladado", 0)))
        }

        # Copropiedad validation logic
        copropietarios = data.get("copropietarios", [])
        if copropietarios:
            total_percentage = sum(Decimal(str(c['porcentaje'])) for c in copropietarios)
            if abs(total_percentage - Decimal("100.00")) > Decimal("0.01"):
                raise ValueError(f"Copropiedad percentages must sum to 100.00%, got {total_percentage}")

        # Return a dictionary or object representing the node
        # For now, returning a dict representation to show structure
        return {
            "DatosNotario": datos_notario,
            "DatosOperacion": datos_operacion,
            "DatosAdquirientes": copropietarios
        }

    def create_cfdi(self, data: dict) -> str:
        """
        Generates the CFDI 4.0 XML.
        """
        # Prepare taxes
        impuestos = None
        if data.get('retentions', {}).get('is_persona_moral'):
            impuestos = {
                'Retenciones': [
                    {'Impuesto': '001', 'Importe': Decimal(str(data['retentions']['isr_retention']))},
                    {'Impuesto': '002', 'Importe': Decimal(str(data['retentions']['iva_retention']))}
                ],
                'Traslados': [
                     {'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': Decimal('0.160000'), 'Importe': Decimal(str(data['iva_trasladado']))}
                ]
            }
        else:
             impuestos = {
                'Traslados': [
                     {'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': Decimal('0.160000'), 'Importe': Decimal(str(data['iva_trasladado']))}
                ]
            }

        # Generate Complemento
        complemento_node = self._generate_complemento_notarios(data)

        cfdi = cfdi40.Comprobante(
            Emisor={
                'Rfc': 'TOSR520601AZ4', # Notario RFC (Constant)
                'Nombre': 'RENE MANUEL TORTOLERO SANTILLANA',
                'RegimenFiscal': '612'
            },
            Receptor={
                'Rfc': data['rfc_receiver'],
                'Nombre': data['receiver_name'], # Must be sanitized
                'UsoCFDI': data['uso_cfdi'],
                'DomicilioFiscalReceptor': data['cp_receiver'],
                'RegimenFiscalReceptor': data['regimen_receiver']
            },
            LugarExpedicion='28219', # Manzanillo
            Conceptos=data['conceptos'],
            Impuestos=impuestos
            # In a real scenario, the Complemento object would be passed here
            # Complemento=complemento_node
        )

        if self.signer:
            cfdi.sign(self.signer)
            return cfdi.xml_bytes().decode('utf-8')
        else:
            return "XML structure created but not signed (Signer not loaded)"
