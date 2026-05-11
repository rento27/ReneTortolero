from decimal import Decimal
from unittest.mock import patch
import pytest
import notaria_4_core.backend.lib.fiscal_engine as fiscal_engine

class DummyParameter:
    def __init__(self, value):
        self.default_value = DummyValue(value)

class DummyValue:
    def __init__(self, value):
        self.value = value

class DummyTemplate:
    def __init__(self, parameters):
        self.parameters = parameters

@pytest.fixture(autouse=True)
def clear_cache():
    fiscal_engine._ISAI_RATE_CACHE = None
    fiscal_engine._ISAI_RATE_CACHE_TIME = 0

@patch("notaria_4_core.backend.lib.fiscal_engine.get_remote_config_sync")
def test_calculate_isai_manzanillo_custom_rate(mock_get_remote_config):
    # Set mock to return a custom rate of 0.05
    mock_get_remote_config.return_value = DummyTemplate(
        parameters={'tasa_isai_manzanillo': DummyParameter("0.05")}
    )

    price = Decimal("1000000.00")
    cadastral = Decimal("500000.00")

    isai = fiscal_engine.calculate_isai_manzanillo(price, cadastral)
    assert isai == Decimal("50000.00")

@patch("notaria_4_core.backend.lib.fiscal_engine.get_remote_config_sync")
def test_calculate_isai_manzanillo_default_rate_when_missing(mock_get_remote_config):
    # Template without tasa_isai_manzanillo
    mock_get_remote_config.return_value = DummyTemplate(parameters={})

    price = Decimal("1000000.00")
    cadastral = Decimal("500000.00")

    isai = fiscal_engine.calculate_isai_manzanillo(price, cadastral)
    assert isai == Decimal("30000.00")
