from decimal import Decimal
from satcfdi.create.cfd import cfdi40
from satcfdi.create.cfd.catalogos import RegimenFiscal, UsoCFDI, MetodoPago, FormaPago, TipoDeComprobante
# Assuming standard satcfdi structure for complements
try:
    from satcfdi.create.complementos.notariospublicos10 import NotariosPublicos
except ImportError:
    # Fallback or mock if library structure varies
    NotariosPublicos = None

from .fiscal_engine import calculate_retentions

class XMLGenerator:
    def __init__(self, signer, lugar_expedicion="28200"):
        self.signer = signer
        self.lugar_expedicion = lugar_expedicion

    def generar_complemento_notarios(self, datos_notario):
        """
        Generates the Notarios Publicos complement.
        """
        # This manually constructs the object based on the expected inputs
        # In a real scenario, we would map specific fields from datos_notario
        if NotariosPublicos:
            return NotariosPublicos(
                version="1.0",
                datos_notario=datos_notario.get("DatosNotario"),
                datos_operacion=datos_notario.get("DatosOperacion"),
                datos_inmueble=datos_notario.get("DatosInmueble"),
                datos_adquirientes=datos_notario.get("DatosAdquirientes")
            )
        else:
            # Return dict representation if class not available
            return {
                "notariospublicos:NotariosPublicos": datos_notario
            }

    def generar_cfdi(self, datos_factura, datos_complemento=None):
        """
        Generates and signs the CFDI 4.0
        """
        receptor = datos_factura['receptor']
        conceptos = datos_factura['conceptos']

        # Calculate global retentions if applicable (Persona Moral)
        # Note: satcfdi calculates taxes automatically if 'Impuestos' are added to Conceptos
        # The prompt says: "The core must implement a fiscal rules engine... if Len(RFC)==12..."
        # But in CFDI 4.0, taxes are defined per concept and then summarized.
        # We need to inject the taxes into the concepts.

        processed_concepts = []
        for c in conceptos:
            concepto_args = {
                "ClaveProdServ": c['clave_prod_serv'],
                "Cantidad": Decimal(c['cantidad']),
                "ClaveUnidad": c['clave_unidad'],
                "Descripcion": c['descripcion'],
                "ValorUnitario": Decimal(c['valor_unitario']),
                "Importe": Decimal(c['importe']),
                "ObjetoImp": c['objeto_imp']
            }

            # Logic for taxes
            if c['objeto_imp'] == '02': # Sí objeto de impuesto
                traslados = cfdi40.Impuesto.Traslado(
                    Base=Decimal(c['importe']),
                    Impuesto='002', # IVA
                    TipoFactor='Tasa',
                    TasaOCuota=Decimal('0.160000'),
                    Importe=Decimal(c['importe']) * Decimal('0.16')
                )

                impuestos_concepto = {'Traslados': [traslados]}

                # Check for retentions (Persona Moral)
                if len(receptor['rfc']) == 12:
                    retentions_calc = calculate_retentions(Decimal(c['importe']), receptor['rfc'])
                    retenciones = []

                    if retentions_calc['isr_ret'] > 0:
                        retenciones.append(cfdi40.Impuesto.Retencion(
                            Base=Decimal(c['importe']),
                            Impuesto='001', # ISR
                            TipoFactor='Tasa',
                            TasaOCuota=Decimal('0.100000'),
                            Importe=retentions_calc['isr_ret']
                        ))

                    if retentions_calc['iva_ret'] > 0:
                        retenciones.append(cfdi40.Impuesto.Retencion(
                            Base=Decimal(c['importe']),
                            Impuesto='002', # IVA
                            TipoFactor='Tasa',
                            TasaOCuota=Decimal('0.106667'),
                            Importe=retentions_calc['iva_ret']
                        ))

                    if retenciones:
                        impuestos_concepto['Retenciones'] = retenciones

                concepto_args['Impuestos'] = impuestos_concepto

            processed_concepts.append(cfdi40.Concepto(**concepto_args))

        # Create Comprobante
        cfdi = cfdi40.Comprobante(
            Emisor=datos_factura['emisor'],
            Receptor=datos_factura['receptor'],
            Conceptos=processed_concepts,
            LugarExpedicion=self.lugar_expedicion,
            MetodoPago=datos_factura.get('metodo_pago', 'PUE'),
            FormaPago=datos_factura.get('forma_pago', '03'),
            Moneda=datos_factura.get('moneda', 'MXN'),
            TipoDeComprobante=TipoDeComprobante.INGRESO,
            Exportacion='01', # No aplica generally
            Complemento=self.generar_complemento_notarios(datos_complemento) if datos_complemento else None
        )

        # Sign
        if self.signer:
            cfdi.sign(self.signer)

        return cfdi
