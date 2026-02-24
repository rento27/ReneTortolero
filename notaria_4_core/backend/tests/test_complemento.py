import pytest
from datetime import date
from decimal import Decimal
from notaria_4_core.backend.lib.api_models import ComplementoNotariosModel, DatosNotario, DatosOperacion, DescInmueble, DatosAdquiriente, DatosEnajenante
from notaria_4_core.backend.lib.complement_notarios import create_complemento_notarios

def test_create_complemento_single_adquiriente():
    data = ComplementoNotariosModel(
        datos_notario=DatosNotario(
            curp="ABCD123456HDFRDA01",
            num_notaria=4,
            entidad_federativa="06",
            adscripcion="MANZANILLO COLIMA"
        ),
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=12345,
            fecha_inst_notarial=date(2023, 10, 25),
            monto_operacion=Decimal("1000000.00"),
            subtotal=Decimal("1000.00"),
            iva=Decimal("160.00")
        ),
        desc_inmuebles=[
            DescInmueble(
                tipo_inmueble="01",
                calle="Av. Mexico",
                no_exterior="123",
                colonia="Centro",
                municipio="Manzanillo",
                estado="06",
                pais="MEX",
                codigo_postal="28200"
            )
        ],
        datos_adquirientes=[
            DatosAdquiriente(
                nombre="JUAN PEREZ",
                rfc="PEHJ8001011A1",
                copro_soc_conyugal_e="No"
            )
        ],
        datos_enajenantes=[
            DatosEnajenante(
                nombre="MARIA LOPEZ",
                rfc="LOMM9001012B2",
                copro_soc_conyugal_e="No"
            )
        ]
    )

    comp = create_complemento_notarios(data)
    assert comp is not None
    # Verify structure using dictionary access if possible or attribute access
    # satcfdi objects support dictionary access
    assert comp['DatosOperacion']['NumInstrumentoNotarial'] == 12345
    assert comp['DatosAdquiriente']['CoproSocConyugalE'] == 'No'
    assert comp['DatosAdquiriente']['DatosUnAdquiriente']['Nombre'] == 'JUAN PEREZ'

def test_create_complemento_copropiedad():
    data = ComplementoNotariosModel(
        datos_notario=DatosNotario(
            curp="ABCD123456HDFRDA01",
            num_notaria=4,
            entidad_federativa="06"
        ),
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=12345,
            fecha_inst_notarial=date(2023, 10, 25),
            monto_operacion=Decimal("1000000.00"),
            subtotal=Decimal("1000.00"),
            iva=Decimal("160.00")
        ),
        desc_inmuebles=[
            DescInmueble(
                tipo_inmueble="01",
                calle="Av. Mexico",
                estado="06",
                pais="MEX",
                codigo_postal="28200"
            )
        ],
        datos_adquirientes=[
            DatosAdquiriente(
                nombre="JUAN PEREZ",
                rfc="PEHJ8001011A1",
                porcentaje=Decimal("50.00"),
                copro_soc_conyugal_e="Si"
            ),
            DatosAdquiriente(
                nombre="PEDRO PEREZ",
                rfc="PEHJ8101012B2",
                porcentaje=Decimal("50.00"),
                copro_soc_conyugal_e="Si"
            )
        ],
        datos_enajenantes=[
            DatosEnajenante(
                nombre="MARIA LOPEZ",
                copro_soc_conyugal_e="No"
            )
        ]
    )

    comp = create_complemento_notarios(data)
    assert comp['DatosAdquiriente']['CoproSocConyugalE'] == 'Si'
    assert len(comp['DatosAdquiriente']['DatosAdquirientesCopSC']) == 2
    assert comp['DatosAdquiriente']['DatosAdquirientesCopSC'][0]['Porcentaje'] == Decimal("50.00")

def test_create_complemento_copropiedad_fail_sum():
    data = ComplementoNotariosModel(
        datos_notario=DatosNotario(
            curp="ABCD123456HDFRDA01",
            num_notaria=4,
            entidad_federativa="06"
        ),
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=12345,
            fecha_inst_notarial=date(2023, 10, 25),
            monto_operacion=Decimal("1000000.00"),
            subtotal=Decimal("1000.00"),
            iva=Decimal("160.00")
        ),
        desc_inmuebles=[DescInmueble(tipo_inmueble="01", calle="x", estado="06", pais="MEX", codigo_postal="28200")],
        datos_adquirientes=[
            DatosAdquiriente(
                nombre="JUAN",
                porcentaje=Decimal("50.00"),
                copro_soc_conyugal_e="Si"
            ),
             DatosAdquiriente(
                nombre="PEDRO",
                porcentaje=Decimal("40.00"),
                copro_soc_conyugal_e="Si"
            )
        ],
        datos_enajenantes=[DatosEnajenante(nombre="MARIA", copro_soc_conyugal_e="No")]
    )

    with pytest.raises(ValueError):
        create_complemento_notarios(data)
