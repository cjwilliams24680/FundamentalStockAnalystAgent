import asyncio
from pathlib import Path

from langchain.agents import create_agent

from stock_analyst.date_parser import (
    extract_quarter_info,
    get_quarter_parsing_parameters,
)
from stock_analyst.llm_models import DEFAULT_MODEL
from stock_analyst.pdf_reader import load_pdf_with_markdown_tables
from stock_analyst.quarterly_report_parse_result import QuarterlyReportParseResult
from stock_analyst.table_parser import (
    FinancialReportTable,
    extract_tables_from_report,
    turn_table_to_string,
)

parser_system_prompt = """
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
"""
parser_agent = create_agent(
    system_prompt=parser_system_prompt,
    model=DEFAULT_MODEL,
    response_format=QuarterlyReportParseResult,
)


async def run_parser_table_by_table(file_path: Path) -> QuarterlyReportParseResult:
    pages = load_pdf_with_markdown_tables(file_path)
    quarter_info = await extract_quarter_info(pages)
    params = get_quarter_parsing_parameters(quarter_info)
    tables = await extract_tables_from_report(pages, params)

    merged_result = QuarterlyReportParseResult()

    # Run the parser on each table one-by-one
    results = await asyncio.gather(*[run_parser_on_table(table) for table in tables])

    # Merge the parse results together
    for result in results:
        merged_result = merged_result.merge(result)

    return merged_result


async def run_parser_on_table(table: FinancialReportTable) -> QuarterlyReportParseResult:
    message = f"""
Here is a table from a 10Q document. I would like you to parse it for financial statements:

{turn_table_to_string(table)}
"""

    result = await parser_agent.ainvoke({"messages": [{"role": "user", "content": message}]})
    return result["structured_response"]
