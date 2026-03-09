import json
import base64
from decimal import Decimal
import datetime
import pytest

from notaria_4_core.backend.lib.xml_generator import generate_signed_xml

def get_base_invoice_data():
    return {
        "receptor": {
            "rfc": "ABC123456T12", # 12 chars -> Moral
            "nombre": "EMPRESA DE PRUEBA S.A. DE C.V.",
            "uso_cfdi": "G03",
            "domicilio_fiscal": "28200",
            "regimen_fiscal": "601"
        },
        "conceptos": [
            {
                "clave_prod_serv": "84111506",
                "cantidad": 1,
                "clave_unidad": "E48",
                "descripcion": "Honorarios Notariales",
                "valor_unitario": 10000.00,
                "importe": 10000.00,
                "objeto_imp": "02"
            }
        ],
        "subtotal": 10000.00,
        "total": 10533.33,
        "complemento_notarios": None
    }

def test_xml_generation_with_retentions():
    data = get_base_invoice_data()
    # Mock signer is loaded (env var handling or default None)
    xml_bytes = generate_signed_xml(data)

    # We should have satcfdi creating bytes
    assert xml_bytes is not None
    assert isinstance(xml_bytes, bytes)

    xml_str = xml_bytes.decode('utf-8')
    assert "Comprobante" in xml_str

    # Assert retentions and traslados are in the XML for concepts
    assert "Impuestos" in xml_str
    assert "Retenciones" in xml_str
    assert "1000.00" in xml_str # ISR 10%
    assert "1066.67" in xml_str # IVA 10.6667%
    assert "1600.00" in xml_str # IVA Trasladado 16%

def test_xml_generation_with_complement():
    data = get_base_invoice_data()

    # We use valid Complement data
    data["complemento_notarios"] = {
        "datos_notario": {
            "curp": "TOSR520601HOCMXA00",
            "num_notaria": 4,
            "entidad_federativa": "06",
            "adscripcion": "MANZANILLO"
        },
        "datos_operacion": {
            "num_instrumento_notarial": 12345,
            "fecha_inst_notarial": datetime.date.today().isoformat(),
            "monto_operacion": 1000000.00,
            "subtotal": 1000000.00,
            "iva": 0.00
        },
        "datos_enajenantes": [
            {
                "nombre": "Pedro Lopez",
                "rfc": "LOMP800101XYZ",
                "curp": "LOMP800101XYZABC01",
                "copro_soc_conyugal_e": "No"
            }
        ],
        "datos_adquirientes": [
            {
                "nombre": "Maria Sanchez",
                "rfc": "SAMM900101XYZ",
                "curp": "SAMM900101XYZABC01",
                "copro_soc_conyugal_e": "No"
            }
        ],
        "desc_inmuebles": [
            {
                "tipo_inmueble": "01",
                "calle": "Principal",
                "municipio": "Manzanillo",
                "estado": "06",
                "pais": "MEX",
                "codigo_postal": "28200"
            }
        ]
    }

    xml_bytes = generate_signed_xml(data)
    xml_str = xml_bytes.decode('utf-8')

    assert "NotariosPublicos" in xml_str
    assert "DatosOperacion" in xml_str
    assert "DatosEnajenante" in xml_str
    assert "DatosAdquiriente" in xml_str
