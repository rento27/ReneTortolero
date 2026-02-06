from fastapi.testclient import TestClient
from main import app
from decimal import Decimal

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "notaria-4-core-backend"}

def test_calculate_isai():
    # Max(1000000, 800000) * 0.03 = 30000
    payload = {
        "precio_operacion": 1000000,
        "valor_catastral": 800000,
        "tasa": 0.03
    }
    response = client.post("/api/v1/calculate-isai", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["base_used"] == 1000000.0
    assert data["isai_amount"] == 30000.00
