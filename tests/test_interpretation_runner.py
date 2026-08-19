"""Tests for interpretation_runner.py."""

import dataclasses

from stock_analyst.analysis import calculations
from stock_analyst.analysis.calculated_values import CalculatedValues
from stock_analyst.analysis.interpretation_runner import interpret_calculated_values

_ZONE_FIELDS = {"altman_z_zone", "altman_z_double_prime_zone"}

_FIELD_NAMES = [field.name for field in dataclasses.fields(CalculatedValues)]


def test_interpret_calculated_values_covers_every_field_in_declaration_order():
    filled = CalculatedValues(
        **{name: (calculations.Z_SAFE if name in _ZONE_FIELDS else 1.0) for name in _FIELD_NAMES}
    )
    results = interpret_calculated_values(filled)
    assert [result.field_name for result in results] == _FIELD_NAMES
    assert all(result.raw_value is not None for result in results)
    assert all(result.interpretation for result in results)


def test_every_field_interpreted_when_nothing_was_computed():
    results = interpret_calculated_values(CalculatedValues())
    assert len(results) == len(_FIELD_NAMES)
    assert all(result.raw_value is None for result in results)
    assert all(result.falls_outside_normal_range is False for result in results)
    assert all(result.interpretation for result in results)
