import pytest
from unittest.mock import patch, MagicMock
from notaria_4_core.backend.lib.xml_generator import generate_signed_xml

@patch('notaria_4_core.backend.lib.xml_generator.cfdi40')
@patch('notaria_4_core.backend.lib.xml_generator.load_signer_from_secret_manager')
def test_generate_xml_success(mock_load_signer, mock_cfdi40):
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

    mock_signer = MagicMock()
    mock_load_signer.return_value = mock_signer

    mock_comprobante_instance = MagicMock()
    mock_comprobante_instance.xml_bytes.return_value = b"<xml>signed</xml>"
    mock_cfdi40.Comprobante.return_value = mock_comprobante_instance

    xml = generate_signed_xml(data)
    assert xml == b"<xml>signed</xml>"
    mock_comprobante_instance.sign.assert_called_once_with(mock_signer)

@patch('notaria_4_core.backend.lib.xml_generator.cfdi40')
@patch('notaria_4_core.backend.lib.xml_generator.load_signer_from_secret_manager')
def test_generate_xml_no_signer(mock_load_signer, mock_cfdi40):
    data = {
        'receptor': {
            'rfc': 'ABC123456T12',
            'nombre': 'EMPRESA',
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
                'descripcion': 'HONORARIOS',
                'valor_unitario': '1000.00',
                'importe': '1000.00',
                'objeto_imp': '02'
            }
        ]
    }

    mock_load_signer.return_value = None
    mock_cfdi40.Comprobante.return_value = MagicMock()

    with pytest.raises(ValueError, match="Signer could not be loaded from Secret Manager."):
        generate_signed_xml(data)
