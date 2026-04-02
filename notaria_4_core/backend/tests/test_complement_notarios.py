import pytest
from decimal import Decimal
from notaria_4_core.backend.lib.complement_notarios import create_complemento_notarios
from notaria_4_core.backend.lib.api_models import ComplementoNotariosModel, DatosAdquiriente, DatosEnajenante, DescInmueble, DatosNotario

def test_create_complemento_notarios_success():
    model = ComplementoNotariosModel(
        version="1.0",
        fecha_inst_notarial="2023-10-01",
        desc_inmuebles=[
            DescInmueble(tipo_inmueble="01", calle="Main St", municipio="Manzanillo", estado="COL", pais="MEX", codigo_postal="28200")
        ],
        datos_enajenantes=[
            DatosEnajenante(copro_soc_conyugal_e="No", nombre="John Doe", rfc="DOEJ900101XYZ", curp="DOEJ900101XYZ12345")
        ],
        datos_adquirientes=[
            DatosAdquiriente(copro_soc_conyugal_e="Si", nombre="Jane Doe", rfc="DOEJ900101ABC", curp="DOEJ900101ABC12345", porcentaje=Decimal("50.00")),
            DatosAdquiriente(copro_soc_conyugal_e="Si", nombre="Jim Doe", rfc="DOEJ900101DEF", curp="DOEJ900101DEF12345", porcentaje=Decimal("50.00"))
        ]
    )
    result = create_complemento_notarios(model)
    assert result is not None
    assert result['DatosAdquiriente']['DatosAdquirientesCopSC'][0]['Porcentaje'] == Decimal("50.00")

def test_create_complemento_notarios_coproperty_invalid_percentage():
    model = ComplementoNotariosModel(
        version="1.0",
        fecha_inst_notarial="2023-10-01",
        desc_inmuebles=[
            DescInmueble(tipo_inmueble="01", calle="Main St", municipio="Manzanillo", estado="COL", pais="MEX", codigo_postal="28200")
        ],
        datos_enajenantes=[
            DatosEnajenante(copro_soc_conyugal_e="No", nombre="John Doe", rfc="DOEJ900101XYZ", curp="DOEJ900101XYZ12345")
        ],
        datos_adquirientes=[
            DatosAdquiriente(copro_soc_conyugal_e="Si", nombre="Jane Doe", rfc="DOEJ900101ABC", curp="DOEJ900101ABC12345", porcentaje=Decimal("50.00")),
            DatosAdquiriente(copro_soc_conyugal_e="Si", nombre="Jim Doe", rfc="DOEJ900101DEF", curp="DOEJ900101DEF12345", porcentaje=Decimal("49.99"))
        ]
    )
    with pytest.raises(ValueError, match="Sum of adquiriente coproperty percentages must be exactly 100.00%"):
        create_complemento_notarios(model)

def test_create_complemento_notarios_single_buyer_seller():
    model = ComplementoNotariosModel(
        version="1.0",
        fecha_inst_notarial="2023-10-01",
        desc_inmuebles=[
            DescInmueble(tipo_inmueble="01", calle="Main St", municipio="Manzanillo", estado="COL", pais="MEX", codigo_postal="28200")
        ],
        datos_enajenantes=[
            DatosEnajenante(copro_soc_conyugal_e="No", nombre="John Doe", rfc="DOEJ900101XYZ", curp="DOEJ900101XYZ12345")
        ],
        datos_adquirientes=[
            DatosAdquiriente(copro_soc_conyugal_e="No", nombre="Jane Doe", rfc="DOEJ900101ABC", curp="DOEJ900101ABC12345")
        ]
    )
    result = create_complemento_notarios(model)
    assert result is not None
    assert result['DatosAdquiriente']['CoproSocConyugalE'] == "No"
    assert result['DatosEnajenante']['CoproSocConyugalE'] == "No"
