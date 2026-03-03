from notaria_4_core.backend.lib.api_models import InvoiceRequest, Receptor, Concepto
from decimal import Decimal

def test_invoice_request():
    receptor = Receptor(rfc="ABC123456T12", nombre="TEST", uso_cfdi="G03", domicilio_fiscal="28200")
    assert receptor.rfc == "ABC123456T12"
