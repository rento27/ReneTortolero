import pytest
from decimal import Decimal
import logging

# Adjust import path if necessary
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.lib.xml_generator import generate_signed_xml

def test_generate_xml_simple_structure():
    invoice_data = {
        'receptor': {
            'rfc': 'XAXX010101000',
            'nombre': 'PUBLICO EN GENERAL',
            'uso_cfdi': 'S01',
            'domicilio_fiscal': '28200'
        },
        'conceptos': [
            {
                'clave_prod_serv': '84111506',
                'cantidad': 1,
                'clave_unidad': 'E48',
                'descripcion': 'HONORARIOS NOTARIALES',
                'valor_unitario': 1000.00,
                'importe': 1000.00,
                'objeto_imp': '02'
            }
        ],
        'subtotal': 1000.00,
        'total': 1160.00,
        # Notary Complement Data
        'complemento_notarios': {
            'num_escritura': 12345,
            'fecha_inst_notarial': '2023-10-27',
            'monto_operacion': 500000.00,
            'subtotal': 500000.00,
            'iva': 80000.00,
            'inmuebles': [
                {
                    'tipo_inmueble': '03',
                    'calle': 'Av. Audiencia',
                    'no_ext': '123',
                    'municipio': 'Manzanillo',
                    'estado': 'Colima',
                    'pais': 'MEX',
                    'cp': '28200'
                }
            ],
            'enajenantes': [
                {
                    'nombre': 'JUAN',
                    'apellido_paterno': 'PEREZ',
                    'rfc': 'PEPJ8001019Q8',
                    'curp': 'PEPJ800101HCLRRA01'
                }
            ],
            'adquirientes': [
                {
                    'nombre': 'MARIA',
                    'apellido_paterno': 'LOPEZ',
                    'rfc': 'LOMM850505ABC',
                    'curp': 'LOMM850505MCLZNA05'
                }
            ]
        }
    }

    xml_bytes = generate_signed_xml(invoice_data)

    # Assertions
    assert b'Version="4.0"' in xml_bytes
    assert b'NumNotaria="4"' in xml_bytes
    assert b'notariospublicos:NotariosPublicos' in xml_bytes
    assert b'DatosUnAdquiriente' in xml_bytes # Single buyer
    assert b'CoproSocConyugalE="No"' in xml_bytes

def test_generate_xml_coproperty_structure():
    invoice_data = {
        'receptor': {
            'rfc': 'XAXX010101000',
            'nombre': 'PUBLICO EN GENERAL',
            'uso_cfdi': 'S01',
            'domicilio_fiscal': '28200'
        },
        'conceptos': [
            {
                'clave_prod_serv': '84111506',
                'cantidad': 1,
                'clave_unidad': 'E48',
                'descripcion': 'HONORARIOS NOTARIALES',
                'valor_unitario': 2000.00,
                'importe': 2000.00,
                'objeto_imp': '02'
            }
        ],
        'subtotal': 2000.00,
        'total': 2320.00,
        'complemento_notarios': {
            'num_escritura': 54321,
            'fecha_inst_notarial': '2023-11-01',
            'monto_operacion': 1000000.00,
            'subtotal': 1000000.00,
            'iva': 160000.00,
            'inmuebles': [
                {
                    'tipo_inmueble': '03',
                    'calle': 'Blvd. Costero',
                    'no_ext': '555',
                    'municipio': 'Manzanillo',
                    'estado': 'Colima',
                    'pais': 'MEX',
                    'cp': '28200'
                }
            ],
            'enajenantes': [
                {'nombre': 'VENDEDOR A', 'rfc': 'AAAA800101AAA', 'curp': 'AAAA800101HCLRRA01', 'porcentaje': 50.00},
                {'nombre': 'VENDEDOR B', 'rfc': 'BBBB800101BBB', 'curp': 'BBBB800101HCLRRA01', 'porcentaje': 50.00}
            ],
            'adquirientes': [
                {'nombre': 'COMPRADOR X', 'rfc': 'XXXX900101XXX', 'curp': 'XXXX900101HCLRRA01', 'porcentaje': 50.00},
                {'nombre': 'COMPRADOR Y', 'rfc': 'YYYY900101YYY', 'curp': 'YYYY900101HCLRRA01', 'porcentaje': 50.00}
            ]
        }
    }

    xml_bytes = generate_signed_xml(invoice_data)

    assert b'CoproSocConyugalE="Si"' in xml_bytes
    assert b'DatosAdquirienteCopSC' in xml_bytes
    # Allow flexible decimal formatting (50, 50.0, 50.00)
    assert b'Porcentaje="50"' in xml_bytes or b'Porcentaje="50.0"' in xml_bytes or b'Porcentaje="50.00"' in xml_bytes

def test_persona_moral_retention():
    # Persona Moral RFC (12 chars)
    pm_rfc = "AAA010101AAA"
    invoice_data = {
        'receptor': {
            'rfc': pm_rfc,
            'nombre': 'EMPRESA SA DE CV',
            'uso_cfdi': 'G03',
            'domicilio_fiscal': '28200'
        },
        'conceptos': [
            {
                'clave_prod_serv': '84111506',
                'cantidad': 1,
                'clave_unidad': 'E48',
                'descripcion': 'HONORARIOS',
                'valor_unitario': 10000.00,
                'importe': 10000.00,
                'objeto_imp': '02' # Taxable
            }
        ],
        'subtotal': 10000.00,
        'total': 11600.00, # Before retentions logic in satcfdi
        # No complement for this test to focus on taxes
    }

    xml_bytes = generate_signed_xml(invoice_data)

    # Check for ISR Retention (10% of 10000 = 1000.00)
    assert b'Impuesto="001"' in xml_bytes
    # satcfdi might strip trailing zeros for 0.10
    assert b'TasaOCuota="0.10"' in xml_bytes or b'TasaOCuota="0.100000"' in xml_bytes
    assert b'Importe="1000.00"' in xml_bytes

    # Check for IVA Retention (2/3 of 1600 = 1066.67)
    assert b'Impuesto="002"' in xml_bytes
    assert b'TasaOCuota="0.106667"' in xml_bytes
    assert b'Importe="1066.67"' in xml_bytes
