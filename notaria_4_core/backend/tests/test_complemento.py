import pytest
from unittest.mock import MagicMock, patch
import sys
from datetime import date, timedelta
from decimal import Decimal

# Mock satcfdi before importing lib.complement_notarios
sys.modules['satcfdi.create.cfd.notariospublicos10'] = MagicMock()

from notaria_4_core.backend.lib.api_models import ComplementoNotariosModel, DatosOperacion, DescInmueble, DatosAdquiriente, DatosEnajenante
from notaria_4_core.backend.lib.complement_notarios import split_name, validate_percentages, create_complemento_notarios

def test_split_name():
    assert split_name("Juan Perez Lopez") == ("Perez", "Lopez")
    # Heuristic limit: "Maria De La Cruz" might split weirdly depending on spaces, but let's test basic 3 parts
    assert split_name("Maria Cruz") == ("Cruz", "")
    assert split_name("Pedro") == ("", "")

def test_validate_percentages():
    validate_percentages([Decimal("50.00"), Decimal("50.00")])
    with pytest.raises(ValueError):
        validate_percentages([Decimal("50.00"), Decimal("49.99")])

def test_create_complemento_single_adquiriente():
    data = ComplementoNotariosModel(
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=123,
            fecha_inst_notarial=date.today(),
            monto_operacion=Decimal("1000.00"),
            subtotal=Decimal("1000.00"),
            iva=Decimal("160.00")
        ),
        desc_inmuebles=[DescInmueble(
            tipo_inmueble="01", calle="Calle 1", municipio="Manzanillo", estado="COL", pais="MEX", codigo_postal="28200"
        )],
        datos_enajenantes=[DatosEnajenante(nombre="Vendedor", rfc="XAXX010101000", curp="XAXX010101HXXXXX00")],
        datos_adquirientes=[DatosAdquiriente(nombre="Juan Comprador", rfc="XAXX010101000", curp="XAXX010101HXXXXX00")]
    )

    with patch('notaria_4_core.backend.lib.complement_notarios.NotariosPublicos') as MockNotarios:
        create_complemento_notarios(data)

        args, kwargs = MockNotarios.call_args
        assert kwargs['datos_adquirientes']['CoproSocConyugalE'] == 'No'
        assert 'DatosUnAdquiriente' in kwargs['datos_adquirientes']
        assert kwargs['datos_adquirientes']['DatosUnAdquiriente']['Nombre'] == 'Juan Comprador'
        # Check automatic name splitting if not provided
        assert kwargs['datos_adquirientes']['DatosUnAdquiriente']['ApellidoPaterno'] == 'Comprador'

def test_create_complemento_copropiedad():
    data = ComplementoNotariosModel(
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=123,
            fecha_inst_notarial=date.today(),
            monto_operacion=Decimal("1000.00"),
            subtotal=Decimal("1000.00"),
            iva=Decimal("160.00")
        ),
        desc_inmuebles=[DescInmueble(
            tipo_inmueble="01", calle="Calle 1", municipio="Manzanillo", estado="COL", pais="MEX", codigo_postal="28200"
        )],
        datos_enajenantes=[DatosEnajenante(nombre="Vendedor", rfc="XAXX010101000", curp="XAXX010101HXXXXX00")],
        datos_adquirientes=[
            DatosAdquiriente(nombre="Comp1", rfc="XAXX010101000", curp="XAXX010101HXXXXX00", porcentaje=Decimal("50.00"), copro_soc_conyugal_e="Si"),
            DatosAdquiriente(nombre="Comp2", rfc="XAXX010101000", curp="XAXX010101HXXXXX00", porcentaje=Decimal("50.00"), copro_soc_conyugal_e="Si")
        ]
    )

    with patch('notaria_4_core.backend.lib.complement_notarios.NotariosPublicos') as MockNotarios:
        create_complemento_notarios(data)

        args, kwargs = MockNotarios.call_args
        assert kwargs['datos_adquirientes']['CoproSocConyugalE'] == 'Si'
        assert 'DatosAdquirientesCopSC' in kwargs['datos_adquirientes']
        assert len(kwargs['datos_adquirientes']['DatosAdquirientesCopSC']) == 2

def test_future_date_validation():
    future = date.today() + timedelta(days=1)
    data = ComplementoNotariosModel(
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=123,
            fecha_inst_notarial=future,
            monto_operacion=Decimal("1000.00"),
            subtotal=Decimal("1000.00"),
            iva=Decimal("160.00")
        ),
        desc_inmuebles=[],
        datos_enajenantes=[],
        datos_adquirientes=[]
    )
    with pytest.raises(ValueError, match="future"):
        create_complemento_notarios(data)
