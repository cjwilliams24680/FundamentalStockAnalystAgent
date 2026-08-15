"""Helpers for cleaning markdown tables extracted from quarterly report PDFs."""

import re

_PARENTHESIZED_NUMBER_PATTERN = re.compile(r"\((\d[\d,]*(?:\.\d+)?)\)")

_DASH_ONLY_TABLE_CELL_PATTERN = re.compile(r"(?<=\|)(\s*)[‒–—―−]+(\s*)(?=\|)")


def replace_parenthesized_numbers_with_negative_values(text: str) -> str:
    """Rewrite accounting-style parenthesized numbers as negative numbers.

    Financial filings write negative values in parentheses, e.g. ``(1704.5)``
    for ``-1704.5``. Replaces every parenthesized number in ``text`` with the
    same number prefixed by a minus sign; thousands separators are preserved,
    so ``(1,704.5)`` becomes ``-1,704.5``. Parenthesized text that is not a
    number, e.g. ``(word)``, is left unchanged.
    """
    return _PARENTHESIZED_NUMBER_PATTERN.sub(r"-\1", text)


def replace_dash_only_table_cells_with_zero_values(text: str) -> str:
    """Rewrite markdown table cells containing only a long dash as ``0.0``.

    Financial filings write a zero value as a long dash (usually an em dash).
    Replaces the content of any markdown table cell that consists solely of
    one or more Unicode dashes (figure dash, en dash, em dash, horizontal
    bar, or minus sign) with ``0.0``. ASCII hyphens are deliberately not
    matched, so markdown separator rows like ``| --- |`` and hyphenated text
    are never altered; dashes embedded in other cell text are also left alone.
    """
    return _DASH_ONLY_TABLE_CELL_PATTERN.sub(r"\g<1>0.0\g<2>", text)
