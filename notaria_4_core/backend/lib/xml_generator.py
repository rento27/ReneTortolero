from satcfdi.create.cfd import cfdi40
from satcfdi.create.cfd.catalogos import RegimenFiscal, UsoCFDI, MetodoPago, FormaPago, TipoDeComprobante

class XMLGenerator:
    @staticmethod
    def generate_invoice(data: dict, signer=None):
        """
        Generates a CFDI 4.0 object based on provided data.
        """
        receptor = data['receptor']
        emisor = data['emisor']
        conceptos = data['conceptos']

        # Basic CFDI Structure
        comprobante = cfdi40.Comprobante(
            Emisor=emisor,
            Receptor=receptor,
            Conceptos=conceptos,
            LugarExpedicion=emisor.get('CodigoPostal'),
            MetodoPago=MetodoPago.PAGO_EN_UNA_SOLA_EXHIBICION,
            FormaPago=FormaPago.TRANSFERENCIA_ELECTRONICA_DE_FONDOS,
            TipoDeComprobante=TipoDeComprobante.INGRESO,
            Exportacion="01", # No aplica
            Moneda="MXN",
            SubTotal=data['subtotal'],
            Total=data['total']
        )

        if signer:
            comprobante.sign(signer)

        return comprobante

    @staticmethod
    def generate_complemento_notarios(data: dict):
        """
        Stub for generating the 'Complemento de Notarios Públicos'.
        Requires specific XSD mapping which satcfdi supports via generic structures or extensions.
        """
        # Note: In a real implementation, we would import the specific module or build the dict
        # structure conforming to http://www.sat.gob.mx/notariospublicos

        complemento = {
            "NumNotaria": 4,
            "EntidadFederativa": "06", # Colima
            "Adscripcion": "MANZANILLO COLIMA",
            "DatosOperacion": {
                "FechaInstNotarial": data.get('fecha_firma'),
                "MontoOperacion": data.get('monto_operacion'),
                "SubTotal": data.get('subtotal'),
                "IVA": data.get('iva')
            },
            "DatosNotario": {
                "CURP": data.get('notario_curp'),
                "NumNotaria": 4,
                "EntidadFederativa": "06",
                "Adscripcion": "MANZANILLO COLIMA"
            },
            "DatosAdquirientes": data.get('adquirientes'), # List of acquirers
            # ... and so on for Enajenantes, Inmuebles
        }
        return complemento
