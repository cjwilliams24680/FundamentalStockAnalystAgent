from filing_downloader import run_report_downloader
from document_parser import run_parser_table_by_table
import asyncio

from run_all_calculations import run_all_calculations
from stock_directory import lookup
from calculation_interpreter import interpret_all_calculations
from report_writer import write_report
from filing_downloader import DownloadedFiling
from notes_taker import take_notes_on_filing

async def main():
    input_ticker = input("Enter a ticker: ")
    stock_info = lookup(input_ticker)
    download_result = await run_report_downloader(input_ticker)
    parse_result = await run_parser_table_by_table(download_result.file_path)
    notes = await take_notes_on_filing(download_result.file_path)
    calculated_metrics = run_all_calculations(
        stock_info=stock_info,
        parse_result=parse_result,
    )
    interpreted_values = interpret_all_calculations(calculated_metrics)
    unusual_values = [value for value in interpreted_values if value.falls_outside_normal_range]
    report = await write_report(
        stock_info=stock_info,
        downloaded_filing=download_result,
        unusual_values=unusual_values,
        commentary=notes.risks + notes.opportunities + notes.upcoming_catalysts,
        parsed_values=parse_result,
    )
    save_report(report, download_result)

def save_report(report: str, downloaded_filing: DownloadedFiling) -> None:
    with open(f"output/{downloaded_filing.ticker}_{downloaded_filing.form_type}_{downloaded_filing.period_end_date}.md", "w", encoding="utf-8") as file:
        file.write(report)

if __name__ == "__main__":
    asyncio.run(main())
