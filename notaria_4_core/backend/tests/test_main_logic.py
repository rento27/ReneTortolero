import sys
import os
from unittest.mock import MagicMock, patch
from decimal import Decimal

# Add backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Mock satcfdi modules to avoid ImportErrors if not installed
sys.modules['satcfdi'] = MagicMock()
sys.modules['satcfdi.create'] = MagicMock()
sys.modules['satcfdi.create.cfd'] = MagicMock()
sys.modules['satcfdi.models'] = MagicMock()

from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_create_cfdi_mixed_items_retention_logic():
    # Patch the generate_signed_xml function imported in main
    with patch('main.generate_signed_xml', return_value=b'<xml>signed</xml>') as mock_gen:

        payload = {
            "receptor": {
                "rfc": "AAA010101AAA", # Moral (12 chars)
                "nombre": "EMPRESA X",
                "uso_cfdi": "G03",
                "domicilio_fiscal": "28200"
            },
            "conceptos": [
                {
                    "clave_prod_serv": "84111506",
                    "cantidad": 1,
                    "clave_unidad": "E48",
                    "descripcion": "HONORARIOS",
                    "valor_unitario": 1000.00,
                    "importe": 1000.00,
                    "objeto_imp": "02" # Taxable
                },
                {
                    "clave_prod_serv": "84111506",
                    "cantidad": 1,
                    "clave_unidad": "E48",
                    "descripcion": "GASTOS",
                    "valor_unitario": 500.00,
                    "importe": 500.00,
                    "objeto_imp": "01" # Non-Taxable
                }
            ],
            "subtotal": 1500.00,
            "total": 1660.00
        }

        response = client.post("/api/v1/cfdi", json=payload)

        if response.status_code != 200:
            print(f"Response Error: {response.text}")

        assert response.status_code == 200
        data = response.json()

        # Verify Retentions Calculation
        # Taxable Base = 1000 (only first item)
        # ISR = 1000 * 0.10 = 100.00
        # IVA Ret = 1000 * 0.16 * 2/3 = 106.67 (approx)

        retentions = data['retentions_calculated']

        # Convert to float for comparison or string
        # FastAPI default JSON encoder converts Decimal to float or str depending on config.
        # Let's see what we get.

        print(f"Retentions received: {retentions}")

        # We expect 100.00 and 106.67
        # Note: If logic was wrong (using 1500 base), ISR would be 150.00

        # Check ISR
        # Pydantic might return float 100.0
        assert float(retentions['isr']) == 100.00

        # Check IVA
        # 106.67
        assert abs(float(retentions['iva']) - 106.67) < 0.01

        assert retentions['is_moral'] == True

        print("Test Passed: Mixed items retention logic is correct.")

if __name__ == "__main__":
    test_create_cfdi_mixed_items_retention_logic()
