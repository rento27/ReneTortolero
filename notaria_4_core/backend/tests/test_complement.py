import pytest
from decimal import Decimal
from notaria_4_core.backend.lib.api_models import ComplementoNotariosModel
from notaria_4_core.backend.lib.complement_notarios import create_complemento_notarios

def test_create_complement():
    data = {
        "fecha_inst_notarial": "2023-10-01",
        "desc_inmuebles": [
            {
                "tipo_inmueble": "03",
                "calle": "Av Siempre Viva 123",
                "municipio": "Manzanillo",
                "estado": "COL",
                "codigo_postal": "28200"
            }
        ],
        "datos_enajenantes": [
            {
                "copro_soc_conyugal_e": "Si",
                "nombre": "JUAN PEREZ",
                "rfc": "PEAJ900101XYZ",
                "curp": "PEAJ900101HOCMXA00",
                "porcentaje": "100.00"
            }
        ],
        "datos_adquirientes": [
            {
                "copro_soc_conyugal_e": "No",
                "nombre": "MARIA LOPEZ",
                "rfc": "LOMM900101XYZ",
                "curp": "LOMM900101HOCMXA00"
            }
        ]
    }
    model = ComplementoNotariosModel(**data)
    comp = create_complemento_notarios(model)
    assert comp is not None
