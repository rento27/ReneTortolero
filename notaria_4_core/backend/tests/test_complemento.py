from decimal import Decimal
import pytest
from datetime import date
from notaria_4_core.backend.lib.api_models import (
    ComplementoNotariosModel,
    DatosNotarioModel,
    DatosOperacionModel,
    DescInmuebleModel,
    DatosEnajenanteModel,
    DatosUnEnajenanteModel,
    DatosAdquirienteModel,
    DatosAdquirientesCopSCModel,
    DatosUnAdquirienteModel,
    DatosEnajenantesCopSCModel
)
from notaria_4_core.backend.lib.complement_notarios import create_complemento_notarios

def test_create_complemento_valid_single():
    """Test valid complement creation with single enajenante/adquiriente."""
    data = ComplementoNotariosModel(
        datos_notario=DatosNotarioModel(curp="CURPNOTARIO1234567"),
        datos_operacion=DatosOperacionModel(
            num_instrumento_notarial=123,
            fecha_inst_notarial=date(2023, 10, 1),
            monto_operacion=Decimal("1000000.00"),
            subtotal=Decimal("900000.00"),
            iva=Decimal("160000.00")
        ),
        desc_inmuebles=[DescInmuebleModel(
            tipo_inmueble="01",
            calle="Calle Falsa 123",
            municipio="Manzanillo",
            estado="Colima",
            codigo_postal="28200",
            pais="MEX"
        )],
        datos_enajenante=DatosEnajenanteModel(
            copro_soc_conyugal_e="No",
            datos_un_enajenante=DatosUnEnajenanteModel(
                nombre="JUAN",
                apellido_paterno="PEREZ",
                rfc="PEJU800101XYZ",
                curp="PEJU800101HOCMXA00"
            )
        ),
        datos_adquiriente=DatosAdquirienteModel(
            copro_soc_conyugal_e="No",
            datos_un_adquiriente=DatosUnAdquirienteModel(
                nombre="PEDRO",
                rfc="PAPE900101XYZ",
                apellido_paterno="PARAMO"
            )
        )
    )

    comp = create_complemento_notarios(data)
    assert comp is not None
    # Verify internal structure (satcfdi object)
    assert comp['DatosOperacion']['NumInstrumentoNotarial'] == 123

def test_create_complemento_valid_copropiedad():
    """Test valid complement creation with coproperty."""
    data = ComplementoNotariosModel(
        datos_notario=DatosNotarioModel(curp="CURPNOTARIO1234567"),
        datos_operacion=DatosOperacionModel(
            num_instrumento_notarial=124,
            fecha_inst_notarial=date(2023, 10, 2),
            monto_operacion=Decimal("2000000.00"),
            subtotal=Decimal("1800000.00"),
            iva=Decimal("320000.00")
        ),
        desc_inmuebles=[DescInmuebleModel(
            tipo_inmueble="03",
            calle="Av Mexico",
            municipio="Manzanillo",
            estado="Colima",
            codigo_postal="28218",
            pais="MEX"
        )],
        datos_enajenante=DatosEnajenanteModel(
            copro_soc_conyugal_e="No",
            datos_un_enajenante=DatosUnEnajenanteModel(
                nombre="VENDEDOR",
                apellido_paterno="UNO",
                rfc="VEND800101XYZ",
                curp="VEND800101HOCMXA00"
            )
        ),
        datos_adquiriente=DatosAdquirienteModel(
            copro_soc_conyugal_e="Si",
            datos_adquirientes_cop_sc=[
                DatosAdquirientesCopSCModel(
                    nombre="COMPRADOR1",
                    rfc="COMP100101XYZ",
                    porcentaje=Decimal("50.00"),
                    apellido_paterno="UNO"
                ),
                DatosAdquirientesCopSCModel(
                    nombre="COMPRADOR2",
                    rfc="COMP200101XYZ",
                    porcentaje=Decimal("50.00"),
                    apellido_paterno="DOS"
                )
            ]
        )
    )

    comp = create_complemento_notarios(data)
    assert comp is not None
    # Verify coproperty list
    adq = comp['DatosAdquiriente']
    assert adq['CoproSocConyugalE'] == 'Si'
    assert len(adq['DatosAdquirientesCopSC']) == 2

def test_create_complemento_invalid_percentage():
    """Test failure when percentages do not sum to 100."""
    data = ComplementoNotariosModel(
        datos_notario=DatosNotarioModel(curp="CURPNOTARIO1234567"),
        datos_operacion=DatosOperacionModel(
            num_instrumento_notarial=125,
            fecha_inst_notarial=date(2023, 10, 3),
            monto_operacion=Decimal("100.00"),
            subtotal=Decimal("100.00"),
            iva=Decimal("16.00")
        ),
        desc_inmuebles=[DescInmuebleModel(
            tipo_inmueble="01",
            calle="X",
            municipio="Y",
            estado="Z",
            codigo_postal="00000",
            pais="MEX"
        )],
        datos_enajenante=DatosEnajenanteModel(
            copro_soc_conyugal_e="No",
            datos_un_enajenante=DatosUnEnajenanteModel(
                nombre="X", apellido_paterno="Y", rfc="XAXX010101000", curp="XAXX010101HXXXXX00"
            )
        ),
        datos_adquiriente=DatosAdquirienteModel(
            copro_soc_conyugal_e="Si",
            datos_adquirientes_cop_sc=[
                DatosAdquirientesCopSCModel(
                    nombre="C1", rfc="C1XX010101000", porcentaje=Decimal("33.33"), apellido_paterno="C"
                ),
                DatosAdquirientesCopSCModel(
                    nombre="C2", rfc="C2XX010101000", porcentaje=Decimal("33.33"), apellido_paterno="C"
                )
            ]
        )
    )

    with pytest.raises(ValueError) as excinfo:
        create_complemento_notarios(data)

    assert "Sum of percentages must be 100.00%" in str(excinfo.value)
