import pytest
from decimal import Decimal
from notaria_4_core.backend.lib.complement_notarios import create_complemento_notarios
from notaria_4_core.backend.lib.api_models import ComplementoNotariosModel, DatosAdquiriente, DescInmueble

def test_copropiedad_sum_validation():
    # Helper to test exactly what the reviewer mentioned is missing
    data = {
        "version": "1.0",
        "fecha_inst_notarial": "2023-10-10",
        "desc_inmuebles": [
            {
                "tipo_inmueble": "03",
                "calle": "AV PRINCIPAL",
                "estado": "06",
                "municipio": "007",
                "pais": "MEX",
                "codigo_postal": "28200"
            }
        ],
        "datos_enajenantes": [],
        "datos_adquirientes": [
            {
                "copro_soc_conyugal_e": "Si",
                "nombre": "RUBEN",
                "apellido_paterno": "LOPEZ",
                "apellido_materno": "ANGUIANO",
                "rfc": "LOAR800101XYZ",
                "curp": "LOAR800101HCOLNZ00",
                "porcentaje": "50.00"
            },
            {
                "copro_soc_conyugal_e": "Si",
                "nombre": "MONICA",
                "apellido_paterno": "LEON",
                "apellido_materno": "GONZALEZ",
                "rfc": "LEGM800101XYZ",
                "curp": "LEGM800101MCOLNZ00",
                "porcentaje": "49.90" # Intentionally wrong sum
            }
        ]
    }

    model = ComplementoNotariosModel(**data)
    with pytest.raises(ValueError, match="Sum of adquiriente coproperty percentages must be exactly 100.00%, got 99.90%"):
        create_complemento_notarios(model)
