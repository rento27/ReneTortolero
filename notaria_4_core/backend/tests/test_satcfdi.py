import os
from decimal import Decimal
from backend.lib.xml_generator import generate_signed_xml

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
            'fecha_inst_notarial': '2023-10-27',
            'desc_inmuebles': [
                {
                    'tipo_inmueble': '03',
                    'calle': 'Av. Principal',
                    'municipio': 'Manzanillo',
                    'estado': 'COL',
                    'pais': 'MEX',
                    'codigo_postal': '28200'
                }
            ],
            'datos_enajenantes': [
                {
                    'copro_soc_conyugal_e': 'Si',
                    'nombre': 'JUAN',
                    'apellido_paterno': 'PEREZ',
                    'apellido_materno': 'GOMEZ',
                    'rfc': 'PEGJ800101XYZ',
                    'curp': 'PEGJ800101HDFRRA00',
                    'porcentaje': 50.00
                },
                {
                    'copro_soc_conyugal_e': 'Si',
                    'nombre': 'MARIA',
                    'apellido_paterno': 'LOPEZ',
                    'apellido_materno': 'DIAZ',
                    'rfc': 'LODM800101XYZ',
                    'curp': 'LODM800101MDFRRA00',
                    'porcentaje': 50.00
                }
            ],
            'datos_adquirientes': [
                {
                    'copro_soc_conyugal_e': 'No',
                    'nombre': 'PEDRO RAMIREZ',
                    'rfc': 'RAPE800101XYZ',
                    'curp': 'RAPE800101HDFRRA00'
                }
            ]
        }
    }

    xml = generate_signed_xml(data)
    assert xml is not None
