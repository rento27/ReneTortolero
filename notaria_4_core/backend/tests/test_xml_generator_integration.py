from decimal import Decimal
import pytest
from notaria_4_core.backend.lib.xml_generator import generate_signed_xml
from satcfdi.create.cfd import cfdi40

def test_xml_generation_basic(monkeypatch):
    monkeypatch.setenv("MOCK_SIGNER", "1")
    data = {
        'receptor': {
            'rfc': 'XAXX010101000',
            'nombre': 'PUBLICO EN GENERAL',
            'uso_cfdi': 'S01',
            'domicilio_fiscal': '28200',
            'regimen_fiscal': '616'
        },
        'conceptos': [
            {
                'clave_prod_serv': '84111506',
                'cantidad': 1,
                'clave_unidad': 'E48',
                'descripcion': 'HONORARIOS',
                'valor_unitario': 1000.00,
                'importe': 1000.00,
                'objeto_imp': '02'
            }
        ],
        'subtotal': 1000.00,
        'total': 1160.00
    }

    xml_bytes = generate_signed_xml(data)
    assert b"cfdi:Comprobante" in xml_bytes
    assert b'Rfc="XAXX010101000"' in xml_bytes
    # Check taxes
    assert b'Impuesto="002"' in xml_bytes # IVA

def test_xml_moral_retentions(monkeypatch):
    monkeypatch.setenv("MOCK_SIGNER", "1")
    data = {
        'receptor': {
            'rfc': 'ABC123456T12', # 12 chars -> Moral
            'nombre': 'EMPRESA MORAL',
            'uso_cfdi': 'G03',
            'domicilio_fiscal': '28200',
            'regimen_fiscal': '601'
        },
        'conceptos': [
            {
                'clave_prod_serv': '84111506',
                'cantidad': 1,
                'clave_unidad': 'E48',
                'descripcion': 'HONORARIOS',
                'valor_unitario': 1000.00,
                'importe': 1000.00,
                'objeto_imp': '02'
            }
        ],
        'subtotal': 1000.00,
        'total': 1000.00 + 160.00 - 100.00 - 106.67 # Net total
    }

    xml_bytes = generate_signed_xml(data)
    # Verify Retentions exist
    assert b'Retenciones' in xml_bytes
    assert b'Impuesto="001"' in xml_bytes # ISR
    assert b'Impuesto="002"' in xml_bytes # IVA
    # Check amounts (roughly)
    assert b'Importe="100.00"' in xml_bytes
    assert b'Importe="106.67"' in xml_bytes

def test_xml_with_complement(monkeypatch):
    monkeypatch.setenv("MOCK_SIGNER", "1")
    from datetime import date

    # Minimal data with complement
    data = {
        'receptor': {'rfc': 'XAXX010101000', 'nombre': 'X', 'uso_cfdi': 'S01', 'domicilio_fiscal': '28200'},
        'conceptos': [{'clave_prod_serv': '1', 'cantidad': 1, 'clave_unidad': '1', 'descripcion': 'D', 'valor_unitario': 1, 'importe': 1, 'objeto_imp': '01'}],
        'subtotal': 1, 'total': 1,
        'complemento_notarios': {
            'datos_notario': {},
            'datos_operacion': {
                'num_instrumento_notarial': 12345,
                'fecha_inst_notarial': date.today(),
                'monto_operacion': 100000,
                'subtotal': 1000,
                'iva': 160
            },
            'desc_inmuebles': [{'tipo_inmueble': '01', 'calle': 'C', 'entidad_federativa': '06', 'pais': 'MEX', 'codigo_postal': '28200', 'municipio': '001'}],
            'datos_adquirientes': [{'nombre': 'A', 'rfc': 'R', 'curp': 'C', 'copro_soc_conyugal_e': 'No'}],
            'datos_enajenantes': [{'nombre': 'E', 'rfc': 'R', 'curp': 'C', 'copro_soc_conyugal_e': 'No'}]
        }
    }

    xml_bytes = generate_signed_xml(data)
    assert b'notariospublicos:NotariosPublicos' in xml_bytes
    assert b'NumInstrumentoNotarial="12345"' in xml_bytes
