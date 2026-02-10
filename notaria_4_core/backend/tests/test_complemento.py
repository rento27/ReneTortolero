import pytest
from decimal import Decimal
from datetime import date
import sys
import os

# Add backend to path so we can import lib
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lib.xml_generator import generate_complemento_notarios
from lib.fiscal_engine import validate_copropiedad

def test_validate_copropiedad_success():
    percentages = [Decimal("50.00"), Decimal("50.00")]
    assert validate_copropiedad(percentages) is True

def test_validate_copropiedad_failure():
    percentages = [Decimal("50.00"), Decimal("49.99")]
    with pytest.raises(ValueError):
        validate_copropiedad(percentages)

def test_generate_complemento_notarios_structure():
    data = {
        'datos_notario': {
            'num_notaria': 4,
            'entidad_federativa': '06',
            'adscripcion': 'MANZANILLO COLIMA',
            'curp': 'TOSR520601HCLRRNA1'
        },
        'datos_operacion': {
            'num_instrumento_notarial': 12345,
            'fecha_inst_notarial': date(2023, 10, 27),
            'monto_operacion': Decimal('1000000.00'),
            'subtotal': Decimal('10000.00'),
            'iva': Decimal('1600.00')
        },
        'desc_inmuebles': {
            'tipo_inmueble': '03',
            'calle': 'Av. Audiencia',
            'municipio': 'Manzanillo',
            'estado': 'Colima',
            'pais': 'MEX',
            'codigo_postal': '28200'
        },
        'datos_adquirientes': [
            {
                'nombre': 'Juan Perez',
                'rfc': 'XAXX010101000',
                'copro_soc_conyugal_e': 'Si',
                'porcentaje': Decimal('50.00')
            },
            {
                'nombre': 'Maria Lopez',
                'rfc': 'XAXX010101000',
                'copro_soc_conyugal_e': 'Si',
                'porcentaje': Decimal('50.00')
            }
        ],
        'datos_enajenantes': []
    }

    complemento = generate_complemento_notarios(data)
    assert complemento is not None

    # Verify XML tag
    assert 'NotariosPublicos' in complemento.tag

    # Verify content
    # satcfdi objects support dict-like access for children
    assert complemento['DatosNotario']['NumNotaria'] == 4

    # Verify Coproperty logic
    datos_adquiriente = complemento['DatosAdquiriente']
    assert datos_adquiriente['CoproSocConyugalE'] == 'Si'

    # Check nested CopSC
    # Note: satcfdi might handle list as list of objects
    cop_sc_list = datos_adquiriente['DatosAdquirientesCopSC']
    assert len(cop_sc_list) == 2
    assert cop_sc_list[0]['Porcentaje'] == Decimal('50.00')

def test_generate_complemento_invalid_coproperty():
    data = {
        'datos_notario': {
            'num_notaria': 4,
            'entidad_federativa': '06',
            'adscripcion': 'MANZANILLO COLIMA',
            'curp': 'TOSR520601HCLRRNA1'
        },
        'datos_operacion': {
            'num_instrumento_notarial': 12345,
            'fecha_inst_notarial': date(2023, 10, 27),
            'monto_operacion': Decimal('1000000.00'),
            'subtotal': Decimal('10000.00'),
            'iva': Decimal('1600.00')
        },
        'desc_inmuebles': {
            'tipo_inmueble': '03',
            'calle': 'Av. Audiencia',
            'municipio': 'Manzanillo',
            'estado': 'Colima',
            'pais': 'MEX',
            'codigo_postal': '28200'
        },
        'datos_adquirientes': [
            {
                'nombre': 'Juan Perez',
                'rfc': 'XAXX010101000',
                'copro_soc_conyugal_e': 'Si',
                'porcentaje': Decimal('50.00')
            },
            {
                'nombre': 'Maria Lopez',
                'rfc': 'XAXX010101000',
                'copro_soc_conyugal_e': 'Si',
                'porcentaje': Decimal('40.00') # Sum is 90%, should fail
            }
        ],
        'datos_enajenantes': []
    }

    with pytest.raises(ValueError, match="Sum of percentages must be 100.00%"):
        generate_complemento_notarios(data)
