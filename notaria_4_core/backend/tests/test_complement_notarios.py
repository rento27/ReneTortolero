import pytest
import os
from decimal import Decimal
from notaria_4_core.backend.lib.api_models import ComplementoNotariosModel
from notaria_4_core.backend.lib.complement_notarios import create_complemento_notarios

def test_complemento_notarios():
    model = ComplementoNotariosModel(
        fecha_inst_notarial="2023-10-10",
        desc_inmuebles=[{
            "tipo_inmueble": "03",
            "calle": "Av Siempre Viva",
            "municipio": "001",
            "estado": "06",
            "pais": "MEX",
            "codigo_postal": "28200"
        }],
        datos_enajenantes=[{
            "copro_soc_conyugal_e": "Si",
            "nombre": "JUAN",
            "apellido_paterno": "PEREZ",
            "apellido_materno": "LOPEZ",
            "rfc": "PELJ801010AAA",
            "curp": "PELJ801010HOCMXA00",
            "porcentaje": "100.00"
        }],
        datos_adquirientes=[{
            "copro_soc_conyugal_e": "No",
            "nombre": "MARIA",
            "apellido_paterno": "GOMEZ",
            "apellido_materno": "PEREZ",
            "rfc": "GOPM801010AAA",
            "curp": "GOPM801010HOCMXA00"
        }]
    )
    comp = create_complemento_notarios(model)
    assert comp is not None
