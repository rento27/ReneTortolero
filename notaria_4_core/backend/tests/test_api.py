from fastapi.testclient import TestClient
import os

# Mock environment for tests BEFORE importing app
os.environ["TEST_MODE"] = "True"

from notaria_4_core.backend.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Notaria 4 Digital Core API is running"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_create_cfdi_endpoint():
    payload = {
        "invoice_data": {
            "receptor": {
                "rfc": "XAXX010101000",
                "razon_social": "Client Name",
                "uso_cfdi": "S01",
                "cp": "28219",
                "regimen_fiscal": "616"
            },
            "conceptos": [
                {
                    "clave_prod_serv": "80131600",
                    "cantidad": 1.0,
                    "clave_unidad": "E48",
                    "descripcion": "Service",
                    "valor_unitario": 100.0,
                    "importe": 100.0,
                    "objeto_imp": "02"
                }
            ],
            "forma_pago": "03",
            "metodo_pago": "PUE"
        },
        "notary_data": {
            "inmueble": {
                "tipo": "03",
                "calle": "Street",
                "municipio": "Mun",
                "estado": "Est",
                "cp": "12345"
            },
            "operacion": {
                "num_instrumento": "100",
                "fecha_instrumento": "2023-01-01",
                "monto": 200.0,
                "subtotal": 100.0,
                "iva": 16.0
            },
            "notario": {
                "curp": "AAAA010101HCOLXX00",
                "numero": 4,
                "entidad": "06",
                "adscripcion": "Manzanillo"
            },
            "adquirientes": []
        }
    }

    response = client.post("/api/v1/cfdi", json=payload)
    if response.status_code != 200:
        print(response.json())

    assert response.status_code == 200
    data = response.json()
    assert "xml_base64" in data
    assert data["status"] == "signed"
