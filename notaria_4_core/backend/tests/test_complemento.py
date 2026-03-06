import pytest
from decimal import Decimal
from datetime import date, timedelta
from notaria_4_core.backend.lib.api_models import ComplementoNotariosModel, DatosOperacion, DatosAdquiriente, DatosEnajenante, DatosInmueble
from notaria_4_core.backend.lib.complement_notarios import create_complemento_notarios, split_name

def test_split_name():
    assert split_name("Pedro") == ('', '')
    assert split_name("Pedro Perez") == ('Perez', '')
    assert split_name("Pedro Perez Lopez") == ('Perez', 'Lopez')
    assert split_name("Juan Jose Perez Lopez") == ('Perez', 'Lopez')

def test_create_complemento_future_date():
    op = DatosOperacion(
        num_instrumento_notarial=123,
        fecha_inst_notarial=date.today() + timedelta(days=1),
        monto_operacion=Decimal("1000"),
        subtotal=Decimal("1000"),
        iva=Decimal("160")
    )
    comp = ComplementoNotariosModel(
        datos_operacion=op,
        datos_enajenante=[DatosEnajenante(nombre="Test", rfc="TEST", curp="TEST", copro_soc_conyugal_e="No")],
        datos_adquiriente=[DatosAdquiriente(nombre="Test", rfc="TEST", curp="TEST", copro_soc_conyugal_e="No")],
        desc_inmuebles=[]
    )
    with pytest.raises(ValueError, match="future"):
        create_complemento_notarios(comp)

def test_create_complemento_copro_percentage():
    op = DatosOperacion(
        num_instrumento_notarial=123,
        fecha_inst_notarial=date.today(),
        monto_operacion=Decimal("1000"),
        subtotal=Decimal("1000"),
        iva=Decimal("160")
    )
    comp = ComplementoNotariosModel(
        datos_operacion=op,
        datos_enajenante=[DatosEnajenante(nombre="Test", rfc="TEST", curp="TEST", copro_soc_conyugal_e="No")],
        datos_adquiriente=[
            DatosAdquiriente(nombre="Test 1", rfc="TEST1", curp="TEST1", copro_soc_conyugal_e="Si", porcentaje=Decimal("50.00")),
            DatosAdquiriente(nombre="Test 2", rfc="TEST2", curp="TEST2", copro_soc_conyugal_e="Si", porcentaje=Decimal("49.00"))
        ],
        desc_inmuebles=[]
    )
    with pytest.raises(ValueError, match="100.00"):
        create_complemento_notarios(comp)

def test_create_complemento_success():
    op = DatosOperacion(
        num_instrumento_notarial=123,
        fecha_inst_notarial=date.today(),
        monto_operacion=Decimal("1000"),
        subtotal=Decimal("1000"),
        iva=Decimal("160")
    )
    inm = DatosInmueble(
        tipo_inmueble="01",
        calle="Test Calle",
        municipio="001",
        estado="06",
        pais="MEX",
        codigo_postal="28200"
    )
    comp = ComplementoNotariosModel(
        datos_operacion=op,
        datos_enajenante=[DatosEnajenante(nombre="Pedro Perez Lopez", rfc="TEST", curp="TEST", copro_soc_conyugal_e="No")],
        datos_adquiriente=[
            DatosAdquiriente(nombre="Test 1", rfc="TEST1", curp="TEST1", copro_soc_conyugal_e="Si", porcentaje=Decimal("50.00")),
            DatosAdquiriente(nombre="Test 2", rfc="TEST2", curp="TEST2", copro_soc_conyugal_e="Si", porcentaje=Decimal("50.00"))
        ],
        desc_inmuebles=[inm]
    )

    np = create_complemento_notarios(comp)
    assert np['DatosNotario']['CURP'] == "TOSR520601HOCMXA00"
    assert np['DatosNotario']['NumNotaria'] == 4

    # Verify split name on enajenante
    un_e = np['DatosEnajenante']['DatosUnEnajenante']
    assert un_e['Nombre'] == "Pedro Perez Lopez"
    assert un_e['ApellidoPaterno'] == "Perez"
    assert un_e['ApellidoMaterno'] == "Lopez"

    # Verify copro on adquiriente
    cops = np['DatosAdquiriente']['DatosAdquirientesCopSC']
    assert len(cops) == 2

    # Verify Inmueble
    assert np['DescInmuebles'][0]['Calle'] == "Test Calle"
