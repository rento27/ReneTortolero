import os
import pytest
from decimal import Decimal
from notaria_4_core.backend.lib.xml_generator import generate_signed_xml

def test_generate_xml():
    os.environ["MOCK_SIGNER"] = "1"
    data = {
        'receptor': {
            'rfc': 'ABC123456T12',
            'nombre': 'EMPRESA SA DE CV',
            'uso_cfdi': 'G03',
            'domicilio_fiscal': '28200'
        },
        'subtotal': '1000.00',
        'total': '1053.33',
        'conceptos': [
            {
                'clave_prod_serv': '84111506',
                'cantidad': '1.00',
                'clave_unidad': 'E48',
                'descripcion': 'HONORARIOS NOTARIALES',
                'valor_unitario': '1000.00',
                'importe': '1000.00',
                'objeto_imp': '02'
            }
        ]
    }

    xml = generate_signed_xml(data)
    assert xml is not None

def test_generate_xml_with_complemento():
    os.environ["MOCK_SIGNER"] = "1"
    data = {
        'receptor': {
            'rfc': 'ABC123456T12',
            'nombre': 'EMPRESA SA DE CV',
            'uso_cfdi': 'G03',
            'domicilio_fiscal': '28200'
        },
        'subtotal': '1000.00',
        'total': '1053.33',
        'conceptos': [
            {
                'clave_prod_serv': '84111506',
                'cantidad': '1.00',
                'clave_unidad': 'E48',
                'descripcion': 'HONORARIOS NOTARIALES',
                'valor_unitario': '1000.00',
                'importe': '1000.00',
                'objeto_imp': '02'
            }
        ],
        'complemento_notarios': {
            'version': '1.0',
            'fecha_inst_notarial': '2025-01-01',
            'desc_inmuebles': [
                {
                    'tipo_inmueble': '03',
                    'calle': 'CALLE PRINCIPAL',
                    'municipio': 'MANZANILLO',
                    'estado': 'COL',
                    'codigo_postal': '28200'
                }
            ],
            'datos_enajenantes': [
                {
                    'copro_soc_conyugal_e': 'No',
                    'nombre': 'JUAN PEREZ',
                    'rfc': 'PEPJ800101XYZ',
                    'curp': 'PEPJ800101HOCXYZ00'
                }
            ],
            'datos_adquirientes': [
                {
                    'copro_soc_conyugal_e': 'No',
                    'nombre': 'MARIA GOMEZ',
                    'rfc': 'GOMM850101ABC',
                    'curp': 'GOMM850101MOCABC00'
                }
            ]
        }
    }

    xml = generate_signed_xml(data)
    assert xml is not None
