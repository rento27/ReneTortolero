import pytest
from decimal import Decimal
import base64
import xml.etree.ElementTree as ET

from notaria_4_core.backend.lib.xml_generator import generate_signed_xml
from notaria_4_core.backend.api_models import InvoiceRequest, Receptor, Concepto, ComplementoNotarios, DatosNotario, DatosOperacion, DescInmueble, DatosEnajenante, DatosAdquiriente

def test_basic_cfdi_generation():
    # Setup Data
    req = InvoiceRequest(
        receptor=Receptor(
            rfc="XAXX010101000",
            nombre="PUBLICO EN GENERAL",
            uso_cfdi="S01",
            domicilio_fiscal="28200",
            regimen_fiscal="616"
        ),
        conceptos=[
            Concepto(
                clave_prod_serv="80131502", # Notarial Service
                cantidad=Decimal("1.0"),
                clave_unidad="E48",
                descripcion="HONORARIOS NOTARIALES",
                valor_unitario=Decimal("5000.00"),
                importe=Decimal("5000.00"),
                objeto_imp="02" # Should be enforced anyway
            )
        ],
        subtotal=Decimal("5000.00"),
        total=Decimal("5800.00")
    )

    xml_bytes = generate_signed_xml(req.model_dump())
    assert xml_bytes.startswith(b"<?xml")

    # Parse XML to check content
    root = ET.fromstring(xml_bytes)
    ns = {'cfdi': 'http://www.sat.gob.mx/cfd/4'}

    # Check total
    assert Decimal(root.attrib['Total']) == Decimal("5800.00")

    # Check taxes
    concepts = root.findall('cfdi:Conceptos/cfdi:Concepto', ns)
    assert len(concepts) == 1

    # Check ObjetoImp enforced to 02
    assert concepts[0].attrib['ObjetoImp'] == "02"

    # Check Traslados inside Concepto
    traslados = concepts[0].find('cfdi:Impuestos/cfdi:Traslados/cfdi:Traslado', ns)
    assert traslados is not None
    assert Decimal(traslados.attrib['Importe']) == Decimal("800.00") # 16% of 5000

def test_moral_retentions():
    # Persona Moral RFC
    req = InvoiceRequest(
        receptor=Receptor(
            rfc="ABC123456T12", # 12 chars -> Moral
            nombre="EMPRESA MORAL SA DE CV",
            uso_cfdi="G03",
            domicilio_fiscal="28200",
            regimen_fiscal="601"
        ),
        conceptos=[
            Concepto(
                clave_prod_serv="80131502",
                cantidad=Decimal("1.0"),
                clave_unidad="E48",
                descripcion="HONORARIOS",
                valor_unitario=Decimal("1000.00"),
                importe=Decimal("1000.00"),
                objeto_imp="02"
            )
        ],
        subtotal=Decimal("1000.00"),
        total=Decimal("1160.00") # Before retentions subtraction?
        # Actually, Total = Subtotal - Descuento + Traslados - Retenciones
        # Subtotal: 1000. Traslados: 160.
        # Ret ISR: 100. Ret IVA: 106.67.
        # Total = 1000 + 160 - 100 - 106.67 = 953.33
    )

    xml_bytes = generate_signed_xml(req.model_dump())
    root = ET.fromstring(xml_bytes)
    ns = {'cfdi': 'http://www.sat.gob.mx/cfd/4'}

    # Check Total calculation by satcfdi
    # satcfdi recalculates Total based on concepts taxes and retentions if passed correctly.
    # Expected: 953.33
    assert Decimal(root.attrib['Total']) == Decimal("953.33")

    # Check Retentions in Concepto
    concept = root.find('cfdi:Conceptos/cfdi:Concepto', ns)
    retenciones = concept.findall('cfdi:Impuestos/cfdi:Retenciones/cfdi:Retencion', ns)
    assert len(retenciones) == 2

    # Check ISR
    isr = next(r for r in retenciones if r.attrib['Impuesto'] == "001")
    assert Decimal(isr.attrib['Importe']) == Decimal("100.00")

    # Check IVA
    iva = next(r for r in retenciones if r.attrib['Impuesto'] == "002")
    assert Decimal(iva.attrib['Importe']) == Decimal("106.67")

def test_complemento_notarios_xml():
    req = InvoiceRequest(
        receptor=Receptor(
            rfc="XAXX010101000",
            nombre="PUBLICO",
            uso_cfdi="S01",
            domicilio_fiscal="28200",
            regimen_fiscal="616"
        ),
        conceptos=[
            Concepto(clave_prod_serv="80131502", cantidad=Decimal("1"), clave_unidad="E48", descripcion="H", valor_unitario=Decimal("1"), importe=Decimal("1"), objeto_imp="02")
        ],
        subtotal=Decimal("1"), total=Decimal("1.16"),
        complemento_notarios=ComplementoNotarios(
            desc_inmuebles=[DescInmueble(tipo_inmueble="03", calle="C", municipio="M", estado="06", codigo_postal="28200", pais="MEX")],
            datos_operacion=DatosOperacion(num_instrumento_notarial=1, fecha_inst_notarial="2023-01-01", monto_operacion=Decimal("1"), subtotal=Decimal("1"), iva=Decimal("1")),
            datos_notario=DatosNotario(curp="ABCD123456HCOLR0A0", num_notaria=4, entidad_federativa="06"),
            datos_enajenante=DatosEnajenante(copro_soc_conyugal_e="No", datos_un_enajenante={"nombre": "Vendedor", "rfc": "XAXX010101000", "apellido_paterno": "Perez", "curp": "ABCD123456HCOLR0A0"}),
            datos_adquiriente=DatosAdquiriente(copro_soc_conyugal_e="No", datos_un_adquiriente={"nombre": "Comprador", "rfc": "XAXX010101000"})
        )
    )

    xml_bytes = generate_signed_xml(req.model_dump())
    root = ET.fromstring(xml_bytes)

    # Check Complemento Namespace
    # satcfdi handles namespaces, but lxml/ET might need registration or full tag
    # Check if 'notariospublicos' exists
    # Namespace is usually http://www.sat.gob.mx/notariospublicos

    # Just check string presence for simplicity as namespace handling in ET can be tricky without map
    xml_str = xml_bytes.decode('utf-8')
    assert "notariospublicos:NotariosPublicos" in xml_str
    assert 'NumNotaria="4"' in xml_str
    assert 'CURP="ABCD123456HCOLR0A0"' in xml_str

def test_copropiedad_validation_xml():
    req = InvoiceRequest(
        receptor=Receptor(
            rfc="XAXX010101000",
            nombre="PUBLICO",
            uso_cfdi="S01",
            domicilio_fiscal="28200",
            regimen_fiscal="616"
        ),
        conceptos=[Concepto(clave_prod_serv="80131502", cantidad=Decimal("1"), clave_unidad="E48", descripcion="H", valor_unitario=Decimal("1"), importe=Decimal("1"), objeto_imp="02")],
        subtotal=Decimal("1"), total=Decimal("1.16"),
        complemento_notarios=ComplementoNotarios(
            desc_inmuebles=[DescInmueble(tipo_inmueble="03", calle="C", municipio="M", estado="06", codigo_postal="28200", pais="MEX")],
            datos_operacion=DatosOperacion(num_instrumento_notarial=1, fecha_inst_notarial="2023-01-01", monto_operacion=Decimal("1"), subtotal=Decimal("1"), iva=Decimal("1")),
            datos_notario=DatosNotario(curp="ABCD123456HCOLR0A0", num_notaria=4, entidad_federativa="06"),
            datos_enajenante=DatosEnajenante(copro_soc_conyugal_e="No", datos_un_enajenante={"nombre": "Vendedor", "rfc": "XAXX010101000", "apellido_paterno": "Perez", "curp": "ABCD123456HCOLR0A0"}),
            datos_adquiriente=DatosAdquiriente(
                copro_soc_conyugal_e="Si",
                datos_adquirientes_cop_sc=[
                    {"nombre": "A", "rfc": "XAXX010101000", "porcentaje": Decimal("50.00"), "curp": "ABCD123456HCOLR0A0"},
                    {"nombre": "B", "rfc": "XAXX010101000", "porcentaje": Decimal("40.00"), "curp": "ABCD123456HCOLR0A0"} # Sum 90 != 100
                ]
            )
        )
    )
    # The validate_copropiedad function raises ValueError with specific message
    with pytest.raises(ValueError, match="Sum of percentages must be 100.00%"):
        generate_signed_xml(req.model_dump())
