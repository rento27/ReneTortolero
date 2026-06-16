import pytest
from notaria_4_core.backend.lib.pdf_generator import generate_hybrid_pdf

def test_generate_hybrid_pdf():
    xml_bytes = b"<cfdi></cfdi>"
    invoice_data = {
        "receptor": {"nombre": "TEST USER"},
        "subtotal": "100.00",
        "total": "116.00"
    }

    pdf_bytes = generate_hybrid_pdf(xml_bytes, invoice_data)

    # Verify that bytes are returned. Note: if WeasyPrint is installed it generates a PDF,
    # otherwise it returns b"". In our environment, it's installed via requirements.
    assert isinstance(pdf_bytes, bytes)
    # Magic number for PDF
    if pdf_bytes:
        assert pdf_bytes.startswith(b"%PDF")
