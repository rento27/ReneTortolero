import os
import sys

# Ensure backend root is in sys.path so we can import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_create_cfdi_stub():
    # Set TEST_MODE if needed
    os.environ["TEST_MODE"] = "True"

    payload = {
        "receptor": {
            "rfc": "ABC123456789", # Persona Moral (12 chars)
            "nombre": "EMPRESA DE PRUEBA, S.A. DE C.V.",
            "codigo_postal": "28200",
            "regimen_fiscal": "601"
        },
        "conceptos": [
            {
                "clave_prod_serv": "80131500",
                "descripcion": "HONORARIOS",
                "valor_unitario": 1000.00,
                "cantidad": 1,
                "objeto_imp": "02",
                "clave_unidad": "E48"
            }
        ],
        "uso_cfdi": "G03"
    }
    response = client.post("/api/v1/cfdi", json=payload)

    # Debug info if fails
    if response.status_code != 200:
        print(response.json())

    assert response.status_code == 200

    data = response.json()["data"]

    # Check Sanitization
    assert data["sanitized_receptor_name"] == "EMPRESA DE PRUEBA"

    # Check Retentions (Moral)
    # Note: JSON response will use floats
    assert abs(data["retentions_applied"]["isr"] - 0.10) < 0.0001
    assert abs(data["retentions_applied"]["iva"] - 0.106667) < 0.0001
