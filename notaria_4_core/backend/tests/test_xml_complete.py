from lib.xml_generator import generate_signed_xml
from decimal import Decimal
from datetime import date
import pytest
from lxml import etree

def test_generate_xml_simple_pm():
    """Test simple invoice for Persona Moral (Retentions)"""
    data = {
        'receptor': {
            'rfc': 'XAXX010101000', # 13 chars = PF (No retentions) -> Wait, 12 chars = PM
            'nombre': 'EMPRESA PM',
            'uso_cfdi': 'G03',
            'domicilio_fiscal': '28200'
        },
        'conceptos': [
            {
                'clave_prod_serv': '84111506',
                'cantidad': 1,
                'clave_unidad': 'E48',
                'descripcion': 'HONORARIOS',
                'valor_unitario': 1000,
                'importe': 1000,
                'objeto_imp': '02'
            }
        ],
        'subtotal': 1000,
        'total': 1160, # 1000 + 160 IVA - 0 Ret
        'copropietarios': None,
        'complemento_notarios': None
    }

    # Test 1: Persona Fisica (13 chars) - No Retentions
    xml_bytes = generate_signed_xml(data)
    root = etree.fromstring(xml_bytes)
    ns = {'cfdi': 'http://www.sat.gob.mx/cfd/4'}

    impuestos = root.find('cfdi:Impuestos', ns)
    # Should have Traslados but NO Retenciones
    assert impuestos is not None
    assert impuestos.find('cfdi:Retenciones', ns) is None
    assert float(impuestos.get('TotalImpuestosTrasladados')) == 160.0

    # Test 2: Persona Moral (12 chars) - Retentions
    data['receptor']['rfc'] = 'AAA010101AAA' # 12 chars
    xml_bytes = generate_signed_xml(data)
    root = etree.fromstring(xml_bytes)

    impuestos = root.find('cfdi:Impuestos', ns)
    assert impuestos.find('cfdi:Retenciones', ns) is not None
    # 10% ISR (100) + 10.6667% IVA (106.67) = 206.67
    total_ret = float(impuestos.get('TotalImpuestosRetenidos'))
    assert abs(total_ret - 206.67) < 0.01

def test_generate_xml_with_complement():
    """Test invoice with Notary Complement"""
    data = {
        'receptor': {
            'rfc': 'XAXX010101000',
            'nombre': 'JUAN PEREZ',
            'uso_cfdi': 'G03',
            'domicilio_fiscal': '28200'
        },
        'conceptos': [{'clave_prod_serv': '84111506', 'cantidad': 1, 'clave_unidad': 'E48', 'descripcion': 'HON', 'valor_unitario': 1000, 'importe': 1000, 'objeto_imp': '02'}],
        'subtotal': 1000,
        'total': 1160,
        'copropietarios': None,
        'complemento_notarios': {
            'num_instrumento': 12345,
            'fecha_inst_notarial': date(2023, 10, 27),
            'monto_operacion': 500000,
            'subtotal_operacion': 500000,
            'iva_operacion': 0,
            'inmuebles': [
                {
                    'tipo_inmueble': '03',
                    'calle': 'AVE MEXICO',
                    'no_exterior': '10',
                    'codigo_postal': '28200',
                    'municipio': 'MANZANILLO',
                    'estado': 'COL',
                    'pais': 'MEX'
                }
            ],
            'enajenantes': [
                {
                    'nombre': 'PEDRO VENDEDOR',
                    'rfc': 'XAXX010101000',
                    'curp': 'AAAA010101HCOLXX00',
                    'es_copropiedad': False
                }
            ]
        }
    }

    xml_bytes = generate_signed_xml(data)
    root = etree.fromstring(xml_bytes)
    ns = {'cfdi': 'http://www.sat.gob.mx/cfd/4', 'notariospublicos': 'http://www.sat.gob.mx/notariospublicos'}

    complemento = root.find('cfdi:Complemento', ns)
    assert complemento is not None

    notarios = complemento.find('.//notariospublicos:NotariosPublicos', ns)
    # Check if namespace mapping works, otherwise try wildcard or local-name
    if notarios is None:
        # Sometimes lxml needs explicit ns map usage or the prefix is different in output
        # Let's check tag
        found = False
        for child in complemento:
            if 'NotariosPublicos' in child.tag:
                found = True
                break
        assert found
