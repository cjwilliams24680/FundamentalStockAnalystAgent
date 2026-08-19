import asyncio
from dataclasses import dataclass
from pathlib import Path

from langchain.agents import create_agent

from stock_analyst.llm_provider import DEFAULT_MODEL
from stock_analyst.parsing.end_of_financial_period_parser import (
    extract_end_of_earnings_period,
    get_earnings_period_info,
)
from stock_analyst.parsing.pdf_reader import load_pdf_with_markdown_tables
from stock_analyst.parsing.quantitative_data import RawQuantitativeData
from stock_analyst.parsing.table_parser import (
    FinancialReportTable,
    extract_tables_from_report,
    turn_table_to_string,
)

_QUANTITATIVE_PARSING_PROMPT = """
You are a financial analyst.

You are given a 10Q document.

You are tasked with extracting financial statements from 10Q documents,
so that your team can run fundamental analysis using that data.

Documents often have multiple values for each field, which corresponds to different dates.
You should only extract the value that is for the most recent date.

Sometimes reports will use a dash or a line to represent zero.
Just use 0. Do not try to infer the value.

Sometimes values will be surrounded by parentheses. This represents a negative value.
Use the negative value of the number inside the parentheses.

Record numbers exactly as printed in the table. Never convert them for unit
captions like "in millions" or "in thousands" — the pipeline applies the unit
scale afterward.
"""
_QUANTITATIVE_PARSING_AGENT = create_agent(
    system_prompt=_QUANTITATIVE_PARSING_PROMPT,
    model=DEFAULT_MODEL,
    response_format=RawQuantitativeData,
)


@dataclass(frozen=True)
class QuantitativeParseResult:
    raw_data: RawQuantitativeData
    fiscal_quarter: str  # "Q1".."Q4", from end_of_financial_period_parser.EarningsPeriodInfo


async def parse_quantitative_values_from_report(path_to_report: Path) -> QuantitativeParseResult:
    pages = load_pdf_with_markdown_tables(path_to_report)
    quarter_info = await extract_end_of_earnings_period(pages)
    earnings_period_info = get_earnings_period_info(quarter_info)
    tables = await extract_tables_from_report(pages, earnings_period_info)

    merged_result = RawQuantitativeData()

    # Run the parser on each table one-by-one
    results = await asyncio.gather(*[_parse_quantitative_values_from_table(table) for table in tables])

    # Merge the parse results together
    for result in results:
        merged_result = merged_result.merge(result)

    return QuantitativeParseResult(raw_data=merged_result, fiscal_quarter=earnings_period_info.quarter)


async def _parse_quantitative_values_from_table(table: FinancialReportTable) -> RawQuantitativeData:
    message = f"""
Here is a table from a 10Q document. I would like you to parse it for financial statements:

{turn_table_to_string(table)}
"""

    result = await _QUANTITATIVE_PARSING_AGENT.ainvoke({"messages": [{"role": "user", "content": message}]})
    parse_result = result["structured_response"]

    # Scale per table, before merging: tables can state different scales.
    monetary_value_multiplier = table.unit_scale.multiplier
    share_count_multiplier = (
        monetary_value_multiplier if table.share_counts_reported_in_stated_scale else 1.0
    )
    return parse_result.apply_unit_scale(monetary_value_multiplier, share_count_multiplier)
