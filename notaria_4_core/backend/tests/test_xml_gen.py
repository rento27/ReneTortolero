from decimal import Decimal
import pytest
from notaria_4_core.backend.lib.xml_generator import generate_signed_xml

def test_xml_generation():
    data = {
        'receptor': {
            'rfc': 'ABC123456T12', # 12 chars -> Moral -> trigger retentions
            'nombre': 'INMOBILIARIA DEL PACÍFICO, S.A. DE C.V.',
            'uso_cfdi': 'G03',
            'domicilio_fiscal': '28200',
            'regimen_fiscal': '601'
        },
        'conceptos': [
            {
                'clave_prod_serv': '80141600',
                'cantidad': 1,
                'clave_unidad': 'E48',
                'descripcion': 'Honorarios',
                'valor_unitario': 1000,
                'importe': 1000,
                'objeto_imp': '02'
            }
        ],
        'subtotal': 1000,
        'total': 1160,
    }

    xml = generate_signed_xml(data).decode('utf-8')
    assert "INMOBILIARIA DEL PACIFICO" in xml
    assert "Retencion" in xml # retentions should be present
    assert "Impuesto=\"001\"" in xml # ISR
    assert "TasaOCuota=\"0.106667\"" in xml # IVA Ret
