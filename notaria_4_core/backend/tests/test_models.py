from decimal import Decimal
import pytest
from pydantic import ValidationError
from notaria_4_core.backend.lib.api_models import DatosNotario, DatosAdquiriente

def test_datos_notario_curp_length():
    with pytest.raises(ValidationError):
        DatosNotario(
            curp="SHORT123",
            num_notaria=4,
            entidad_federativa="06",
            adscripcion="MANZANILLO"
        )

    with pytest.raises(ValidationError):
        DatosNotario(
            curp="TOOLONG1234567890123",
            num_notaria=4,
            entidad_federativa="06",
            adscripcion="MANZANILLO"
        )

    # Valid
    notario = DatosNotario(
        curp="TOSR520601HOCMXA00",
        num_notaria=4,
        entidad_federativa="06",
        adscripcion="MANZANILLO"
    )
    assert notario.curp == "TOSR520601HOCMXA00"

def test_datos_adquiriente_optional_fields():
    # Only name
    adq = DatosAdquiriente(
        nombre="Juan",
        rfc="JUAN123456",
        curp="JUAN12345678901234",
        copro_soc_conyugal_e="No"
    )
    assert adq.apellido_paterno is None

    # All names
    adq2 = DatosAdquiriente(
        nombre="Juan",
        apellido_paterno="Perez",
        apellido_materno="Gomez",
        rfc="JUAN123456",
        curp="JUAN12345678901234",
        copro_soc_conyugal_e="No"
    )
    assert adq2.apellido_paterno == "Perez"
