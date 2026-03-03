from decimal import Decimal
from satcfdi.create.cfd import cfdi40

impuestos = {
    'Retenciones': [
        {'Impuesto': '001', 'TipoFactor': 'Tasa', 'TasaOCuota': Decimal('0.100000'), 'Importe': Decimal('100.00'), 'Base': Decimal('1000.00')},
        {'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': Decimal('0.106667'), 'Importe': Decimal('106.67'), 'Base': Decimal('1000.00')}
    ],
    'Traslados': [
        {'Impuesto': '002', 'TipoFactor': 'Tasa', 'TasaOCuota': Decimal('0.160000'), 'Importe': Decimal('160.00'), 'Base': Decimal('1000.00')}
    ]
}

concepto = cfdi40.Concepto(
    clave_prod_serv='84111506',
    cantidad=Decimal('1'),
    clave_unidad='E48',
    descripcion='Honorarios',
    valor_unitario=Decimal('1000.00'),
    objeto_imp='02',
    impuestos=impuestos
)

comp = cfdi40.Comprobante(
    emisor={
        'Rfc': 'TOSR520601AZ4',
        'RegimenFiscal': '612',
        'Nombre': 'RENE MANUEL TORTOLERO SANTILLANA'
    },
    receptor={
        'Rfc': 'ABC123456T12',
        'Nombre': 'EMPRESA PRUEBA',
        'UsoCFDI': 'G03',
        'DomicilioFiscalReceptor': '28200',
        'RegimenFiscalReceptor': '601'
    },
    conceptos=[concepto],
    lugar_expedicion='28200'
)

print(comp.xml_bytes())
