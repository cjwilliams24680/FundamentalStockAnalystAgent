from pathlib import Path
from pick import pick

from stock_analyst.stock_directory import StockInfo, lookup
from stock_analyst.llm_provider import MODEL_CONFIG, ModelConfig
from stock_analyst.earnings_report_downloader import get_filings_url, run_report_downloader
from stock_analyst.paths import SANDBOX_DIRECTORY
from stock_analyst.report_download_models import DownloadedReport, DownloadMethod

def _prompt_for_ticker() -> str:
    ticker = input("Enter a ticker: ")

    while lookup(ticker) is None:
        print(f"Ticker {ticker} not found. Please try again.")
        ticker = input("Enter a ticker: ")

    return ticker

def _prompt_for_download_method(stock_info: StockInfo) -> DownloadMethod:
    manual_option = "I've downloaded the earnings report pdf and placed it inside /sandbox"
    web_crawler_option = "I'd like you to download the earnings report pdf for me."
    options = [manual_option]
    foot_note = ""

    # Web crawling is only available when remote LLMs are enabled.
    # Local LLMs aren't powerful enough to reliably perform this task.
    if MODEL_CONFIG != ModelConfig.LOCAL_ONLY:
        options.insert(0, web_crawler_option)
        foot_note = "\nAlternatively, I can crawl that web page and download the file for you.\n"

    title = f"""
I need {stock_info.name}'s latest earnings report (10-Q or 10-K) in order to do my analysis.

The Nasdaq exchange provides them here:
{get_filings_url(stock_info)}

In order to proceed, open that url in your web browser and download the PDF.
Then drag it to the /sandbox folder in this project.
{foot_note}
Select an option to continue:
"""

    option, _ = pick(options=options, title=title, indicator="=>")
    if option == manual_option:
        return DownloadMethod.Manual
    elif option == web_crawler_option:
        return DownloadMethod.WebCrawler
    else:
        raise ValueError(f"Invalid download method: {option}")

def _prompt_for_file_selection() -> Path:
    return None

def _prompt_for_file_selection() -> Path:
    pdf_files = [f for f in SANDBOX_DIRECTORY.iterdir() if f.is_file() and f.suffix.lower() == '.pdf']

    # Handle case where no PDFs are found
    if not pdf_files:
        print(f"No PDF files found in: {SANDBOX_DIRECTORY}")
        return None

    pdf_files.sort(key=lambda f: f.stat().st_ctime, reverse=True)

    # Extract just the file names for clean menu display
    file_names = [f.name for f in pdf_files]

    title = f"Select a PDF file from {SANDBOX_DIRECTORY.name} (Use Arrow Keys + Enter):\n"
    selected_name, index = pick(
        options=file_names,
        title=title,
        indicator="=>",
    )

    return pdf_files[index]

async def collect_user_input() -> DownloadedReport:
    ticker = _prompt_for_ticker()
    stock_info = lookup(ticker)
    ticker = stock_info.ticker
    download_method = _prompt_for_download_method(stock_info)
    match download_method:
        case DownloadMethod.WebCrawler:
            return await run_report_downloader(ticker)
        case DownloadMethod.Manual:
            path = _prompt_for_file_selection()
            if path:
                return DownloadedReport(ticker=ticker, file_path=path)
            else:
                return None
        case _:
            raise ValueError(f"Invalid download method: {download_method}")
