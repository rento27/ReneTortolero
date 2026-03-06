from pydantic import ValidationError
from decimal import Decimal
import pytest
from notaria_4_core.backend.lib.api_models import DatosNotario, Receptor, ISAIRequest, ComplementoNotariosModel

def test_datos_notario_curp_length():
    with pytest.raises(ValidationError):
        DatosNotario(curp="123") # Too short

    with pytest.raises(ValidationError):
        DatosNotario(curp="1234567890123456789") # Too long

    # Correct length
    notario = DatosNotario(curp="TOSR520601HOCMXA00")
    assert notario.curp == "TOSR520601HOCMXA00"

def test_receptor_model():
    r = Receptor(
        rfc="ABC123456T12",
        nombre="Test",
        uso_cfdi="G03",
        domicilio_fiscal="28200",
        regimen_fiscal="601"
    )
    assert r.regimen_fiscal == "601"

def test_isai_request():
    req = ISAIRequest(precio_operacion=Decimal("100"), valor_catastral=Decimal("150"))
    assert req.tasa == Decimal("0.03") # default
