import pytest
from decimal import Decimal
from datetime import date
from notaria_4_core.backend.lib.api_models import InvoiceRequest, Receptor, Concepto, ComplementoNotariosModel, DatosNotario, DatosOperacion, DatosInmueble, DatosAdquiriente, DatosEnajenante
from notaria_4_core.backend.lib.xml_generator import generate_signed_xml
from notaria_4_core.backend.lib.complement_notarios import create_complemento_notarios
from notaria_4_core.backend.lib.fiscal_engine import sanitize_name

# Check if satcfdi is installed
try:
    import satcfdi
    SATCFDI_AVAILABLE = True
except ImportError:
    SATCFDI_AVAILABLE = False

@pytest.fixture
def basic_invoice_request():
    return InvoiceRequest(
        receptor=Receptor(
            rfc="XAXX010101000",
            nombre="Juan Perez",
            uso_cfdi="G03",
            domicilio_fiscal="28200",
            regimen_fiscal="616"
        ),
        conceptos=[
            Concepto(
                clave_prod_serv="84111506",
                cantidad=Decimal("1"),
                clave_unidad="E48",
                descripcion="Honorarios Medicos",
                valor_unitario=Decimal("1000.00"),
                importe=Decimal("1000.00"),
                objeto_imp="02"
            )
        ],
        forma_pago="03",
        metodo_pago="PUE",
        subtotal=Decimal("1000.00"),
        total=Decimal("1160.00")
    )

def test_sanitize_name_integration(basic_invoice_request):
    basic_invoice_request.receptor.nombre = "Inmobiliaria del Pacífico, S.A. de C.V."
    if not SATCFDI_AVAILABLE:
        pytest.skip("satcfdi not available")

    xml_bytes = generate_signed_xml(basic_invoice_request)
    assert b"INMOBILIARIA DEL PACIFICO" in xml_bytes.upper()
    assert b"S.A. DE C.V." not in xml_bytes.upper()

def test_persona_moral_retentions():
    if not SATCFDI_AVAILABLE:
        pytest.skip("satcfdi not available")

    req = InvoiceRequest(
        receptor=Receptor(
            rfc="ABC123456T12",
            nombre="Empresa Moral",
            uso_cfdi="G03",
            domicilio_fiscal="28200",
            regimen_fiscal="601"
        ),
        conceptos=[
            Concepto(
                clave_prod_serv="84111506",
                cantidad=Decimal("1"),
                clave_unidad="E48",
                descripcion="Servicios Profesionales",
                valor_unitario=Decimal("1000.00"),
                importe=Decimal("1000.00"),
                objeto_imp="02"
            )
        ],
        subtotal=Decimal("1000.00"),
        total=Decimal("1000.00")
    )

    xml_bytes = generate_signed_xml(req)
    # Check for Retenciones (001 ISR, 002 IVA)
    assert b'Impuesto="001"' in xml_bytes
    assert b'Impuesto="002"' in xml_bytes
    assert b'Importe="100.00"' in xml_bytes
    assert b'Importe="106.67"' in xml_bytes

def test_complemento_notarios_structure():
    if not SATCFDI_AVAILABLE:
        pytest.skip("satcfdi not available")

    comp_data = ComplementoNotariosModel(
        datos_notario=DatosNotario(
            num_notaria=4,
            entidad_federativa="06",
            adscripcion="MANZANILLO"
        ),
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=12345,
            fecha_inst_notarial=date.today(),
            monto_operacion=Decimal("500000.00"),
            subtotal=Decimal("450000.00"),
            iva=Decimal("50000.00")
        ),
        datos_inmueble=DatosInmueble(
            tipo_inmueble="01",
            calle="Av. Mexico",
            municipio="Manzanillo",
            estado="Colima",
            pais="Mexico",
            codigo_postal="28200"
        ),
        datos_adquirientes=[
            DatosAdquiriente(
                nombre="Juan",
                apellido_paterno="Perez",
                rfc="PEPJ8001019Q8",
                porcentaje=Decimal("50.00"),
                copro_soc_conyugal_e="Si"
            ),
            DatosAdquiriente(
                nombre="Maria",
                apellido_paterno="Gomez",
                rfc="GOMM8001019Q8",
                porcentaje=Decimal("50.00"),
                copro_soc_conyugal_e="Si"
            )
        ],
        datos_enajenantes=[
            DatosEnajenante(
                nombre="Pedro",
                apellido_paterno="Lopez",
                rfc="LOPP8001019Q8",
                curp="LOPP800101HOCRRA00",
                porcentaje=Decimal("100.00"),
                copro_soc_conyugal_e="No"
            )
        ]
    )

    notarios = create_complemento_notarios(comp_data)
    assert notarios is not None
    # Access via keys or attributes
    # In satcfdi, keys are typically PascalCase matching XSD
    assert notarios['DatosNotario']['NumNotaria'] == 4

    # Check DatosAdquirientes
    # It should be a list of DatosAdquiriente objects or wrapped
    # Since we removed DatosAdquirientes wrapper class usage, we check usage
    # notarios['DatosAdquirientes'] might exist as a wrapper key if satcfdi creates it from list
    # or 'DatosAdquiriente' if flattened.
    # Usually satcfdi output dict/xml structure respects XSD.
    # Let's check generally if data is there
    # Or just rely on XML generation test

    req = InvoiceRequest(
        receptor=Receptor(
            rfc="XAXX010101000",
            nombre="Publico General",
            uso_cfdi="S01",
            domicilio_fiscal="28200",
            regimen_fiscal="616"
        ),
        conceptos=[
            Concepto(
                clave_prod_serv="84111506",
                cantidad=Decimal("1"),
                clave_unidad="E48",
                descripcion="Tramite Notarial",
                valor_unitario=Decimal("5000.00"),
                importe=Decimal("5000.00"),
                objeto_imp="01"
            )
        ],
        complemento_notarios=comp_data
    )

    xml_bytes = generate_signed_xml(req)
    assert b'Complemento' in xml_bytes
    assert b'notariospublicos:NotariosPublicos' in xml_bytes
    assert b'NumNotaria="4"' in xml_bytes
    # Check if coproperty was handled
    assert b'CoproSocConyugalE="Si"' in xml_bytes
