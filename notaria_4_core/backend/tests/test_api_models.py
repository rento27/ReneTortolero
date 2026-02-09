from decimal import Decimal
import pytest
from pydantic import ValidationError
from notaria_4_core.backend.api_models import InvoiceRequest, Receptor, Concepto, ComplementoNotarios, DatosNotario, DatosOperacion, DescInmueble, DatosEnajenante, DatosAdquiriente

def test_receptor_validation():
    # Valid
    r = Receptor(rfc="ABC123456T12", nombre="Empresa", uso_cfdi="G03", domicilio_fiscal="28200", regimen_fiscal="601")
    assert r.rfc == "ABC123456T12"

    # Invalid RFC length
    with pytest.raises(ValidationError):
        Receptor(rfc="ABC", nombre="Empresa", uso_cfdi="G03", domicilio_fiscal="28200", regimen_fiscal="601")

def test_complemento_structure():
    # Test nested structure validation
    comp = ComplementoNotarios(
        desc_inmuebles=[
            DescInmueble(tipo_inmueble="03", calle="Calle 1", municipio="Manzanillo", estado="06", codigo_postal="28200")
        ],
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=123,
            fecha_inst_notarial="2023-10-27",
            monto_operacion=Decimal("1000000.00"),
            subtotal=Decimal("50000.00"),
            iva=Decimal("8000.00")
        ),
        datos_notario=DatosNotario(
            curp="ABCD123456HCOLR0A0", # Corrected length 18 chars
            num_notaria=4,
            entidad_federativa="06"
        ),
        datos_enajenante=DatosEnajenante(
            copro_soc_conyugal_e="No",
            datos_un_enajenante={"nombre": "Juan", "rfc": "XAXX010101000", "apellido_paterno": "Perez", "curp": "ABCD123456HCOLR0A0"}
        ),
        datos_adquiriente=DatosAdquiriente(
            copro_soc_conyugal_e="No",
            datos_un_adquiriente={"nombre": "Pedro", "rfc": "XAXX010101000"}
        )
    )
    assert comp.datos_operacion.num_instrumento_notarial == 123
