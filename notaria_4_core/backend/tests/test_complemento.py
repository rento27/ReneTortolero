from decimal import Decimal
import pytest
from datetime import date
from notaria_4_core.backend.lib.complement_notarios import create_complemento_notarios
from notaria_4_core.backend.lib.api_models import ComplementoNotariosModel, DatosAdquiriente, DatosAdquirienteCopSC, DatosNotario, DatosOperacion, DescInmueble, DatosUnAdquiriente

# Helper to create basic complement model
def create_basic_model(percentages=None):
    desc_inmuebles = [DescInmueble(
        tipo_inmueble="01", calle="Calle 1", municipio="Manzanillo", estado="COL", pais="MEX", codigo_postal="28200"
    )]
    datos_operacion = DatosOperacion(
        num_instrumento_notarial=123, fecha_inst_notarial=date(2023, 10, 27),
        monto_operacion=Decimal("1000000.00"), subtotal=Decimal("10000.00"), iva=Decimal("1600.00")
    )
    datos_notario = DatosNotario(num_notaria=4, entidad_federativa="06", adscripcion="MANZANILLO")

    if percentages:
        # Copropiedad
        copro_list = [
            DatosAdquirienteCopSC(nombre=f"Owner {i}", rfc="XAXX010101000", porcentaje=p)
            for i, p in enumerate(percentages)
        ]
        datos_adquiriente = DatosAdquiriente(
            copro_soc_conyugal_e="Si",
            datos_adquirientes_cop_sc=copro_list
        )
    else:
        # Singular
        datos_adquiriente = DatosAdquiriente(
            copro_soc_conyugal_e="No",
            datos_un_adquiriente=DatosUnAdquiriente(nombre="Owner", rfc="XAXX010101000")
        )

    return ComplementoNotariosModel(
        desc_inmuebles=desc_inmuebles,
        datos_operacion=datos_operacion,
        datos_notario=datos_notario,
        datos_adquiriente=datos_adquiriente
    )

def test_complemento_copropiedad_success():
    model = create_basic_model([Decimal("50.00"), Decimal("50.00")])
    # Should not raise exception
    comp = create_complemento_notarios(model)
    assert comp is not None
    # Verify structure (satcfdi object)
    # Accessing dict-like keys (TitleCase usually in satcfdi dict representation)
    # However, satcfdi objects might use attribute access or dict access.
    # Usually dict access uses the XML tag name which is TitleCase.
    assert comp['DatosAdquiriente']['CoproSocConyugalE'] == "Si"
    assert len(comp['DatosAdquiriente']['DatosAdquirientesCopSC']) == 2

def test_complemento_copropiedad_fail_sum():
    model = create_basic_model([Decimal("50.00"), Decimal("49.99")])
    with pytest.raises(ValueError, match="Sum of percentages must be 100.00%"):
        create_complemento_notarios(model)

def test_complemento_singular():
    model = create_basic_model()
    comp = create_complemento_notarios(model)
    assert comp['DatosAdquiriente']['CoproSocConyugalE'] == "No"
    # Note: satcfdi usually normalizes keys to TitleCase or whatever matches XSD
    assert comp['DatosAdquiriente']['DatosUnAdquiriente']['Nombre'] == "Owner"
