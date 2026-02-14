import pytest
import sys
import os
from datetime import date, timedelta
from decimal import Decimal

# Ensure backend is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.api_models import ComplementoNotariosModel, DatosNotario, DatosOperacion, DescInmueble, DatosAdquiriente, DatosEnajenante
from lib.complement_notarios import create_complemento_notarios, validate_coproperty_sum, validate_date_not_future

def test_validate_coproperty_sum():
    percentages = [Decimal("50.00"), Decimal("50.00")]
    validate_coproperty_sum(percentages) # Should pass

    with pytest.raises(ValueError):
        validate_coproperty_sum([Decimal("50.00"), Decimal("49.99")])

def test_validate_date_not_future():
    today = date.today()
    validate_date_not_future(today) # Should pass

    future = today + timedelta(days=1)
    with pytest.raises(ValueError):
        validate_date_not_future(future)

def test_create_complemento_notarios_coproperty():
    data = ComplementoNotariosModel(
        datos_notario=DatosNotario(),
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=12345,
            fecha_inst_notarial=date.today(),
            monto_operacion=Decimal("1000000.00"),
            subtotal=Decimal("10000.00"),
            iva=Decimal("1600.00")
        ),
        desc_inmuebles=[
            DescInmueble(
                tipo_inmueble="01",
                calle="Av. Mexico",
                municipio="Manzanillo",
                estado="Colima",
                codigo_postal="28200"
            )
        ],
        datos_adquirientes=[
            DatosAdquiriente(
                nombre="JUAN PEREZ",
                rfc="PEcJ800101XYZ",
                porcentaje=Decimal("50.00"),
                copro_soc_conyugal_e="Si"
            ),
            DatosAdquiriente(
                nombre="MARIA LOPEZ",
                rfc="LOMM800101ABC",
                porcentaje=Decimal("50.00"),
                copro_soc_conyugal_e="Si"
            )
        ],
        datos_enajenantes=[
            DatosEnajenante(
                nombre="PEDRO RAMIREZ",
                rfc="RAPP800101DEF",
                copro_soc_conyugal_e="No"
            )
        ]
    )

    complement = create_complemento_notarios(data)
    assert complement is not None

    # satcfdi objects act as dicts with PascalCase keys
    assert complement['DatosNotario']['NumNotaria'] == 4

    # Check Coproperty structure
    adqs = complement['DatosAdquiriente']
    assert adqs['CoproSocConyugalE'] == 'Si'

    # In satcfdi v4 (based on print output), the plural container key maps directly to the list of items
    items = adqs['DatosAdquirientesCopSC']

    assert isinstance(items, list)
    assert len(items) == 2

    # Check Name Splitting Fallback
    # JUAN PEREZ -> JUAN, PEREZ, ''
    # Note: satcfdi might use PascalCase keys for items
    assert items[0]['Nombre'] == 'JUAN'
    assert items[0]['ApellidoPaterno'] == 'PEREZ'

def test_validation_no_coproperty_multiple_items():
    data = ComplementoNotariosModel(
        datos_notario=DatosNotario(),
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=123,
            fecha_inst_notarial=date.today(),
            monto_operacion=Decimal("100"),
            subtotal=Decimal("10"),
            iva=Decimal("1.6")
        ),
        desc_inmuebles=[DescInmueble(tipo_inmueble="01", calle="x", municipio="x", estado="x", codigo_postal="00000")],
        datos_adquirientes=[
            DatosAdquiriente(nombre="A", rfc="AAA010101AAA", copro_soc_conyugal_e="No"),
            DatosAdquiriente(nombre="B", rfc="BBB010101BBB", copro_soc_conyugal_e="No")
        ],
        datos_enajenantes=[DatosEnajenante(nombre="C", rfc="CCC010101CCC", copro_soc_conyugal_e="No")]
    )

    with pytest.raises(ValueError, match="multiple DatosAdquirientes provided"):
        create_complemento_notarios(data)
