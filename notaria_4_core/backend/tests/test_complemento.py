import pytest
from decimal import Decimal
from datetime import date, timedelta
from lib.api_models import ComplementoNotariosModel, DatosOperacionModel, DescInmuebleModel, DatosAdquirienteModel, DatosNotarioModel
from lib.complement_notarios import create_complemento_notarios

def test_create_complemento_valid():
    # Test a valid case
    data = ComplementoNotariosModel(
        datos_operacion=DatosOperacionModel(
            num_instrumento_notarial=123,
            fecha_inst_notarial=date.today(),
            monto_operacion=Decimal("100000.00"),
            subtotal=Decimal("10000.00"),
            iva=Decimal("1600.00")
        ),
        desc_inmuebles=[
            DescInmuebleModel(
                tipo_inmueble="03",
                calle="Calle 1",
                municipio="Manzanillo",
                estado="Colima",
                pais="MEX",
                codigo_postal="28200"
            )
        ],
        datos_adquirientes=[
            DatosAdquirienteModel(
                nombre="Juan Perez",
                rfc="XAXX010101000",
                copro_soc_conyugal_e="No"
            )
        ]
    )

    comp = create_complemento_notarios(data)
    assert comp is not None
    # Check if datos_notario has default (satcfdi objects usually support item access or attribute access)
    # Checking attribute access or dict access depends on satcfdi version, usually dict-like or XElement.
    # Assuming standard XElement behavior
    assert comp['DatosNotario']['NumNotaria'] == 4

def test_coproperty_sum_validation():
    # Test Sum != 100%
    today = date.today()
    data = ComplementoNotariosModel(
        datos_operacion=DatosOperacionModel(
            num_instrumento_notarial=123,
            fecha_inst_notarial=today,
            monto_operacion=Decimal("100000.00"),
            subtotal=Decimal("10000.00"),
            iva=Decimal("1600.00")
        ),
        desc_inmuebles=[
            DescInmuebleModel(
                tipo_inmueble="03",
                calle="C",
                municipio="M",
                estado="S",
                pais="P",
                codigo_postal="00"
            )
        ],
        datos_adquirientes=[
            DatosAdquirienteModel(
                nombre="A",
                porcentaje=Decimal("50.00"),
                copro_soc_conyugal_e="Si"
            ),
            DatosAdquirienteModel(
                nombre="B",
                porcentaje=Decimal("49.99"),
                copro_soc_conyugal_e="Si"
            )
        ]
    )

    # Sum is 99.99, should fail with strict validation
    with pytest.raises(ValueError, match="Sum of percentages"):
        create_complemento_notarios(data)

def test_future_date_validation():
    # Test future date
    future = date.today() + timedelta(days=1)
    data = ComplementoNotariosModel(
        datos_operacion=DatosOperacionModel(
            num_instrumento_notarial=123,
            fecha_inst_notarial=future,
            monto_operacion=Decimal("100"),
            subtotal=Decimal("10"),
            iva=Decimal("1.6")
        ),
        desc_inmuebles=[],
        datos_adquirientes=[]
    )

    with pytest.raises(ValueError, match="Date .* cannot be in the future"):
        create_complemento_notarios(data)
