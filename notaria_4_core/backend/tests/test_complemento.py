import pytest
from datetime import date, timedelta
from decimal import Decimal
from lib.api_models import ComplementoNotariosModel, DatosOperacion, DescInmueble, DatosAdquiriente
from lib.complement_notarios import create_complemento_notarios

try:
    from satcfdi.create.cfd.notariospublicos10 import NotariosPublicos
except ImportError:
    NotariosPublicos = None

@pytest.mark.skipif(NotariosPublicos is None, reason="satcfdi not installed")
def test_create_complemento_basic():
    data = ComplementoNotariosModel(
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=12345,
            fecha_inst_notarial=date.today(),
            monto_operacion=Decimal("100000.00"),
            subtotal=Decimal("10000.00"),
            iva=Decimal("1600.00")
        ),
        desc_inmuebles=[
            DescInmueble(
                tipo_inmueble="01",
                calle="Av. Mexico",
                municipio="Manzanillo",
                estado="Colima",
                pais="MEX",
                codigo_postal="28200"
            )
        ],
        datos_adquirientes=[
            DatosAdquiriente(
                nombre="JUAN PEREZ",
                rfc="PEJU8001019Q8",
                copro_soc_conyugal_e="No"
            )
        ]
    )

    comp = create_complemento_notarios(data)
    assert comp is not None
    # Check that defaults were applied
    assert comp["DatosNotario"]["NumNotaria"] == 4

@pytest.mark.skipif(NotariosPublicos is None, reason="satcfdi not installed")
def test_create_complemento_future_date():
    future_date = date.today() + timedelta(days=1)
    data = ComplementoNotariosModel(
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=12345,
            fecha_inst_notarial=future_date,
            monto_operacion=Decimal("100000.00"),
            subtotal=Decimal("10000.00"),
            iva=Decimal("1600.00")
        ),
        desc_inmuebles=[],
        datos_adquirientes=[]
    )

    with pytest.raises(ValueError, match="future"):
        create_complemento_notarios(data)

@pytest.mark.skipif(NotariosPublicos is None, reason="satcfdi not installed")
def test_create_complemento_coproperty_validation():
    data = ComplementoNotariosModel(
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=12345,
            fecha_inst_notarial=date.today(),
            monto_operacion=Decimal("100000.00"),
            subtotal=Decimal("10000.00"),
            iva=Decimal("1600.00")
        ),
        desc_inmuebles=[],
        datos_adquirientes=[
            DatosAdquiriente(nombre="A", copro_soc_conyugal_e="Si", porcentaje=Decimal("50.00")),
            DatosAdquiriente(nombre="B", copro_soc_conyugal_e="Si", porcentaje=Decimal("49.99"))
        ]
    )

    with pytest.raises(ValueError, match="100.00"):
        create_complemento_notarios(data)
