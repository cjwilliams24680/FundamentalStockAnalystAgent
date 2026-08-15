"""Tests for table_parsing.py."""

from table_parsing import (
    replace_dash_only_table_cells_with_zero_values,
    replace_parenthesized_numbers_with_negative_values,
)


def test_parenthesized_decimal_number_becomes_negative():
    assert replace_parenthesized_numbers_with_negative_values("(1704.5)") == "-1704.5"


def test_parenthesized_integer_becomes_negative():
    assert replace_parenthesized_numbers_with_negative_values("(607)") == "-607"


def test_thousands_separators_are_preserved():
    assert replace_parenthesized_numbers_with_negative_values("(1,704.5)") == "-1,704.5"


def test_non_numeric_parentheses_are_left_unchanged():
    assert replace_parenthesized_numbers_with_negative_values("(word)") == "(word)"
    assert replace_parenthesized_numbers_with_negative_values("(note 1)") == "(note 1)"
    assert replace_parenthesized_numbers_with_negative_values("()") == "()"


def test_text_without_parentheses_is_left_unchanged():
    assert replace_parenthesized_numbers_with_negative_values("1704.5") == "1704.5"
    assert replace_parenthesized_numbers_with_negative_values("") == ""


def test_all_numbers_in_a_markdown_table_row_are_replaced():
    row = "| Revenue | (607) | (1,704.5) |"
    expected = "| Revenue | -607 | -1,704.5 |"
    assert replace_parenthesized_numbers_with_negative_values(row) == expected


def test_only_numeric_parentheses_change_in_mixed_text():
    text = "Net loss (see note 4) was (12.3) this quarter"
    expected = "Net loss (see note 4) was -12.3 this quarter"
    assert replace_parenthesized_numbers_with_negative_values(text) == expected


def test_em_dash_only_cell_becomes_zero():
    assert replace_dash_only_table_cells_with_zero_values("| — |") == "| 0.0 |"


def test_adjacent_dash_only_cells_are_both_replaced():
    row = "| Revenue | — | — |"
    expected = "| Revenue | 0.0 | 0.0 |"
    assert replace_dash_only_table_cells_with_zero_values(row) == expected


def test_separator_rows_are_left_unchanged():
    assert replace_dash_only_table_cells_with_zero_values("| --- | --- |") == "| --- | --- |"
    assert replace_dash_only_table_cells_with_zero_values("|:---|---:|") == "|:---|---:|"


def test_dashes_embedded_in_cell_text_are_left_unchanged():
    assert replace_dash_only_table_cells_with_zero_values("| 2023—2024 |") == "| 2023—2024 |"


def test_lone_ascii_hyphen_cell_is_left_unchanged():
    assert replace_dash_only_table_cells_with_zero_values("| - |") == "| - |"  # not a long dash


def test_dash_outside_a_table_is_left_unchanged():
    assert replace_dash_only_table_cells_with_zero_values("revenue was —") == "revenue was —"


def test_both_replacements_compose_on_a_realistic_row():
    row = "| Net income | (1,704.5) | — |"
    cleaned = replace_dash_only_table_cells_with_zero_values(
        replace_parenthesized_numbers_with_negative_values(row)
    )
    assert cleaned == "| Net income | -1,704.5 | 0.0 |"
