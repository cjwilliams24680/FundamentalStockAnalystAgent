import asyncio

from stock_analyst.calculation_interpreter import interpret_all_calculations
from stock_analyst.document_parser import run_parser_table_by_table
from stock_analyst.file_download_models import DownloadedFiling
from stock_analyst.notes_taker import take_notes_on_filing
from stock_analyst.paths import OUTPUT_DIRECTORY
from stock_analyst.report_writer import write_report
from stock_analyst.run_all_calculations import run_all_calculations
from stock_analyst.stock_directory import lookup
from stock_analyst.welcome import collect_user_input
from datetime import datetime


async def main():
    download_result = await collect_user_input()
    if not download_result:
        return

    parse_result = await run_parser_table_by_table(download_result.file_path)
    notes = await take_notes_on_filing(download_result.file_path)

    stock_info = lookup(download_result.ticker)
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
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    report_file_name = (
        f"{downloaded_filing.ticker}"
        f"_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.md"
    )
    report_path = OUTPUT_DIRECTORY / report_file_name
    with open(report_path, "w", encoding="utf-8") as file:
        file.write(report)


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
