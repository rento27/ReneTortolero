import pytest
from decimal import Decimal
from datetime import date, timedelta
from notaria_4_core.backend.lib.api_models import (
    ComplementoNotariosModel, DatosNotarioModel, DatosOperacionModel,
    DescInmuebleModel, DatosAdquirienteModel, DatosEnajenanteModel
)
from notaria_4_core.backend.lib.complement_notarios import create_complemento_notarios

def test_create_complemento_success():
    data = ComplementoNotariosModel(
        datos_operacion=DatosOperacionModel(
            num_instrumento_notarial=123,
            fecha_inst_notarial=date.today(),
            monto_operacion=Decimal("1000000.00"),
            subtotal=Decimal("10000.00"),
            iva=Decimal("1600.00")
        ),
        inmuebles=[DescInmuebleModel(
            tipo_inmueble="01",
            calle="Calle Falsa",
            no_exterior="123",
            municipio="Manzanillo",
            estado="Colima",
            codigo_postal="28200"
        )],
        adquirientes=[DatosAdquirienteModel(
            nombre="Juan",
            apellido_paterno="Perez",
            rfc="PEPJ800101XXX",
            copro_soc_conyugal_e="No"
        )],
        enajenantes=[DatosEnajenanteModel(
            nombre="Maria",
            apellido_paterno="Lopez",
            rfc="LOMM800101XXX",
            copro_soc_conyugal_e="No"
        )]
    )

    complemento = create_complemento_notarios(data)
    assert complemento is not None
    # Verify defaults. satcfdi objects allow dict access usually.
    # Note: satcfdi usually capitalizes keys to match XML.
    assert complemento['DatosNotario']['NumNotaria'] == 4

def test_future_date_fails():
    future_date = date.today() + timedelta(days=1)
    data = ComplementoNotariosModel(
        datos_operacion=DatosOperacionModel(
            num_instrumento_notarial=123,
            fecha_inst_notarial=future_date,
            monto_operacion=Decimal("1000.00"),
            subtotal=Decimal("100.00"),
            iva=Decimal("16.00")
        ),
        inmuebles=[],
        adquirientes=[],
        enajenantes=[]
    )
    with pytest.raises(ValueError, match="future"):
        create_complemento_notarios(data)

def test_coproperty_validation_success():
    data = ComplementoNotariosModel(
        datos_operacion=DatosOperacionModel(
            num_instrumento_notarial=123,
            fecha_inst_notarial=date.today(),
            monto_operacion=Decimal("1000.00"),
            subtotal=Decimal("100.00"),
            iva=Decimal("16.00")
        ),
        inmuebles=[],
        adquirientes=[
            DatosAdquirienteModel(nombre="A", rfc="AAA", copro_soc_conyugal_e="Si", porcentaje=Decimal("50.00")),
            DatosAdquirienteModel(nombre="B", rfc="BBB", copro_soc_conyugal_e="Si", porcentaje=Decimal("50.00"))
        ],
        enajenantes=[]
    )
    comp = create_complemento_notarios(data)
    # Check if coproperty structure is created
    # Use attribute access to be safe with satcfdi internal structure naming
    assert comp['DatosAdquiriente']['CoproSocConyugalE'] == 'Si'
    assert len(comp['DatosAdquiriente']['DatosAdquirientesCopSC']) == 2

def test_coproperty_validation_fail_sum():
    data = ComplementoNotariosModel(
        datos_operacion=DatosOperacionModel(
            num_instrumento_notarial=123,
            fecha_inst_notarial=date.today(),
            monto_operacion=Decimal("1000.00"),
            subtotal=Decimal("100.00"),
            iva=Decimal("16.00")
        ),
        inmuebles=[],
        adquirientes=[
            DatosAdquirienteModel(nombre="A", rfc="AAA", copro_soc_conyugal_e="Si", porcentaje=Decimal("33.00")),
            DatosAdquirienteModel(nombre="B", rfc="BBB", copro_soc_conyugal_e="Si", porcentaje=Decimal("33.00"))
        ],
        enajenantes=[]
    )
    with pytest.raises(ValueError, match="100.00%"):
        create_complemento_notarios(data)

def test_singular_validation_fail_multiple():
    # Multiple acquirers but Copro is No
    data = ComplementoNotariosModel(
        datos_operacion=DatosOperacionModel(
            num_instrumento_notarial=123,
            fecha_inst_notarial=date.today(),
            monto_operacion=Decimal("1000.00"),
            subtotal=Decimal("100.00"),
            iva=Decimal("16.00")
        ),
        inmuebles=[],
        adquirientes=[
            DatosAdquirienteModel(nombre="A", rfc="AAA", copro_soc_conyugal_e="No"),
            DatosAdquirienteModel(nombre="B", rfc="BBB", copro_soc_conyugal_e="No")
        ],
        enajenantes=[]
    )
    with pytest.raises(ValueError, match="Multiple acquirers"):
        create_complemento_notarios(data)
