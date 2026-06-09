import os
import pytest
from decimal import Decimal
from notaria_4_core.backend.lib.xml_generator import generate_signed_xml

from unittest.mock import patch

@patch('notaria_4_core.backend.lib.xml_generator.load_signer_from_secret_manager')
@patch('satcfdi.create.cfd.cfdi40.Comprobante.sign')
@patch('satcfdi.create.cfd.cfdi40.Comprobante.xml_bytes')
def test_generate_xml(mock_xml_bytes, mock_sign, mock_load_signer):
    mock_load_signer.return_value = "MockedSigner"
    mock_xml_bytes.return_value = b"<mock>xml</mock>"

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
    assert xml == b"<mock>xml</mock>"
    mock_load_signer.assert_called_once()
    mock_sign.assert_called_once_with("MockedSigner")
    mock_xml_bytes.assert_called_once()
