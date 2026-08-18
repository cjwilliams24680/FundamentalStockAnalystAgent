"""Helpers for cleaning markdown tables extracted from quarterly report PDFs."""

import asyncio
import re
from enum import StrEnum

from langchain.agents import create_agent
from pydantic import BaseModel, Field

from stock_analyst.end_of_financial_period_parser import EarningsPeriodInfo
from stock_analyst.llm_provider import DEFAULT_MODEL

_PARENTHESIZED_NUMBER_PATTERN = re.compile(r"\((\d[\d,]*(?:\.\d+)?)\)")

# The character class intentionally lists the Unicode dash variants filers use
# to mean zero (figure dash, en dash, em dash, horizontal bar, minus sign).
_DASH_ONLY_TABLE_CELL_PATTERN = re.compile(r"(?<=\|)(\s*)[‒–—―−]+(\s*)(?=\|)")  # noqa: RUF001


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


class FinancialStatementUnitScale(StrEnum):
    """The unit scale a filing states for a table's amounts, e.g. '(In millions)'."""

    UNITS = "units"
    THOUSANDS = "thousands"
    MILLIONS = "millions"
    BILLIONS = "billions"

    @property
    def multiplier(self) -> float:
        """Factor that converts an amount printed at this scale into whole currency units."""
        return _UNIT_SCALE_MULTIPLIERS[self]


_UNIT_SCALE_MULTIPLIERS = {
    FinancialStatementUnitScale.UNITS: 1.0,
    FinancialStatementUnitScale.THOUSANDS: 1_000.0,
    FinancialStatementUnitScale.MILLIONS: 1_000_000.0,
    FinancialStatementUnitScale.BILLIONS: 1_000_000_000.0,
}


class FinancialReportTable(BaseModel):
    description: str = Field(
        description="A description of the information contained in the table. "
        "Example: 'Consolidated Statements of Cash Flows'"
    )
    markdown_table: str = Field(
        description="The markdown table that contains the information. "
        "Example: '| Cash Flow | Amount |'"
    )
    unit_scale: FinancialStatementUnitScale = Field(
        description="The unit scale the filing states for the table's amounts, from a caption "
        "near the table's title such as '(In millions, except per share data)' or "
        "'(in thousands)'. Use 'units' only when no scale caption is present — US filers "
        "almost always state thousands or millions for financial statements."
    )
    share_counts_reported_in_stated_scale: bool = Field(
        description="Whether share counts in the table use the same stated unit scale as the "
        "monetary amounts. A caption like '(In millions, except per share data)' means share "
        "counts ARE in the stated scale (true). A caption like '(in thousands, except share "
        "and per share data)' means share counts are raw whole numbers (false).",
        default=True,
    )
    flagged_as_irrelevant: bool = Field(
        description="Whether the table is irrelevant to our analysis. Should be false by default.",
        default=False,
    )


class CleanedFinancialReportTable(BaseModel):
    """Response model for the table cleaning agent.

    Deliberately contains only the markdown so the cleaning agent cannot
    regenerate (and possibly hallucinate) the metadata captured at
    extraction time, such as ``unit_scale``.
    """

    markdown_table: str = Field(
        description="The refined markdown table. Example: '| Cash Flow | Amount |'"
    )


class FinancialReportTables(BaseModel):
    tables: list[FinancialReportTable] = Field(
        description="A list of tables from a 10Q document. "
        "Example: '[FinancialReportTable(description='Consolidated Statements of Cash Flows', "
        "markdown_table='| Cash Flow | Amount |'), "
        "FinancialReportTable(description='Consolidated Balance Sheet', "
        "markdown_table='| Cash Flow | Amount |')]'"
    )


def turn_table_to_string(table: FinancialReportTable) -> str:
    return f"""
Here is a description of the table:
{table.description}

Here is the table:
{table.markdown_table}
"""


def turn_tables_to_string(tables: list[FinancialReportTable]) -> str:
    return "\n===============\n".join([turn_table_to_string(table) for table in tables])


_data_extraction_system_prompt = """
You are a financial analyst.

You are given a 10Q document.

10Q documents are lengthy documents that are sometimes difficult for agents to process.
Your job is to trim down the document to the most relevant parts and clean it up,
so that it is easier for the parsing agent to process.
"""
_table_extraction_agent = create_agent(
    system_prompt=_data_extraction_system_prompt,
    model=DEFAULT_MODEL,
    response_format=FinancialReportTables,
)

_table_cleaning_agent = create_agent(
    system_prompt=_data_extraction_system_prompt,
    model=DEFAULT_MODEL,
    response_format=CleanedFinancialReportTable,
)


async def _extract_tables_from_report_page(
    page: str, quarter_info: EarningsPeriodInfo
) -> list[FinancialReportTable]:
    message = f"""
I have a page from a 10Q document. I would like you to extract any financial tables
that you see, so that we can run fundamental analysis on them.

The quarter that we are analyzing ends on:
{quarter_info.end_date}
If a table is about a different data, please flag it as irrelevant.

The time period that we care about is:
{quarter_info.columns_to_use}
If a table is not about that time period, please flag it as irrelevant.

For each table, look for a unit-scale caption near the table's title, such as
"(In millions, except per share data)" or "(in thousands)". Record that scale
as unit_scale. Also record whether share counts use the same scale: a caption
saying "except per share data" means share counts ARE in the stated scale,
while "except share and per share data" means share counts are raw whole
numbers. Do not convert any numbers — copy them exactly as printed.

========================================

Here is the page:
{page}
"""

    result = await _table_extraction_agent.ainvoke(
        {"messages": [{"role": "user", "content": message}]}
    )
    return result["structured_response"].tables


async def clean_table(
    table: FinancialReportTable, quarter_info: EarningsPeriodInfo
) -> FinancialReportTable:
    message = f"""
I have a table from a 10Q document. I want you to remove information that is
irrelevant to our analysis. Below are the instructions.

Sometimes a table will contain extra columns for other dates.
Here is the date that we care about:
{quarter_info.end_date}

Remove any columns that are not for the date that we care about.

Sometimes a table will contain extra columns for different time periods.
Here are the time periods that we care about:
{quarter_info.columns_to_use}

Remove any columns that are not for the time periods that we care about.

========================================

Here is the table that I want you to refine:

{table.markdown_table}
"""

    trimmed_table = (
        await _table_cleaning_agent.ainvoke({"messages": [{"role": "user", "content": message}]})
    )["structured_response"]

    cleaned_markdown_table = replace_parenthesized_numbers_with_negative_values(
        trimmed_table.markdown_table
    )
    cleaned_markdown_table = replace_dash_only_table_cells_with_zero_values(cleaned_markdown_table)

    # Copy from the original table so extraction-time metadata (description,
    # unit_scale, share_counts_reported_in_stated_scale) survives cleaning.
    return table.model_copy(update={"markdown_table": cleaned_markdown_table})


async def extract_tables_from_report(
    pages: list[str], quarter_info: EarningsPeriodInfo
) -> list[FinancialReportTable]:
    tables = []
    results = await asyncio.gather(
        *[_extract_cleaned_tables_from_page(page, quarter_info) for page in pages]
    )
    for result in results:
        tables.extend(result)
    return tables


async def _extract_cleaned_tables_from_page(
    page: str, quarter_info: EarningsPeriodInfo
) -> list[FinancialReportTable]:
    tables_from_page = await _extract_tables_from_report_page(page, quarter_info)
    tables_from_page = [table for table in tables_from_page if not table.flagged_as_irrelevant]
    cleaned_tables = await asyncio.gather(
        *[clean_table(table, quarter_info) for table in tables_from_page]
    )
    return cleaned_tables
