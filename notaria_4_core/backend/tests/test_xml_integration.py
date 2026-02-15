from decimal import Decimal
from datetime import date
import pytest
from notaria_4_core.backend.lib.xml_generator import generate_signed_xml
from notaria_4_core.backend.lib.api_models import InvoiceRequest, Receptor, Concepto, ComplementoNotariosModel, DatosNotario, DatosOperacion, DatosInmueble, DatosAdquiriente, DatosAdquirienteCopSC, DatosEnajenante

@pytest.fixture
def invoice_request():
    return InvoiceRequest(
        receptor=Receptor(
            rfc="XAXX010101000",
            nombre="PUBLICO EN GENERAL",
            uso_cfdi="S01",
            domicilio_fiscal="28200",
            regimen_fiscal="616"
        ),
        conceptos=[
            Concepto(
                clave_prod_serv="84111506",
                cantidad=Decimal("1"),
                clave_unidad="E48",
                descripcion="HONORARIOS",
                valor_unitario=Decimal("1000.00"),
                importe=Decimal("1000.00"),
                objeto_imp="02"
            )
        ],
        subtotal=Decimal("1000.00"),
        total=Decimal("1160.00")
    )

def test_generate_xml_basic(invoice_request):
    xml_bytes = generate_signed_xml(invoice_request)
    # Check basic XML structure
    assert b"cfdi:Comprobante" in xml_bytes
    assert b'Version="4.0"' in xml_bytes
    assert b'SubTotal="1000.00"' in xml_bytes
    # Taxes (16%) -> 160.00
    # Total -> 1160.00
    assert b'Total="1160.00"' in xml_bytes
    assert b'TasaOCuota="0.160000"' in xml_bytes

def test_persona_moral_retentions(invoice_request):
    # Change Receptor to Moral (12 chars)
    invoice_request.receptor.rfc = "ABC123456T12"
    # Ensure ObjetoImp is 02 (it is)

    xml_bytes = generate_signed_xml(invoice_request)
    xml_str = xml_bytes.decode('utf-8')

    # Check for Retentions in Concepto
    # satcfdi puts retentions at concept level and summarizes at root
    # Since we can't easily parse XML here without lxml (though we have it),
    # we'll do string checks for attributes that must be present.

    # Check for ISR (10% of 1000 = 100.00)
    assert 'Impuesto="001"' in xml_str
    assert 'TasaOCuota="0.100000"' in xml_str
    assert 'Importe="100.00"' in xml_str

    # Check for IVA Ret (10.6667% of 1000 = 106.67)
    assert 'Impuesto="002"' in xml_str
    assert 'TasaOCuota="0.106667"' in xml_str
    assert 'Importe="106.67"' in xml_str

def test_complemento_integration(invoice_request):
    # Add minimal Complemento
    invoice_request.complemento_notarios = ComplementoNotariosModel(
        datos_notario=DatosNotario(
            curp="TOSR520601HOCMXA00",
            num_notaria=4,
            entidad_federativa="06"
        ),
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=123,
            fecha_inst_notarial=date(2023, 1, 1),
            monto_operacion=Decimal("500000.00"),
            subtotal=Decimal("1000.00"),
            iva=Decimal("160.00")
        ),
        datos_inmueble=DatosInmueble(
            tipo_inmueble="01",
            calle="Calle Falsa 123",
            municipio="Manzanillo",
            estado="Colima",
            pais="Mexico",
            codigo_postal="28200"
        ),
        datos_adquirientes=[
            DatosAdquiriente(
                nombre="JUAN PEREZ",
                rfc="XAXX010101000",
                copro_soc_conyugal_e="No"
            )
        ],
        datos_enajenantes=[
            DatosEnajenante(
                nombre="PEDRO LOPEZ",
                apellido_paterno="LOPEZ",
                rfc="XAXX010101000",
                curp="PEGL800101HOCMXA00",
                copro_soc_conyugal_e="No"
            )
        ]
    )

    xml_bytes = generate_signed_xml(invoice_request)

    # Verify Complemento Node
    assert b"notariospublicos:NotariosPublicos" in xml_bytes
    assert b'NumInstrumentoNotarial="123"' in xml_bytes
    assert b'FechaInstNotarial="2023-01-01"' in xml_bytes
