import os
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from notaria_4_core.backend.lib.xml_generator import generate_signed_xml

def test_generate_xml_with_mocked_signer():
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

    with patch('notaria_4_core.backend.lib.xml_generator.load_signer_from_secret_manager') as mock_load_signer:
        with patch('satcfdi.create.cfd.cfdi40.Comprobante.sign') as mock_sign:
            # We mock the signer
            mock_signer = MagicMock()
            mock_load_signer.return_value = mock_signer

            xml = generate_signed_xml(data)
            assert xml is not None
            mock_sign.assert_called_once_with(mock_signer)

def test_generate_xml_missing_signer_raises_error():
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

    with patch('notaria_4_core.backend.lib.xml_generator.load_signer_from_secret_manager') as mock_load_signer:
        mock_load_signer.return_value = None

        with pytest.raises(ValueError, match="Signer could not be loaded from Secret Manager."):
            generate_signed_xml(data)
