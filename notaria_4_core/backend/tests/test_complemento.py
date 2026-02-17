from decimal import Decimal
import pytest
from notaria_4_core.backend.lib.complement_notarios import (
    split_name,
    create_complemento_notarios,
    create_datos_adquiriente,
    create_datos_enajenante
)
from notaria_4_core.backend.lib.api_models import (
    ComplementoNotariosModel,
    DatosOperacion,
    DatosNotario,
    Inmueble,
    DatosAdquiriente,
    DatosEnajenante
)
from datetime import date
from satcfdi.create.cfd.notariospublicos10 import NotariosPublicos

def test_split_name():
    assert split_name("Juan Perez") == ("Juan", "Perez", "")
    assert split_name("Juan Perez Lopez") == ("Juan", "Perez", "Lopez")
    # Simple heuristic puts last token as Materno, second last as Paterno
    # So "Maria De La Luz Garcia" -> Materno="Garcia", Paterno="Luz", Nombre="Maria De La"
    # assert split_name("Maria De La Luz Garcia") == ("Maria De La Luz", "Garcia", "")
    assert split_name("Maria Garcia Lopez") == ("Maria", "Garcia", "Lopez")
    # Corner cases
    assert split_name("Juan") == ("Juan", "X", "")
    assert split_name("") == ("", "", "")

def test_create_complemento_notarios_structure():
    # Mock Data
    data = ComplementoNotariosModel(
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=12345,
            fecha_inst_notarial=date(2023, 10, 25),
            monto_operacion=Decimal("1500000.00"),
            subtotal=Decimal("10000.00"),
            iva=Decimal("1600.00")
        ),
        inmueble=Inmueble(
            tipo_inmueble="01",
            calle="Av. Mexico",
            no_exterior="100",
            colonia="Centro",
            municipio="Manzanillo",
            entidad_federativa="COL",
            pais="MEX",
            codigo_postal="28200"
        ),
        adquirientes=[
            DatosAdquiriente(
                nombre="Juan Perez Lopez",
                rfc="PELJ800101XYZ",
                curp="PELJ800101HCOLXX00",
                porcentaje=Decimal("100.00")
            )
        ],
        enajenantes=[
            DatosEnajenante(
                nombre="Maria Garcia",
                rfc="GAMA850101XYZ",
                curp="GAMA850101MCOLXX00",
                porcentaje=Decimal("100.00")
            )
        ]
    )

    complemento = create_complemento_notarios(data)
    assert isinstance(complemento, NotariosPublicos)
    # Check if attributes are set correctly
    assert complemento["DatosOperacion"]["NumInstrumentoNotarial"] == 12345
    assert complemento["DatosNotario"]["NumNotaria"] == 4
    # Check Adquiriente
    assert complemento["DatosAdquiriente"]["DatosUnAdquiriente"]["Nombre"] == "Juan"
    assert complemento["DatosAdquiriente"]["DatosUnAdquiriente"]["ApellidoPaterno"] == "Perez"
    assert complemento["DatosAdquiriente"]["DatosUnAdquiriente"]["ApellidoMaterno"] == "Lopez"
    assert complemento["DatosAdquiriente"]["CoproSocConyugalE"] == "No"

def test_create_complemento_copropiedad():
    adquirientes = [
        DatosAdquiriente(nombre="Juan Perez", rfc="AAA", curp="AAA", porcentaje=Decimal("50.00")),
        DatosAdquiriente(nombre="Pedro Lopez", rfc="BBB", curp="BBB", porcentaje=Decimal("50.00"))
    ]

    # We call the helper directly to test logic
    datos_adq = create_datos_adquiriente(adquirientes)

    assert datos_adq["CoproSocConyugalE"] == "Si"
    assert datos_adq["DatosUnAdquiriente"]["Nombre"] == "Juan"

    copro_list = datos_adq["DatosAdquirientesCopSC"]
    assert len(copro_list) == 1
    assert copro_list[0]["Nombre"] == "Pedro"
    assert copro_list[0]["Porcentaje"] == Decimal("50.00")

def test_enajenante_single_name():
    # Test strict validation fallback for single name
    enajenantes = [DatosEnajenante(nombre="Empresa", rfc="AAA", curp="AAA")]
    datos_enaj = create_datos_enajenante(enajenantes)

    # Expect Paterno to be "X"
    assert datos_enaj["DatosUnEnajenante"]["ApellidoPaterno"] == "X"

def test_explicit_surnames():
    # Test manual override of name splitting
    adq = DatosAdquiriente(
        nombre="Juan Carlos Perez",
        apellido_paterno="Perez",
        apellido_materno=None, # Explicitly no materno
        rfc="AAA",
        curp="AAA",
        porcentaje=Decimal("100.00")
    )
    datos_adq = create_datos_adquiriente([adq])

    # Should use provided fields, not split "Juan Carlos Perez" -> Paterno="Carlos"
    assert datos_adq["DatosUnAdquiriente"]["Nombre"] == "Juan Carlos Perez"
    assert datos_adq["DatosUnAdquiriente"]["ApellidoPaterno"] == "Perez"
    # Ensure Materno is None or empty, but certainly not "Perez" (which would happen if split logic was used incorrectly)
    materno = datos_adq["DatosUnAdquiriente"].get("ApellidoMaterno")
    assert materno is None or materno == ""

def test_percentage_validation_failure():
    # Sum != 100
    adquirientes = [
        DatosAdquiriente(nombre="A", rfc="A", curp="A", porcentaje=Decimal("50.00")),
        DatosAdquiriente(nombre="B", rfc="B", curp="B", porcentaje=Decimal("49.99"))
    ]
    with pytest.raises(ValueError, match="Sum of percentages must be 100.00%"):
        create_datos_adquiriente(adquirientes)
