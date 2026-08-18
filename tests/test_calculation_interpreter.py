"""Tests for calculation_interpreter.py."""

from stock_analyst import metrics
from stock_analyst.calculated_metrics import CalculatedValues
from stock_analyst.calculation_interpreter import interpret_all_calculations

_ZONE_FIELDS = {"altman_z_zone", "altman_z_double_prime_zone"}


def test_interpret_all_calculations_covers_every_field_in_declaration_order():
    filled = CalculatedValues(
        **{
            name: (metrics.Z_SAFE if name in _ZONE_FIELDS else 1.0)
            for name in CalculatedValues.model_fields
        }
    )
    results = interpret_all_calculations(filled)
    assert [result.field_name for result in results] == list(CalculatedValues.model_fields)
    assert all(result.raw_value is not None for result in results)
    assert all(result.interpretation for result in results)


def test_every_field_interpreted_when_nothing_was_computed():
    results = interpret_all_calculations(CalculatedValues())
    assert len(results) == len(CalculatedValues.model_fields)
    assert all(result.raw_value is None for result in results)
    assert all(result.falls_outside_normal_range is False for result in results)
    assert all(result.interpretation for result in results)
