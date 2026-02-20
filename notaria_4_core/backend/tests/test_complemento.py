import pytest
from datetime import date, timedelta
from decimal import Decimal
from lib.complement_notarios import create_complemento_notarios, split_name
from lib.api_models import (
    ComplementoNotariosModel, DatosNotario, DatosOperacion,
    DescInmueble, DatosAdquiriente, DatosEnajenante
)

def test_split_name():
    # Simple 3 parts
    res = split_name("JUAN PEREZ LOPEZ")
    assert res["nombre"] == "JUAN"
    assert res["apellido_paterno"] == "PEREZ"
    assert res["apellido_materno"] == "LOPEZ"

    # 2 parts
    res = split_name("PEDRO LOPEZ")
    assert res["nombre"] == "PEDRO"
    assert res["apellido_paterno"] == "LOPEZ"

    # 1 part
    res = split_name("PEDRO")
    assert res["nombre"] == "PEDRO"

def test_complemento_valid():
    model = ComplementoNotariosModel(
        datos_notario=DatosNotario(curp="ABCD12345678901234"),
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=123,
            fecha_inst_notarial=date.today(),
            monto_operacion=Decimal("1000000"),
            subtotal=Decimal("10000"),
            iva=Decimal("1600")
        ),
        desc_inmuebles=[DescInmueble(
            tipo_inmueble="01", calle="AVENIDA", municipio="MANZANILLO",
            estado="COL", pais="MEX", codigo_postal="28200"
        )],
        datos_adquirientes=[DatosAdquiriente(
            nombre="CLIENTE UNO", porcentaje=Decimal("100.00"), copro_soc_conyugal_e="No", rfc="XAXX010101000"
        )],
        datos_enajenantes=[DatosEnajenante(
            nombre="VENDEDOR UNO", porcentaje=Decimal("100.00"), copro_soc_conyugal_e="No", rfc="XAXX010101000"
        )]
    )

    comp = create_complemento_notarios(model)
    # Check if satcfdi object is created (it's a dict-like wrapper)
    # Note: satcfdi usually converts keys to PascalCase for XML
    assert comp['DatosNotario']['NumNotaria'] == 4
    # Debug print keys if failure
    # print(comp.keys())
    # The XSD element is DatosAdquirientes, but satcfdi might use singular based on class if not careful.
    # However, create_complemento_notarios returns NotariosPublicos object.
    # Let's check if it's 'DatosAdquiriente' (singular)

    # Try singular or look for the correct key
    adquirientes = comp.get('DatosAdquirientes') or comp.get('DatosAdquiriente')
    assert adquirientes is not None
    # Because 'CLIENTE UNO' is split into Name='CLIENTE' and PatName='UNO' by split_name logic
    assert adquirientes['DatosUnAdquiriente']['Nombre'] == "CLIENTE"
    assert adquirientes['DatosUnAdquiriente']['ApellidoPaterno'] == "UNO"

def test_future_date_error():
    future = date.today() + timedelta(days=1)
    model = ComplementoNotariosModel(
        datos_notario=DatosNotario(curp="ABCD12345678901234"),
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=123,
            fecha_inst_notarial=future,
            monto_operacion=Decimal("1000"),
            subtotal=Decimal("100"),
            iva=Decimal("16")
        ),
        desc_inmuebles=[],
        datos_adquirientes=[DatosAdquiriente(nombre="A", porcentaje=Decimal(100))],
        datos_enajenantes=None
    )
    with pytest.raises(ValueError, match="future"):
        create_complemento_notarios(model)

def test_coproperty_sum_error():
    model = ComplementoNotariosModel(
        datos_notario=DatosNotario(curp="ABCD12345678901234"),
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=123,
            fecha_inst_notarial=date.today(),
            monto_operacion=Decimal("1000"),
            subtotal=Decimal("100"),
            iva=Decimal("16")
        ),
        desc_inmuebles=[],
        datos_adquirientes=[
            DatosAdquiriente(nombre="A", porcentaje=Decimal("50.00"), copro_soc_conyugal_e="Si"),
            DatosAdquiriente(nombre="B", porcentaje=Decimal("49.99"), copro_soc_conyugal_e="Si")
        ],
        datos_enajenantes=None
    )
    with pytest.raises(ValueError, match="Sum of percentages"):
        create_complemento_notarios(model)
