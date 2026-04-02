import pytest
from decimal import Decimal
from unittest.mock import MagicMock

# We have to mock satcfdi module to test complement_notarios without error,
# or we can test if it raises ImportError if satcfdi is not available.
# Since the codebase handles the case where satcfdi is present, let's test assuming it's available.

import sys
from notaria_4_core.backend.lib.api_models import ComplementoNotariosModel, DatosAdquiriente, DatosEnajenante, DescInmueble

# Mocking satcfdi just in case it's not present in test environment, but simulating dictionary access.
class MockElement(dict):
    pass

class MockNotariosPublicos(MockElement):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class MockDatosAdquiriente(MockElement):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class MockDatosEnajenante(MockElement):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class MockDescInmueble(MockElement):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class MockDatosAdquirienteCopSC(MockElement):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class MockDatosEnajenanteCopSC(MockElement):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class MockDatosUnAdquiriente(MockElement):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class MockDatosUnEnajenante(MockElement):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class MockDatosOperacion(MockElement):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class MockDatosNotario(MockElement):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

import notaria_4_core.backend.lib.complement_notarios as comp_mod

# Injecting the mock
mock_notariospublicos10 = MagicMock()
mock_notariospublicos10.NotariosPublicos = MockNotariosPublicos
mock_notariospublicos10.DatosAdquiriente = MockDatosAdquiriente
mock_notariospublicos10.DatosEnajenante = MockDatosEnajenante
mock_notariospublicos10.DescInmueble = MockDescInmueble
mock_notariospublicos10.DatosAdquirienteCopSC = MockDatosAdquirienteCopSC
mock_notariospublicos10.DatosEnajenanteCopSC = MockDatosEnajenanteCopSC
mock_notariospublicos10.DatosUnAdquiriente = MockDatosUnAdquiriente
mock_notariospublicos10.DatosUnEnajenante = MockDatosUnEnajenante
mock_notariospublicos10.DatosOperacion = MockDatosOperacion
mock_notariospublicos10.DatosNotario = MockDatosNotario

comp_mod.notariospublicos10 = mock_notariospublicos10

def test_create_complemento_notarios():
    model = ComplementoNotariosModel(
        fecha_inst_notarial="2023-10-15",
        desc_inmuebles=[
            DescInmueble(
                tipo_inmueble="01",
                calle="Main St",
                estado="COL",
                codigo_postal="28200"
            )
        ],
        datos_enajenantes=[
            DatosEnajenante(
                copro_soc_conyugal_e="No",
                nombre="John Doe",
                rfc="DOEJ800101XXX",
                curp="DOEJ800101XXXXXX00"
            )
        ],
        datos_adquirientes=[
            DatosAdquiriente(
                copro_soc_conyugal_e="Si",
                nombre="Jane Smith",
                rfc="SMIJ800101XXX",
                curp="SMIJ800101XXXXXX00",
                porcentaje=Decimal("100.00")
            )
        ]
    )

    comp = comp_mod.create_complemento_notarios(model)

    # Since MockNotariosPublicos inherits from dict, we can test dictionary access:
    assert 'datos_adquiriente' in comp
    assert 'datos_enajenante' in comp
    assert 'datos_adquiriente_cop_sc' in comp['datos_adquiriente']
    assert len(comp['datos_adquiriente']['datos_adquiriente_cop_sc']) == 1

def test_invalid_date_raises_error():
    model = ComplementoNotariosModel(
        fecha_inst_notarial="invalid-date",
        desc_inmuebles=[],
        datos_enajenantes=[],
        datos_adquirientes=[]
    )
    with pytest.raises(ValueError):
        comp_mod.create_complemento_notarios(model)

def test_invalid_coproperty_percentages():
    model = ComplementoNotariosModel(
        fecha_inst_notarial="2023-10-15",
        desc_inmuebles=[],
        datos_enajenantes=[],
        datos_adquirientes=[
            DatosAdquiriente(
                copro_soc_conyugal_e="Si",
                nombre="A B",
                rfc="AAA",
                curp="BBB",
                porcentaje=Decimal("50.00")
            ),
            DatosAdquiriente(
                copro_soc_conyugal_e="Si",
                nombre="C D",
                rfc="CCC",
                curp="DDD",
                porcentaje=Decimal("49.99")
            )
        ]
    )
    with pytest.raises(ValueError, match="Sum of adquiriente coproperty percentages must be exactly 100.00%"):
        comp_mod.create_complemento_notarios(model)
