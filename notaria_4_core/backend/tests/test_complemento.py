from decimal import Decimal
from datetime import date, timedelta
import pytest
from notaria_4_core.backend.lib.api_models import (
    ComplementoNotariosModel, DatosOperacion, DatosNotario, DescInmueble,
    DatosAdquiriente, DatosUnAdquiriente, DatosAdquirienteCopSC,
    DatosEnajenante, DatosUnEnajenante
)
from notaria_4_core.backend.lib.complement_notarios import create_complemento_notarios, FALLBACK_CURP_NOTARY

@pytest.fixture
def valid_complement_data():
    return ComplementoNotariosModel(
        version="1.0",
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=12345,
            fecha_inst_notarial=date.today(),
            monto_operacion=Decimal("1000000.00"),
            subtotal=Decimal("10000.00"),
            iva=Decimal("1600.00")
        ),
        desc_inmuebles=[
            DescInmueble(
                tipo_inmueble="03",
                calle="Av. Mexico",
                municipio="Manzanillo",
                estado="Colima",
                pais="Mexico",
                codigo_postal="28200"
            )
        ],
        datos_adquiriente=DatosAdquiriente(
            copro_soc_conyugal_e="No",
            datos_un_adquiriente=DatosUnAdquiriente(
                nombre="Juan",
                apellido_paterno="Perez",
                rfc="PEPJ8001019Q8",
                curp="PEPJ800101HCOLXX00"
            )
        ),
        datos_enajenante=DatosEnajenante(
            copro_soc_conyugal_e="No",
            datos_un_enajenante=DatosUnEnajenante(
                nombre="Maria",
                apellido_paterno="Lopez",
                rfc="LOMM8001019Q8",
                curp="LOMM800101HCOLXX00"
            )
        )
    )

def test_create_complemento_success(valid_complement_data):
    comp = create_complemento_notarios(valid_complement_data)
    assert comp is not None
    # Access satcfdi object fields (it behaves like a dict)
    assert comp['DatosOperacion']['NumInstrumentoNotarial'] == 12345
    assert comp['DatosNotario']['CURP'] == FALLBACK_CURP_NOTARY # Default used

def test_create_complemento_future_date(valid_complement_data):
    valid_complement_data.datos_operacion.fecha_inst_notarial = date.today() + timedelta(days=1)
    with pytest.raises(ValueError, match="FechaInstNotarial cannot be in the future"):
        create_complemento_notarios(valid_complement_data)

def test_create_complemento_copropiedad_valid(valid_complement_data):
    # Modify for coproperty
    valid_complement_data.datos_adquiriente.copro_soc_conyugal_e = "Si"
    valid_complement_data.datos_adquiriente.datos_un_adquiriente = None
    valid_complement_data.datos_adquiriente.datos_adquirientes_cop_sc = [
        DatosAdquirienteCopSC(
            nombre="Juan",
            rfc="XAXX010101000",
            porcentaje=Decimal("50.00")
        ),
        DatosAdquirienteCopSC(
            nombre="Pedro",
            rfc="XBXX010101000",
            porcentaje=Decimal("50.00")
        )
    ]
    comp = create_complemento_notarios(valid_complement_data)
    assert len(comp['DatosAdquiriente']['DatosAdquirientesCopSC']) == 2

def test_create_complemento_copropiedad_invalid_sum(valid_complement_data):
    valid_complement_data.datos_adquiriente.copro_soc_conyugal_e = "Si"
    valid_complement_data.datos_adquiriente.datos_un_adquiriente = None
    valid_complement_data.datos_adquiriente.datos_adquirientes_cop_sc = [
        DatosAdquirienteCopSC(
            nombre="Juan",
            rfc="XAXX010101000",
            porcentaje=Decimal("50.00")
        ),
        DatosAdquirienteCopSC(
            nombre="Pedro",
            rfc="XBXX010101000",
            porcentaje=Decimal("49.99")
        )
    ]
    with pytest.raises(ValueError, match="Sum of percentages for Adquirientes must be 100.00%"):
        create_complemento_notarios(valid_complement_data)

def test_explicit_notary_curp(valid_complement_data):
    valid_complement_data.datos_notario = DatosNotario(curp="AAAA000000AAAAAA00")
    comp = create_complemento_notarios(valid_complement_data)
    assert comp['DatosNotario']['CURP'] == "AAAA000000AAAAAA00"
