from decimal import Decimal
import pytest
from pydantic import ValidationError
from notaria_4_core.backend.lib.api_models import InvoiceRequest, Receptor, Concepto, ComplementoNotariosModel, DatosNotario

def test_receptor_validation():
    # Valid Receptor
    r = Receptor(
        rfc="TOSR520601AZ4",
        nombre="RENE MANUEL TORTOLERO SANTILLANA",
        uso_cfdi="G03",
        domicilio_fiscal="28200",
        regimen_fiscal="612"
    )
    assert r.rfc == "TOSR520601AZ4"

def test_datos_notario_curp_validation():
    # Valid CURP (18 chars)
    dn = DatosNotario(
        curp="ABCD123456HDFRDA01",
        num_notaria=4,
        entidad_federativa="06"
    )
    assert dn.curp == "ABCD123456HDFRDA01"

    # Invalid CURP (short)
    with pytest.raises(ValidationError):
        DatosNotario(
            curp="SHORT",
            num_notaria=4,
            entidad_federativa="06"
        )
