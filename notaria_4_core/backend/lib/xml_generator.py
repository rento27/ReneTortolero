from satcfdi.create.cfd import cfdi40
from satcfdi.create.cfd.catalogos import RegimenFiscal, UsoCFDI, MetodoPago, FormaPago, TipoDeComprobante
from decimal import Decimal
from .fiscal_engine import FiscalEngine

class XMLGenerator:
    def __init__(self, signer):
        self.signer = signer

    def generate_invoice(self, invoice_data: dict, notary_data: dict):
        """
        Generates a signed CFDI 4.0 XML.
        """
        subtotal = Decimal(str(invoice_data['subtotal']))
        rfc_receptor = invoice_data['receptor']['rfc']

        # Calculate Taxes/Retentions
        retentions = FiscalEngine.calculate_retentions(subtotal, rfc_receptor)

        # Build Conceptos
        conceptos = []
        for item in invoice_data['items']:
            conceptos.append({
                'ClaveProdServ': item['clave_prod_serv'],
                'Cantidad': Decimal(item['cantidad']),
                'ClaveUnidad': item['clave_unidad'],
                'Descripcion': item['descripcion'],
                'ValorUnitario': Decimal(str(item['valor_unitario'])),
                'Importe': Decimal(str(item['importe'])),
                'ObjetoImp': '02', # Si objeto de impuesto
                'Impuestos': {
                    'Traslados': [
                        {'Base': Decimal(str(item['importe'])), 'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': Decimal('0.160000'), 'Importe': Decimal(str(item['importe'])) * Decimal('0.16')}
                    ]
                }
            })

        # Build Impuestos Globales
        impuestos_globales = {
            'Traslados': [
                {'Base': subtotal, 'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': Decimal('0.160000'), 'Importe': subtotal * Decimal('0.16')}
            ]
        }

        if retentions['is_persona_moral']:
            impuestos_globales['Retenciones'] = [
                {'Impuesto': '001', 'Importe': retentions['isr']}, # ISR
                {'Impuesto': '002', 'Importe': retentions['iva']}  # IVA
            ]

        # Create Comprobante
        cfdi = cfdi40.Comprobante(
            Emisor={
                'Rfc': 'TOSR520601AZ4', # Example RFC from spec
                'Nombre': 'RENE MANUEL TORTOLERO SANTILLANA',
                'RegimenFiscal': '612' # Personas Físicas con Actividades Empresariales y Profesionales (Example)
            },
            Receptor={
                'Rfc': rfc_receptor,
                'Nombre': FiscalEngine.sanitize_name(invoice_data['receptor']['nombre']),
                'UsoCFDI': UsoCFDI.GASTOS_EN_GENERAL,
                'DomicilioFiscalReceptor': invoice_data['receptor']['cp'],
                'RegimenFiscalReceptor': invoice_data['receptor']['regimen']
            },
            LugarExpedicion='28219', # Manzanillo
            MetodoPago=MetodoPago.PAGO_EN_UNA_SOLA_EXHIBICION,
            FormaPago=FormaPago.TRANSFERENCIA_ELECTRONICA_DE_FONDOS,
            TipoDeComprobante=TipoDeComprobante.INGRESO,
            Moneda='MXN',
            SubTotal=subtotal,
            Total=subtotal + (subtotal * Decimal('0.16')) - retentions.get('isr', 0) - retentions.get('iva', 0),
            Conceptos=conceptos,
            Impuestos=impuestos_globales
        )

        # Sign
        cfdi.sign(self.signer)

        return cfdi.xml_bytes()
