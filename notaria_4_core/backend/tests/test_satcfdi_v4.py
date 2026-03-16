import pytest
from decimal import Decimal
from satcfdi.create.cfd import cfdi40

def test_satcfdi_comprobante_v4():
    cfdi = cfdi40.Comprobante(
        emisor={
            'Rfc': 'TOSR520601AZ4',
            'RegimenFiscal': '612',
            'Nombre': 'RENE MANUEL TORTOLERO SANTILLANA'
        },
        receptor={
            'Rfc': 'XAXX010101000',
            'Nombre': 'PUBLICO EN GENERAL',
            'UsoCFDI': 'G03',
            'DomicilioFiscalReceptor': '28200',
            'RegimenFiscalReceptor': '601'
        },
        conceptos=[
            {
                'ClaveProdServ': '80121600',
                'Cantidad': Decimal('1.0'),
                'ClaveUnidad': 'E48',
                'Descripcion': 'HONORARIOS',
                'ValorUnitario': Decimal('1000.00'),
                'Importe': Decimal('1000.00'),
                'ObjetoImp': '02'
            }
        ],
        moneda='MXN',
        tipo_de_comprobante='I',
        lugar_expedicion='28200',
        exportacion='01'
    )
    assert cfdi is not None
