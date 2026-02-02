from fastapi.testclient import TestClient
from ..main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "Notaria 4 Digital Core"}

def test_create_cfdi_endpoint():
    # Minimal valid payload
    payload = {
        "datos_factura": {
            'Emisor': {'Rfc': 'TOSR520601AZ4', 'Nombre': 'RENÉ MANUEL TORTOLERO SANTILLANA', 'RegimenFiscal': '612'},
            'Receptor': {'Rfc': 'XAXX010101000', 'Nombre': 'PUBLICO EN GENERAL', 'UsoCFDI': 'S01', 'DomicilioFiscalReceptor': '28200', 'RegimenFiscalReceptor': '616'},
            'Conceptos': [
                {'ClaveProdServ': '80131600', 'Cantidad': '1', 'ClaveUnidad': 'E48', 'Descripcion': 'Honorarios Notariales', 'ValorUnitario': '10000.00', 'Importe': '10000.00', 'ObjetoImp': '02'}
            ],
            'Subtotal': '10000.00',
            'Total': '11600.00',
            'Moneda': 'MXN',
            'FormaPago': '03',
            'MetodoPago': 'PUE',
            'LugarExpedicion': '28200'
        }
    }

    response = client.post("/api/v1/cfdi", json=payload)
    if response.status_code != 200:
        print(response.json())

    assert response.status_code == 200
    data = response.json()
    assert "xml" in data
    assert "Version=\"4.0\"" in data["xml"]
