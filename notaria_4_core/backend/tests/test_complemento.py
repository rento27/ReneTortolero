import pytest
from decimal import Decimal
from datetime import date, timedelta
from notaria_4_core.backend.lib.complement_notarios import create_complemento_notarios, split_name

def test_split_name():
    assert split_name("JUAN") == ("JUAN", "", "")
    assert split_name("JUAN PEREZ") == ("JUAN", "PEREZ", "")
    assert split_name("JUAN PEREZ GOMEZ") == ("JUAN", "PEREZ", "GOMEZ")
    assert split_name("MARIA DE LA LUZ LOPEZ PEREZ") == ("MARIA DE LA LUZ", "LOPEZ", "PEREZ")

def test_create_complemento_notarios_success_single():
    data = {
        'desc_inmuebles': [{
            'tipo_inmueble': '01',
            'calle': 'Av Principal',
            'municipio': 'Manzanillo',
            'estado': 'COL',
            'pais': 'MEX',
            'codigo_postal': '28200'
        }],
        'datos_operacion': {
            'num_instrumento_notarial': 12345,
            'fecha_inst_notarial': date.today(),
            'monto_operacion': 1000000.00,
            'subtotal': 10000.00,
            'iva': 1600.00
        },
        'datos_notario': {
            'curp': 'TOSR520601HOCMXA00',
            'num_notaria': 4,
            'entidad_federativa': '06',
            'adscripcion': 'MANZANILLO COLIMA'
        },
        'datos_enajenante': {
            'copro_soc_conyugal_e': 'No',
            'datos_un_enajenante': {
                'nombre': 'VENDEDOR UNO',
                'rfc': 'VEND123456789',
                'curp': 'VEND123456ABCDEF00'
            }
        },
        'datos_adquiriente': {
            'copro_soc_conyugal_e': 'No',
            'datos_un_adquiriente': {
                'nombre': 'COMPRADOR UNO',
                'rfc': 'COMP123456789',
                'curp': 'COMP123456ABCDEF00'
            }
        }
    }

    comp = create_complemento_notarios(data)
    assert comp is not None
    assert 'DescInmuebles' in comp
    assert 'DatosAdquiriente' in comp
    assert comp['DatosAdquiriente']['CoproSocConyugalE'] == 'No'

def test_create_complemento_notarios_success_copro():
    data = {
        'desc_inmuebles': [{
            'tipo_inmueble': '01',
            'calle': 'Av Principal',
            'municipio': 'Manzanillo',
            'estado': 'COL',
            'pais': 'MEX',
            'codigo_postal': '28200'
        }],
        'datos_operacion': {
            'num_instrumento_notarial': 12345,
            'fecha_inst_notarial': date.today(),
            'monto_operacion': 1000000.00,
            'subtotal': 10000.00,
            'iva': 1600.00
        },
        'datos_notario': {
            'curp': 'TOSR520601HOCMXA00',
            'num_notaria': 4,
            'entidad_federativa': '06',
            'adscripcion': 'MANZANILLO COLIMA'
        },
        'datos_enajenante': {
            'copro_soc_conyugal_e': 'No',
            'datos_un_enajenante': {
                'nombre': 'VENDEDOR UNO',
                'rfc': 'VEND123456789',
                'curp': 'VEND123456ABCDEF00'
            }
        },
        'datos_adquiriente': {
            'copro_soc_conyugal_e': 'Si',
            'datos_adquirientes_cop_sc': [
                {
                    'nombre': 'COMPRADOR UNO',
                    'rfc': 'COMP123456789',
                    'curp': 'COMP123456ABCDEF00',
                    'porcentaje': 50.00
                },
                {
                    'nombre': 'COMPRADOR DOS',
                    'rfc': 'COMP987654321',
                    'curp': 'COMP987654ABCDEF00',
                    'porcentaje': 50.00
                }
            ]
        }
    }

    comp = create_complemento_notarios(data)
    assert comp is not None
    assert 'DatosAdquiriente' in comp
    assert comp['DatosAdquiriente']['CoproSocConyugalE'] == 'Si'
    # Use dictionary access for testing as required by the AGENTS.md rules
    adquiriente = comp['DatosAdquiriente']
    assert 'DatosAdquirientesCopSC' in adquiriente
    assert len(adquiriente['DatosAdquirientesCopSC']) == 2

def test_create_complemento_notarios_fail_percentage():
    data = {
        'desc_inmuebles': [{
            'tipo_inmueble': '01',
            'calle': 'Av Principal',
            'municipio': 'Manzanillo',
            'estado': 'COL',
            'pais': 'MEX',
            'codigo_postal': '28200'
        }],
        'datos_operacion': {
            'num_instrumento_notarial': 12345,
            'fecha_inst_notarial': date.today(),
            'monto_operacion': 1000000.00,
            'subtotal': 10000.00,
            'iva': 1600.00
        },
        'datos_enajenante': {
            'copro_soc_conyugal_e': 'No',
            'datos_un_enajenante': {
                'nombre': 'VENDEDOR UNO',
                'rfc': 'VEND123456789',
                'curp': 'VEND123456ABCDEF00'
            }
        },
        'datos_adquiriente': {
            'copro_soc_conyugal_e': 'Si',
            'datos_adquirientes_cop_sc': [
                {
                    'nombre': 'COMPRADOR UNO',
                    'rfc': 'COMP123456789',
                    'curp': 'COMP123456ABCDEF00',
                    'porcentaje': 50.00
                },
                {
                    'nombre': 'COMPRADOR DOS',
                    'rfc': 'COMP987654321',
                    'curp': 'COMP987654ABCDEF00',
                    'porcentaje': 49.99
                }
            ]
        }
    }

    with pytest.raises(ValueError, match="Sum of percentages must be exactly 100.00%"):
        create_complemento_notarios(data)

def test_create_complemento_notarios_fail_future_date():
    future_date = date.today() + timedelta(days=1)
    data = {
        'desc_inmuebles': [],
        'datos_operacion': {
            'num_instrumento_notarial': 12345,
            'fecha_inst_notarial': future_date,
            'monto_operacion': 1000000.00,
            'subtotal': 10000.00,
            'iva': 1600.00
        },
        'datos_enajenante': {},
        'datos_adquiriente': {}
    }
    with pytest.raises(ValueError, match="FechaInstNotarial cannot be in the future"):
        create_complemento_notarios(data)
