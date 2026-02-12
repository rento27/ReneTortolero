from decimal import Decimal
import pytest
from datetime import date
import os
from notaria_4_core.backend.lib.xml_generator import generate_signed_xml
from notaria_4_core.backend.lib.api_models import InvoiceRequest, ComplementoNotarios, DatosNotario, DatosOperacion
from satcfdi.create.cfd import cfdi40

# Setup Mock for all tests
os.environ["MOCK_SIGNER"] = "true"

def test_generate_xml_with_complemento():
    # Mock data based on the prompt scenario (coproperty)
    invoice_data = {
        "receptor": {
            "rfc": "XAXX010101000",
            "nombre": "JUAN PEREZ",
            "uso_cfdi": "G03",
            "domicilio_fiscal": "28200",
            "regimen_fiscal": "605"
        },
        "conceptos": [
            {
                "clave_prod_serv": "84111500",
                "cantidad": Decimal("1.0"),
                "clave_unidad": "E48",
                "descripcion": "HONORARIOS NOTARIALES",
                "valor_unitario": Decimal("1000.00"),
                "importe": Decimal("1000.00"),
                "objeto_imp": "02"
            }
        ],
        "subtotal": Decimal("1000.00"),
        "total": Decimal("1160.00"),
        "complemento_notarios": {
            "datos_notario": {
                "curp": "ABCD123456HDFR0500",
                "num_notaria": 4,
                "entidad_federativa": "06",
                "adscripcion": "MANZANILLO COLIMA"
            },
            "datos_operacion": {
                "num_instrumento_notarial": 12345,
                "fecha_inst_notarial": date(2023, 10, 27),
                "monto_operacion": Decimal("500000.00"),
                "subtotal": Decimal("1000.00"),
                "iva": Decimal("160.00")
            },
            "desc_inmuebles": [
                {
                    "tipo_inmueble": "01",
                    "calle": "AVENIDA MEXICO",
                    "no_exterior": "100",
                    "colonia": "CENTRO",
                    "municipio": "MANZANILLO",
                    "estado": "COL",
                    "pais": "MEX",
                    "codigo_postal": "28200"
                }
            ],
            "datos_adquirientes": [
                {
                    "nombre": "PEDRO PARAMO",
                    "rfc": "PEPA800101XXX",
                    "porcentaje": Decimal("50.00"),
                    "copro_soc_conyugal_e": "Si"
                },
                {
                    "nombre": "SUSANA SAN JUAN",
                    "rfc": "SASJ850101XXX",
                    "porcentaje": Decimal("50.00"),
                    "copro_soc_conyugal_e": "Si"
                }
            ],
            "datos_enajenantes": [
                {
                    "nombre": "JUAN RULFO",
                    "apellido_paterno": "PEREZ",
                    "rfc": "XAXX010101000",
                    "curp": "XAXX010101HDFR0000",
                    "porcentaje": Decimal("100.00"),
                    "copro_soc_conyugal_e": "No"
                }
            ]
        }
    }

    # Generate XML
    xml_bytes = generate_signed_xml(invoice_data)

    # Assertions
    assert b"cfdi:Comprobante" in xml_bytes
    assert b"notariospublicos:NotariosPublicos" in xml_bytes
    assert b"Version=\"1.0\"" in xml_bytes # Complement version

    # Check for coproperty logic
    assert b"CoproSocConyugalE=\"Si\"" in xml_bytes
    assert b"Porcentaje=\"50.00\"" in xml_bytes

def test_generate_xml_persona_moral_retentions():
    # Test RFC 12 chars triggering retentions
    invoice_data = {
        "receptor": {
            "rfc": "ABC123456T12", # 12 chars
            "nombre": "EMPRESA S.A. DE C.V.",
            "uso_cfdi": "G03",
            "domicilio_fiscal": "28200",
            "regimen_fiscal": "601"
        },
        "conceptos": [
            {
                "clave_prod_serv": "84111500",
                "cantidad": Decimal("1.0"),
                "clave_unidad": "E48",
                "descripcion": "SERV",
                "valor_unitario": Decimal("1000.00"),
                "importe": Decimal("1000.00"),
                "objeto_imp": "02"
            }
        ],
        "subtotal": Decimal("1000.00"),
        "total": Decimal("1000.00") # Total not strictly validated by generator stub
    }

    xml_bytes = generate_signed_xml(invoice_data)

    # Check for Retentions
    # ISR 10% = 100.00
    # IVA 10.6667% = 106.67

    assert b"Impuesto=\"001\"" in xml_bytes # ISR
    assert b"Importe=\"100.00\"" in xml_bytes

    assert b"Impuesto=\"002\"" in xml_bytes # IVA
    assert b"Importe=\"106.67\"" in xml_bytes

def test_complemento_notarios_future_date_fails():
    from notaria_4_core.backend.lib.complement_notarios import create_complemento_notarios
    from datetime import timedelta

    future_date = date.today() + timedelta(days=1)

    # Minimal stub
    data = ComplementoNotarios(
        datos_notario=DatosNotario(curp="ABCD123456HDFR0500", num_notaria=4, entidad_federativa="06"),
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=1,
            fecha_inst_notarial=future_date,
            monto_operacion=Decimal("100"),
            subtotal=Decimal("100"),
            iva=Decimal("16")
        ),
        desc_inmuebles=[],
        datos_adquirientes=[],
        datos_enajenantes=[]
    )

    with pytest.raises(ValueError, match="FechaInstNotarial cannot be in the future"):
        create_complemento_notarios(data)

def test_generate_xml_sanitization():
    # Test that name with "S.A. DE C.V." is sanitized inside generator
    invoice_data = {
        "receptor": {
            "rfc": "XAXX010101000",
            "nombre": "EMPRESA PATITO, S.A. DE C.V.", # Dirty name
            "uso_cfdi": "G03",
            "domicilio_fiscal": "28200",
            "regimen_fiscal": "601"
        },
        "conceptos": [
            {
                "clave_prod_serv": "84111500",
                "cantidad": Decimal("1.0"),
                "clave_unidad": "E48",
                "descripcion": "SERV",
                "valor_unitario": Decimal("1000.00"),
                "objeto_imp": "01"
            }
        ],
        "subtotal": Decimal("1000.00"),
        "total": Decimal("1000.00")
    }

    xml_bytes = generate_signed_xml(invoice_data)

    # Check that "S.A. DE C.V." is gone and name is upper case
    assert b"Nombre=\"EMPRESA PATITO\"" in xml_bytes
