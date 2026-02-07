from decimal import Decimal
import pytest
import sys
import os
from datetime import date

# Add the backend directory to sys.path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.xml_generator import generate_signed_xml
# We don't strictly need InvoiceRequest for dict construction, but if we used it:
# from main import InvoiceRequest

def test_generate_xml_with_complement():
    # Mock Data matching the new Pydantic models
    invoice_data = {
        "receptor": {
            "rfc": "XAXX010101000",
            "nombre": "PUBLICO EN GENERAL",
            "uso_cfdi": "S01",
                "domicilio_fiscal": "28200",
                "regimen_fiscal": "601"
        },
        "conceptos": [
            {
                "clave_prod_serv": "84111500",
                "cantidad": Decimal("1.0"),
                "clave_unidad": "E48",
                "descripcion": "HONORARIOS NOTARIALES",
                "valor_unitario": Decimal("10000.00"),
                "importe": Decimal("10000.00"),
                "objeto_imp": "02"
            }
        ],
        "subtotal": Decimal("10000.00"),
        "total": Decimal("11600.00"),
        "complemento_notarios": {
            "datos_notario": {
                "num_notaria": 4,
                "entidad_federativa": "06",
                    "adscripcion": "MANZANILLO COLIMA",
                    "curp": "TOSR520601HCLXXX01"
            },
            "desc_inmuebles": [
                {
                    "tipo_inmueble": "01",
                    "calle": "AVENIDA MEXICO",
                    "municipio": "MANZANILLO",
                    "estado": "COLIMA",
                    "pais": "MEXICO",
                    "codigo_postal": "28200"
                }
            ],
            "datos_operacion": {
                "num_instrumento_notarial": 12345,
                "fecha_inst_notarial": "2023-10-27",
                "monto_operacion": Decimal("500000.00"),
                "subtotal": Decimal("10000.00"),
                "iva": Decimal("1600.00")
            },
            "datos_adquiriente": {
                "copro_soc_conyugal_e": "No",
                "datos_un_adquiriente": {
                    "nombre": "JUAN PEREZ",
                    "rfc": "XAXX010101000",
                    "apellido_paterno": "PEREZ",
                    "curp": "AAAA010101AAAAAA01"
                }
            },
            "datos_enajenante": {
                "copro_soc_conyugal_e": "No",
                "datos_un_enajenante": {
                    "nombre": "MARIA LOPEZ",
                    "rfc": "XAXX010101000",
                    "apellido_paterno": "LOPEZ",
                    "curp": "BBBB010101BBBBBB01"
                }
            }
        }
    }

    # Generate XML
    xml_bytes = generate_signed_xml(invoice_data)

    assert isinstance(xml_bytes, bytes)
    assert b"cfdi:Comprobante" in xml_bytes
    assert b"notariospublicos:NotariosPublicos" in xml_bytes
    assert b'NumNotaria="4"' in xml_bytes
    assert b'MontoOperacion="500000.00"' in xml_bytes

def test_generate_xml_coproperty_adquiriente():
    # Test Coproperty Logic
    invoice_data = {
        "receptor": {
            "rfc": "XAXX010101000",
            "nombre": "PUBLICO EN GENERAL",
            "uso_cfdi": "S01",
                "domicilio_fiscal": "28200",
                "regimen_fiscal": "601"
        },
        "conceptos": [
            {
                "clave_prod_serv": "84111500",
                "cantidad": 1,
                "clave_unidad": "E48",
                "descripcion": "HONORARIOS",
                "valor_unitario": 1000,
                "importe": 1000,
                "objeto_imp": "02"
            }
        ],
        "subtotal": 1000,
        "total": 1160,
        "complemento_notarios": {
                "datos_notario": {
                    "curp": "TOSR520601HCLXXX01"
                },
            "desc_inmuebles": [{"tipo_inmueble": "01", "calle": "TEST", "municipio": "TEST", "estado": "TEST", "pais": "TEST", "codigo_postal": "00000"}],
            "datos_operacion": {
                "num_instrumento_notarial": 1,
                "fecha_inst_notarial": "2023-10-27",
                "monto_operacion": 1000,
                "subtotal": 1000,
                "iva": 160
            },
            "datos_adquiriente": {
                "copro_soc_conyugal_e": "Si",
                "datos_adquirientes_cop_sc": [
                    {
                        "nombre": "ADQ1",
                        "rfc": "XAXX010101000",
                        "porcentaje": 50.00,
                        "apellido_paterno": "PATERNO1"
                    },
                    {
                        "nombre": "ADQ2",
                        "rfc": "XAXX010101000",
                        "porcentaje": 50.00,
                        "apellido_paterno": "PATERNO2"
                    }
                ]
            },
            "datos_enajenante": {
                "copro_soc_conyugal_e": "No",
                "datos_un_enajenante": {
                    "nombre": "ENAJ1",
                    "rfc": "XAXX010101000",
                    "apellido_paterno": "ENAJ_PATERNO",
                    "curp": "CCCC010101CCCCCC01"
                }
            }
        }
    }

    xml_bytes = generate_signed_xml(invoice_data)
    assert b'CoproSocConyugalE="Si"' in xml_bytes
    # satcfdi might format 50.00 as 50, 50.0, or 50.00 depending on input type and XSD
    assert b'Porcentaje="50"' in xml_bytes or b'Porcentaje="50.00"' in xml_bytes or b'Porcentaje="50.0"' in xml_bytes
