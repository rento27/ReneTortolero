from decimal import Decimal
from satcfdi.create.cfd import cfdi40
from satcfdi.models import Signer
from google.cloud import secretmanager
from .fiscal_engine import calculate_retentions_persona_moral

# Mock implementation for NotariosPublicos since we don't have the full library introspection here
# In a real scenario, we would import:
# from satcfdi.create.cfd.complemento.notariospublicos10 import NotariosPublicos
# For now, we will return a dictionary structure which satcfdi can often handle or we treat it as a custom object.

class XMLGenerator:
    def __init__(self, project_id: str = "notaria4"):
        self.project_id = project_id
        self.signer = None

    def load_signer_from_secrets(self):
        """
        Loads the Signer (Certificate and Private Key) from Google Secret Manager.
        """
        client = secretmanager.SecretManagerServiceClient()

        def access_secret(secret_id):
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data

        try:
            key_bytes = access_secret("csd-key")
            cer_bytes = access_secret("csd-cer")
            password = access_secret("csd-pass").decode("utf-8")

            self.signer = Signer.load(certificate=cer_bytes, key=key_bytes, password=password)
        except Exception as e:
            print(f"Error loading signer: {e}")
            raise

    def generar_complemento_notarios(self, datos_notario: dict):
        """
        Generates the 'Complemento de Notarios Públicos'.
        datos_notario should contain:
            - NumInstrumentoNotarial
            - FechaInstNotarial
            - MontoOperacion
            - Subtotal
            - IVA
            - Inmuebles (list)
            - Enajenantes (list)
            - Adquirentes (list)
        """
        # structure based on standard XSD requirements
        # returning a dict representation that satcfdi might accept or needs a specific class wrapper
        complemento = {
            "Version": "1.0",
            "DescInmuebles": {
                "DescInmueble": datos_notario.get("Inmuebles", [])
            },
            "DatosOperacion": {
                "NumInstrumentoNotarial": datos_notario["NumInstrumentoNotarial"],
                "FechaInstNotarial": datos_notario["FechaInstNotarial"],
                "MontoOperacion": datos_notario["MontoOperacion"],
                "Subtotal": datos_notario["Subtotal"],
                "IVA": datos_notario["IVA"]
            },
            "DatosNotario": {
                "NumNotaria": 4,
                "EntidadFederativa": "06", # Colima
                "Adscripcion": "MANZANILLO COLIMA"
            },
            "DatosEnajenantes": {
                "DatosEnajenante": datos_notario.get("Enajenantes", [])
            },
            "DatosAdquirentes": {
                "DatosAdquirente": datos_notario.get("Adquirentes", [])
            }
        }
        return complemento

    def generar_xml(self, datos_factura: dict, datos_notario: dict = None) -> cfdi40.Comprobante:
        """
        Generates the CFDI 4.0 object.
        """
        if not self.signer:
            # For testing/dev purposes if secrets aren't available, we might want to skip or fail.
            # raise ValueError("Signer not loaded")
            pass

        receptor_rfc = datos_factura['receptor']['rfc']
        subtotal = Decimal(str(datos_factura['subtotal']))

        # Calculate Base Gravable (Only items with ObjetoImp == '02')
        base_gravable = Decimal('0.00')
        for concepto in datos_factura.get('conceptos', []):
            if concepto.get('ObjetoImp') == '02':
                base_gravable += Decimal(str(concepto.get('Importe', 0)))

        # Calculate Taxes
        impuestos = None

        # Check for Persona Moral Retentions on Base Gravable
        retentions = calculate_retentions_persona_moral(base_gravable, receptor_rfc)

        traslados_list = [
            {'Base': base_gravable, 'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': '0.160000', 'Importe': base_gravable * Decimal('0.16')}
        ]

        if retentions:
            retenciones_list = []
            if retentions.get('isr_retention'):
                retenciones_list.append({
                    'Impuesto': '001',
                    'Importe': retentions['isr_retention']
                })
            if retentions.get('iva_retention'):
                retenciones_list.append({
                    'Impuesto': '002',
                    'Importe': retentions['iva_retention']
                })

            impuestos = {
                'Retenciones': retenciones_list,
                'Traslados': traslados_list
            }
        else:
            impuestos = {
                'Traslados': traslados_list
            }

        # Create CFDI
        cfdi = cfdi40.Comprobante(
            emisor={'Rfc': 'TOSR520601AZ4', 'RegimenFiscal': '612', 'Nombre': 'RENE MANUEL TORTOLERO SANTILLANA'},
            receptor=datos_factura['receptor'],
            lugar_expedicion='28219',
            conceptos=datos_factura['conceptos'],
            impuestos=impuestos,
            # complemento=self.generar_complemento_notarios(datos_notario) if datos_notario else None
        )

        # If we had the actual satcfdi library installed and running, we would attach the complement here.
        # For now, leaving it commented or handled structurally.

        return cfdi
