from decimal import Decimal
import pytest
from notaria_4_core.backend.lib.complement_notarios import create_complemento_notarios, validate_percentages, split_name_fallback
from notaria_4_core.backend.lib.api_models import ComplementoNotariosModel, DatosNotario, DatosOperacion, DatosInmueble, DatosAdquiriente, DatosAdquirienteCopSC

def test_validate_percentages_success():
    # Mock items
    item1 = DatosAdquirienteCopSC(nombre="A", porcentaje=Decimal("50.00"), rfc="X", curp="X")
    item2 = DatosAdquirienteCopSC(nombre="B", porcentaje=Decimal("50.00"), rfc="X", curp="X")

    adq = DatosAdquiriente(
        nombre="Grupo",
        copro_soc_conyugal_e="Si",
        copropietarios=[item1, item2]
    )

    # Should pass
    validate_percentages([adq], "Adquiriente")

def test_validate_percentages_fail():
    item1 = DatosAdquirienteCopSC(nombre="A", porcentaje=Decimal("33.33"), rfc="X", curp="X")
    item2 = DatosAdquirienteCopSC(nombre="B", porcentaje=Decimal("33.33"), rfc="X", curp="X")
    item3 = DatosAdquirienteCopSC(nombre="C", porcentaje=Decimal("33.33"), rfc="X", curp="X")

    adq = DatosAdquiriente(
        nombre="Grupo",
        copro_soc_conyugal_e="Si",
        copropietarios=[item1, item2, item3]
    )

    with pytest.raises(ValueError):
        validate_percentages([adq], "Adquiriente")

def test_split_name_fallback():
    n, p, m = split_name_fallback("JUAN PEREZ LOPEZ")
    assert n == "JUAN"
    assert p == "PEREZ"
    assert m == "LOPEZ"

    n, p, m = split_name_fallback("JUAN PEREZ")
    assert n == "JUAN"
    assert p == "PEREZ"
    assert m is None
