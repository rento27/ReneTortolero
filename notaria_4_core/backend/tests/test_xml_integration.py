from decimal import Decimal
import pytest
from notaria_4_core.backend.lib.xml_generator import generate_signed_xml
from notaria_4_core.backend.lib.api_models import InvoiceRequest, Receptor, Concepto, DatosNotarioModel, DatosOperacionModel, DescInmuebleModel, DatosEnajenanteModel, DatosUnEnajenanteModel, DatosAdquirienteModel, DatosUnAdquirienteModel, ComplementoNotariosModel
from datetime import date

def test_full_xml_generation_with_complement():
    """Test generating a full XML with Notarios Complement."""

    # Construct request data (simulating model_dump() output)
    data = {
        'receptor': {
            'rfc': 'XAXX010101000',
            'nombre': 'CLIENTE GENERAL',
            'uso_cfdi': 'G03',
            'domicilio_fiscal': '28200'
        },
        'conceptos': [
            {
                'clave_prod_serv': '80131600',
                'cantidad': 1,
                'clave_unidad': 'E48',
                'descripcion': 'HONORARIOS',
                'valor_unitario': 1000.00,
                'importe': 1000.00,
                'objeto_imp': '02'
            }
        ],
        'subtotal': 1000.00,
        'total': 1160.00,
        'complemento_notarios': {
            'datos_notario': {'curp': 'CURPNOTARIO1234567'},
            'datos_operacion': {
                'num_instrumento_notarial': 999,
                'fecha_inst_notarial': date(2023, 10, 1),
                'monto_operacion': 500000.00,
                'subtotal': 1000.00,
                'iva': 160.00
            },
            'desc_inmuebles': [{
                'tipo_inmueble': '01',
                'calle': 'Calle Test',
                'municipio': 'Manzanillo',
                'estado': 'Colima',
                'codigo_postal': '28200',
                'pais': 'MEX'
            }],
            'datos_enajenante': {
                'copro_soc_conyugal_e': 'No',
                'datos_un_enajenante': {
                    'nombre': 'VEND',
                    'apellido_paterno': 'P',
                    'rfc': 'XAXX010101000',
                    'curp': 'XAXX010101HXXXXX00'
                }
            },
            'datos_adquiriente': {
                'copro_soc_conyugal_e': 'No',
                'datos_un_adquiriente': {
                    'nombre': 'ADQ',
                    'rfc': 'XAXX010101000'
                }
            }
        }
    }

    # Generate XML
    xml_bytes = generate_signed_xml(data)
    assert xml_bytes.startswith(b'<?xml')
    assert b'Complemento' in xml_bytes
    assert b'notariospublicos:NotariosPublicos' in xml_bytes
