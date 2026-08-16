"""Tests for calculation_interpreter.py."""

import metrics
from calculated_metrics import CalculatedMetrics
from calculation_interpreter import interpret_all_calculations

_ZONE_FIELDS = {"altman_z_zone", "altman_z_double_prime_zone"}


def test_interpret_all_calculations_covers_every_field_in_declaration_order():
    filled = CalculatedMetrics(
        **{
            name: (metrics.Z_SAFE if name in _ZONE_FIELDS else 1.0)
            for name in CalculatedMetrics.model_fields
        }
    )
    results = interpret_all_calculations(filled)
    assert [result.field_name for result in results] == list(CalculatedMetrics.model_fields)
    assert all(result.raw_value is not None for result in results)
    assert all(result.interpretation for result in results)


def test_every_field_interpreted_when_nothing_was_computed():
    results = interpret_all_calculations(CalculatedMetrics())
    assert len(results) == len(CalculatedMetrics.model_fields)
    assert all(result.raw_value is None for result in results)
    assert all(result.falls_outside_normal_range is False for result in results)
    assert all(result.interpretation for result in results)
