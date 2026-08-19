from pathlib import Path

import requests
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from pydantic import BaseModel, Field

from stock_analyst.data_collection.report_download_models import DownloadedReport
from stock_analyst.data_collection.stock_directory import StockInfo, lookup
from stock_analyst.llm_provider import get_high_effort_model
from stock_analyst.paths import SANDBOX_DIRECTORY

_DOWNLOAD_DIRECTORY = SANDBOX_DIRECTORY


class QuarterlyReportFilingRow(BaseModel):
    """One row of Nasdaq's SEC-filings table, for the most recent 10-Q filing."""

    company_name: str
    form_type: str
    filed_date: str = Field(description="The 'Filed' column, formatted MM/DD/YYYY.")
    period_end_date: str = Field(description="The 'Period' column, formatted MM/DD/YYYY.")
    download_link: str = Field(
        description="The full href of the 'PDF' link in the row's View column."
    )

def get_filings_url(stock_info: StockInfo) -> str:
    return f"https://www.nasdaq.com/market-activity/stocks/{stock_info.ticker}/sec-filings?page=1&rows_per_page=50"

def _get_web_crawling_instructions(stock_info: StockInfo) -> str:
    # Nasdaq actually lists 10Qs for NYSE stocks too, so I can use the same instructions for both.
    return f"""
Go to {get_filings_url(stock_info)}

You'll see a list of SEC forms.

You should see the following columns: Company Name, Form Type, Filed, Period, View.

Find the first row in the table that has a Form Type of "10-Q" or "10-K".
You may need to scroll down or click the "Next" button to see another page.

From that row's View column, read the href attribute of the "PDF" link. Do NOT click the
link -- clicking opens a new tab and no download event fires. Just extract the href.

Return the information from that row, including the PDF link's href.
"""


def _download_filing(download_link: str, destination: Path) -> None:
    """Fetch the filing's href directly over HTTP.

    Clicking the link in the browser opens a new tab and never fires a
    Playwright download event, so the href must be fetched directly instead.
    """
    response = requests.get(
        download_link,
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
        timeout=60,
    )
    response.raise_for_status()
    if not response.content.startswith(b"%PDF"):
        raise ValueError(
            f"Expected a PDF from {download_link}, got "
            f"{response.headers.get('Content-Type')!r}: {response.content[:200]!r}"
        )
    destination.write_bytes(response.content)


async def run_report_downloader(ticker: str) -> DownloadedReport:
    client = MultiServerMCPClient(
        {
            "playwright": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@playwright/mcp@latest", "--isolated"],
            }
        }
    )

    browser_tools = await client.get_tools()

    model = get_high_effort_model()

    browser_agent = create_agent(
        model=model,
        tools=browser_tools,
        system_prompt="You are a web research assistant. "
        "Use the browser tools to locate the requested 10Q filing.",
        response_format=QuarterlyReportFilingRow,
    )

    stock_info = lookup(ticker)

    # Stream every step so tool calls and tool results are visible while the
    # agent works, instead of only the final answer.
    final_state = None
    async for chunk in browser_agent.astream(
        {"messages": [{"role": "user", "content": _get_web_crawling_instructions(stock_info)}]},
        config={"recursion_limit": 50},
        stream_mode="values",
    ):
        chunk["messages"][-1].pretty_print()
        final_state = chunk

    filing_row = final_state.get("structured_response") if final_state else None
    if filing_row is None:
        raise RuntimeError("Agent finished without producing a structured filing row.")

    period_end_date_for_filename = filing_row.period_end_date.replace("/", "-")
    file_name = (
        f"{stock_info.ticker}_{filing_row.form_type}_ended_{period_end_date_for_filename}.pdf"
    )
    destination = _DOWNLOAD_DIRECTORY / file_name
    _download_filing(filing_row.download_link, destination)
    print(f"Saved {destination} ({destination.stat().st_size:,} bytes)")

    return DownloadedReport(
        ticker=stock_info.ticker,
        file_path=destination,
    )
