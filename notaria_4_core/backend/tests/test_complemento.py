from datetime import date, timedelta
from decimal import Decimal
import pytest
from notaria_4_core.backend.lib.api_models import (
    ComplementoNotariosModel, DatosNotarioModel, DatosOperacionModel,
    DescInmuebleModel, DatosAdquirienteModel, DatosEnajenanteModel
)
from notaria_4_core.backend.lib.complement_notarios import create_complemento_notarios, split_name

# Helper to create valid base data
def get_base_data():
    return ComplementoNotariosModel(
        datos_notario=DatosNotarioModel(),
        datos_operacion=DatosOperacionModel(
            num_instrumento_notarial=12345,
            fecha_inst_notarial=date.today(),
            monto_operacion=Decimal("100000.00"),
            subtotal=Decimal("10000.00"),
            iva=Decimal("1600.00")
        ),
        desc_inmuebles=[
            DescInmuebleModel(
                tipo_inmueble="01",
                calle="Av. Mexico",
                no_exterior="100",
                entidad_federativa="06",
                municipio="007",
                pais="MEX",
                codigo_postal="28200"
            )
        ],
        datos_adquirientes=[
            DatosAdquirienteModel(
                nombre="JUAN PEREZ LOPEZ",
                rfc="PELJ800101XYZ",
                curp="PELJ800101HCOLXX00",
                copro_soc_conyugal_e="No"
            )
        ],
        datos_enajenantes=[
            DatosEnajenanteModel(
                nombre="MARIA GONZALEZ RUIZ",
                rfc="GORM850101ABC",
                curp="GORM850101MCOLXX00",
                copro_soc_conyugal_e="No"
            )
        ]
    )

def test_split_name():
    assert split_name("JUAN PEREZ LOPEZ") == ("JUAN", "PEREZ", "LOPEZ")
    assert split_name("MARIA DE LA LUZ GONZALEZ RUIZ") == ("MARIA DE LA LUZ", "GONZALEZ", "RUIZ")
    assert split_name("PEDRO") == ("PEDRO", "", "")
    assert split_name("PEDRO PEREZ") == ("PEDRO", "PEREZ", "")

def test_create_complemento_basic():
    data = get_base_data()
    comp = create_complemento_notarios(data)

    # Check structure (using dict access as satcfdi objects support it)
    assert comp['DatosOperacion']['NumInstrumentoNotarial'] == 12345
    assert comp['DatosNotario']['NumNotaria'] == 4

    # Check Adquirientes
    # satcfdi v4 flattens to singular DatosAdquiriente if only one group
    adq = comp.get('DatosAdquiriente')
    assert adq is not None
    assert adq['CoproSocConyugalE'] == "No"
    un_adq = adq['DatosUnAdquiriente']
    assert un_adq['Nombre'] == "JUAN"
    assert un_adq['ApellidoPaterno'] == "PEREZ"

def test_create_complemento_copropiedad():
    data = get_base_data()
    # 2 Adquirientes, 50% each
    data.datos_adquirientes = [
        DatosAdquirienteModel(
            nombre="JUAN PEREZ",
            rfc="RFC1",
            curp="CURP1",
            porcentaje=Decimal("50.00"),
            copro_soc_conyugal_e="Si"
        ),
        DatosAdquirienteModel(
            nombre="ANA LOPEZ",
            rfc="RFC2",
            curp="CURP2",
            porcentaje=Decimal("50.00"),
            copro_soc_conyugal_e="Si"
        )
    ]

    comp = create_complemento_notarios(data)
    adq = comp.get('DatosAdquiriente')
    assert adq is not None
    assert adq['CoproSocConyugalE'] == "Si"

    cop_list = adq['DatosAdquirientesCopSC']
    assert len(cop_list) == 2
    assert cop_list[0]['Porcentaje'] == Decimal("50.00")

def test_future_date_fail():
    data = get_base_data()
    data.datos_operacion.fecha_inst_notarial = date.today() + timedelta(days=1)

    with pytest.raises(ValueError, match="future"):
        create_complemento_notarios(data)

def test_copropiedad_sum_fail():
    data = get_base_data()
    data.datos_adquirientes = [
        DatosAdquirienteModel(
            nombre="A", rfc="R1", curp="C1", porcentaje=Decimal("33.33"), copro_soc_conyugal_e="Si"
        ),
        DatosAdquirienteModel(
            nombre="B", rfc="R2", curp="C2", porcentaje=Decimal("33.33"), copro_soc_conyugal_e="Si"
        ),
        DatosAdquirienteModel(
            nombre="C", rfc="R3", curp="C3", porcentaje=Decimal("33.33"), copro_soc_conyugal_e="Si"
        )
    ]
    # Sum is 99.99 != 100.00
    with pytest.raises(ValueError, match="Sum of percentages"):
        create_complemento_notarios(data)
