from decimal import Decimal
import pytest
from ..lib.xml_generator import generar_factura, generar_complemento_notarios

@pytest.fixture
def mock_invoice_data():
    return {
        'Emisor': {'Rfc': 'TOSR520601AZ4', 'Nombre': 'RENÉ MANUEL TORTOLERO SANTILLANA', 'RegimenFiscal': '612'},
        'Receptor': {'Rfc': 'XAXX010101000', 'Nombre': 'PUBLICO EN GENERAL', 'UsoCFDI': 'S01', 'DomicilioFiscalReceptor': '28200', 'RegimenFiscalReceptor': '616'},
        'Conceptos': [
            {'ClaveProdServ': '80131600', 'Cantidad': Decimal('1'), 'ClaveUnidad': 'E48', 'Descripcion': 'Honorarios Notariales', 'ValorUnitario': Decimal('10000.00'), 'Importe': Decimal('10000.00'), 'ObjetoImp': '02'}
        ],
        'Subtotal': '10000.00',
        'Total': '11600.00',
        'Moneda': 'MXN',
        'FormaPago': '03',
        'MetodoPago': 'PUE',
        'LugarExpedicion': '28200'
    }

@pytest.fixture
def mock_complement_data():
    return {
        'DatosNotario': {
            'NumNotaria': 4,
            'EntidadFederativa': '06', # Colima
            'Adscripcion': 'MANZANILLO COLIMA',
            'CURP': 'TOSR520601HCLRNR05'
        },
        'DatosOperacion': {
            'NumInstrumentoNotarial': 12345,
            'FechaInstNotarial': '2025-01-01',
            'MontoOperacion': '1000000.00',
            'Subtotal': '10000.00',
            'IVA': '1600.00'
        },
        'DescInmuebles': {
            'TipoInmueble': '03', # Casa Habitacion
            'Calle': 'Av. Principal 100',
            'Municipio': '007', # Manzanillo
            'Estado': '06', # Colima
            'Pais': 'MEX',
            'CodigoPostal': '28200'
        },
        'DatosAdquirientes': [
            {
                'Nombre': 'JUAN',
                'ApellidoPaterno': 'PEREZ',
                'RFC': 'XAXX010101000',
                'DatosAdquirientesCopSC': {
                    'Nombre': 'JUAN',
                    'ApellidoPaterno': 'PEREZ',
                    'RFC': 'XAXX010101000',
                    'Porcentaje': '50.00'
                }
            },
            {
                'Nombre': 'MARIA',
                'ApellidoPaterno': 'LOPEZ',
                'RFC': 'XAXX010101000',
                'DatosAdquirientesCopSC': {
                    'Nombre': 'MARIA',
                    'ApellidoPaterno': 'LOPEZ',
                    'RFC': 'XAXX010101000',
                    'Porcentaje': '50.00'
                }
            }
        ],
        'DatosEnajenantes': [
            {
                'Nombre': 'PEDRO',
                'ApellidoPaterno': 'RAMIREZ',
                'RFC': 'XAXX010101000',
                'CURP': 'XAXX010101HCLRNR05'
            }
        ]
    }

def test_generar_complemento_structure(mock_complement_data):
    comp = generar_complemento_notarios(mock_complement_data)
    # satcfdi objects behave like dicts but keys are PascalCase
    assert comp['Version'] == '1.0'
    assert comp['DatosNotario']['NumNotaria'] == 4

def test_generar_complemento_invalid_sum(mock_complement_data):
    # Modify the first adquiriendo percentage
    mock_complement_data['DatosAdquirientes'][0]['DatosAdquirientesCopSC']['Porcentaje'] = '40.00'
    # Sum is now 90.00
    with pytest.raises(ValueError, match="La suma de porcentajes de copropiedad .* no es 100.00%"):
        generar_complemento_notarios(mock_complement_data)

def test_generar_factura_xml(mock_invoice_data, mock_complement_data):
    cfdi = generar_factura(mock_invoice_data, mock_complement_data)

    # Verify basic structure
    assert cfdi['Version'] == '4.0'
    assert cfdi['Emisor']['Rfc'] == 'TOSR520601AZ4'

    # Verify Complemento exists
    # satcfdi puts complement in 'Complemento' list usually
    assert 'Complemento' in cfdi
    # Depending on satcfdi version, it might be a list or object wrapper.
    # We just check it's not empty/None
    assert cfdi['Complemento'] is not None

    # Verify Retentions were not added for Generic RFC (XAXX...)
    # Impuestos node should not have Retenciones
    assert 'Retenciones' not in cfdi['Impuestos']

def test_generar_factura_xml_persona_moral(mock_invoice_data):
    # Change Receptor to Moral RFC (12 chars)
    mock_invoice_data['Receptor']['Rfc'] = 'ABC123456T12'

    cfdi = generar_factura(mock_invoice_data)

    impuestos = cfdi['Impuestos']
    assert 'Retenciones' in impuestos
    # Check retentions exist
    # It might be a list of dicts or object that supports __getitem__
    # satcfdi objects allow key access
    ret_list = impuestos['Retenciones']
    assert len(ret_list) == 2

    # Check values (Subtotal 10000 -> ISR 1000)
    # SatCFDI objects can be accessed by key
    isr_ret = next(r for r in ret_list if r['Impuesto'] == '001')
    assert isr_ret['Importe'] == Decimal('1000.00')
