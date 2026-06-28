import pytest
from notaria_4_core.backend.lib.pdf_generator import generate_hybrid_pdf
from notaria_4_core.backend.lib.nom151 import request_nom151_constancia

def test_generate_hybrid_pdf():
    xml_bytes = b"<xml>mock cfdi</xml>"
    invoice_data = {
        'receptor': {
            'rfc': 'ABC123456T12',
            'nombre': 'EMPRESA SA DE CV',
        },
        'subtotal': '1000.00',
        'total': '1160.00',
        'conceptos': [
            {
                'descripcion': 'HONORARIOS NOTARIALES',
                'importe': '1000.00',
            }
        ]
    }

    pdf_bytes = generate_hybrid_pdf(xml_bytes, invoice_data)

    # Check that bytes are returned
    assert isinstance(pdf_bytes, bytes)
    # The output from weasyprint will be a PDF or the fallback mock PDF bytes
    assert len(pdf_bytes) > 0

def test_request_nom151_constancia():
    mock_hash = "abcdef123456"
    response = request_nom151_constancia(mock_hash)

    assert isinstance(response, dict)
    assert response.get("status") == "success"
    assert response.get("psc") == "WeeSign Mock"
    assert response.get("document_hash") == mock_hash
    assert "timestamp" in response
    assert "constancia_id" in response
    assert "signature" in response
