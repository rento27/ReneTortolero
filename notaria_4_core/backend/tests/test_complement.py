from datetime import datetime, timedelta
from decimal import Decimal
import pytest

from notaria_4_core.backend.lib.api_models import (
    ComplementoNotariosModel, DatosOperacion, DatosNotario,
    DescInmueble, DatosAdquiriente, DatosEnajenante
)
from notaria_4_core.backend.lib.complement_notarios import create_complemento_notarios, split_name
from notaria_4_core.backend.lib.fiscal_engine import sanitize_name

def test_split_name():
    assert split_name("JUAN PEREZ GOMEZ") == ("JUAN", "PEREZ", "GOMEZ")
    assert split_name("MARIA DE LA LUZ PEREZ GOMEZ") == ("MARIA DE LA LUZ", "PEREZ", "GOMEZ")
    assert split_name("JUAN PEREZ") == ("JUAN", "PEREZ", "")
    assert split_name("INMOBILIARIA") == ("INMOBILIARIA", "", "")

def test_create_complemento_notarios_success():
    data = ComplementoNotariosModel(
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=123,
            fecha_inst_notarial="2023-01-01T12:00:00",
            monto_operacion=Decimal("100000.00"),
            subtotal=Decimal("100000.00"),
            iva=Decimal("16000.00")
        ),
        datos_notario=DatosNotario(),
        desc_inmuebles=[
            DescInmueble(
                tipo_inmueble="01", calle="CALLE 1", municipio="001",
                estado="06", codigo_postal="28200"
            )
        ],
        datos_adquirientes=[
            DatosAdquiriente(
                nombre="JUAN PEREZ GOMEZ", rfc="XAXX010101000", curp="123456789012345678",
                copro_soc_conyugal_e="No"
            )
        ],
        datos_enajenantes=[
            DatosEnajenante(
                nombre="EMPRESA S.A. DE C.V.", rfc="EMP123456789", curp="EMP123456789012345",
                copro_soc_conyugal_e="No"
            )
        ]
    )

    comp = create_complemento_notarios(data)
    assert comp is not None
    # Assuming comp exposes its properties as a dict
    assert comp['DatosOperacion']['NumInstrumentoNotarial'] == 123
    # Check that sanitize_name worked on Enajenante
    enajenante = comp['DatosEnajenante']['DatosUnEnajenante']
    assert enajenante['Nombre'] == "EMPRESA"

def test_create_complemento_notarios_future_date():
    future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
    data = ComplementoNotariosModel(
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=123,
            fecha_inst_notarial=future_date,
            monto_operacion=Decimal("100000.00"),
            subtotal=Decimal("100000.00"),
            iva=Decimal("16000.00")
        ),
        datos_notario=DatosNotario(),
        desc_inmuebles=[
            DescInmueble(
                tipo_inmueble="01", calle="CALLE 1", municipio="001",
                estado="06", codigo_postal="28200"
            )
        ],
        datos_adquirientes=[
            DatosAdquiriente(
                nombre="JUAN PEREZ GOMEZ", rfc="XAXX010101000", curp="123456789012345678",
                copro_soc_conyugal_e="No"
            )
        ],
        datos_enajenantes=[
            DatosEnajenante(
                nombre="EMPRESA S.A. DE C.V.", rfc="EMP123456789", curp="EMP123456789012345",
                copro_soc_conyugal_e="No"
            )
        ]
    )
    with pytest.raises(ValueError, match="cannot be in the future"):
        create_complemento_notarios(data)

def test_create_complemento_notarios_copro_invalid():
    data = ComplementoNotariosModel(
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=123,
            fecha_inst_notarial="2023-01-01T12:00:00",
            monto_operacion=Decimal("100000.00"),
            subtotal=Decimal("100000.00"),
            iva=Decimal("16000.00")
        ),
        datos_notario=DatosNotario(),
        desc_inmuebles=[
            DescInmueble(
                tipo_inmueble="01", calle="CALLE 1", municipio="001",
                estado="06", codigo_postal="28200"
            )
        ],
        datos_adquirientes=[
            DatosAdquiriente(
                nombre="JUAN PEREZ", rfc="XAXX010101000", curp="123456789012345678",
                copro_soc_conyugal_e="Si", porcentaje=Decimal("50.00")
            ),
            DatosAdquiriente(
                nombre="MARIA GOMEZ", rfc="XAXX010101000", curp="123456789012345678",
                copro_soc_conyugal_e="Si", porcentaje=Decimal("49.99")
            )
        ],
        datos_enajenantes=[
            DatosEnajenante(
                nombre="EMPRESA", rfc="EMP123456789", curp="EMP123456789012345",
                copro_soc_conyugal_e="No"
            )
        ]
    )
    with pytest.raises(ValueError, match="Sum of percentages in Adquirientes coproperty must be 100.00%"):
        create_complemento_notarios(data)

def test_create_complemento_notarios_copro_success():
    data = ComplementoNotariosModel(
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=123,
            fecha_inst_notarial="2023-01-01T12:00:00",
            monto_operacion=Decimal("100000.00"),
            subtotal=Decimal("100000.00"),
            iva=Decimal("16000.00")
        ),
        datos_notario=DatosNotario(),
        desc_inmuebles=[
            DescInmueble(
                tipo_inmueble="01", calle="CALLE 1", municipio="001",
                estado="06", codigo_postal="28200"
            )
        ],
        datos_adquirientes=[
            DatosAdquiriente(
                nombre="JUAN PEREZ", rfc="XAXX010101000", curp="123456789012345678",
                copro_soc_conyugal_e="Si", porcentaje=Decimal("50.00")
            ),
            DatosAdquiriente(
                nombre="MARIA GOMEZ", rfc="XAXX010101000", curp="123456789012345678",
                copro_soc_conyugal_e="Si", porcentaje=Decimal("50.00")
            )
        ],
        datos_enajenantes=[
            DatosEnajenante(
                nombre="EMPRESA", rfc="EMP123456789", curp="EMP123456789012345",
                copro_soc_conyugal_e="No"
            )
        ]
    )

    comp = create_complemento_notarios(data)
    assert comp is not None
    assert comp['DatosAdquiriente']['CoproSocConyugalE'] == "Si"
    assert len(comp['DatosAdquiriente']['DatosAdquirientesCopSC']) == 2
