import os
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from notaria_4_core.backend.lib.xml_generator import generate_signed_xml

@patch('notaria_4_core.backend.lib.xml_generator.load_signer_from_secret_manager')
@patch('satcfdi.create.cfd.cfdi40.Comprobante.sign')
def test_generate_xml_with_complemento(mock_sign, mock_load_signer):
    mock_load_signer.return_value = MagicMock()
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
            'fecha_inst_notarial': '2023-10-10',
            'desc_inmuebles': [
                {
                    'tipo_inmueble': '01',
                    'calle': 'Calle 1',
                    'estado': 'COL',
                    'municipio': '007',
                    'pais': 'MEX',
                    'codigo_postal': '28200'
                }
            ],
            'datos_enajenantes': [
                {
                    'copro_soc_conyugal_e': 'No',
                    'nombre': 'Juan Perez',
                    'rfc': 'JUPA800101XYZ',
                    'curp': 'JUPA800101XYZABCDE'
                }
            ],
            'datos_adquirientes': [
                {
                    'copro_soc_conyugal_e': 'No',
                    'nombre': 'Maria Gomez',
                    'rfc': 'MAGO800101XYZ',
                    'curp': 'MAGO800101XYZABCDE'
                }
            ]
        }
    }

    xml = generate_signed_xml(data)
    assert xml is not None
