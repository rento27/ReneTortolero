from decimal import Decimal
from notaria_4_core.backend.lib.xml_generator import generate_signed_xml

invoice_data = {
    'receptor': {
        'rfc': 'XAXX010101000',
        'nombre': 'PUBLICO EN GENERAL',
        'uso_cfdi': 'G03',
        'domicilio_fiscal': '28200'
    },
    'conceptos': [
        {
            'clave_prod_serv': '80121600',
            'cantidad': '1.0',
            'clave_unidad': 'E48',
            'descripcion': 'HONORARIOS',
            'valor_unitario': '1000.00',
            'importe': '1000.00',
            'objeto_imp': '02'
        }
    ],
    'subtotal': '1000.00',
    'total': '1160.00'
}

print(generate_signed_xml(invoice_data))
