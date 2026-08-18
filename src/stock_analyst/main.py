import asyncio
from datetime import datetime

from stock_analyst.calculation_interpreter import interpret_all_calculations
from stock_analyst.document_parser import run_parser_table_by_table
from stock_analyst.file_download_models import DownloadedFiling
from stock_analyst.notes_taker import take_notes_on_filing
from stock_analyst.paths import OUTPUT_DIRECTORY
from stock_analyst.report_writer import write_report
from stock_analyst.run_all_calculations import run_all_calculations
from stock_analyst.stock_directory import lookup
from stock_analyst.welcome import collect_user_input


async def main():
    download_result = await collect_user_input()
    if not download_result:
        return

    print("Parsing filing...")
    parsed_report, notes = await asyncio.gather(
        run_parser_table_by_table(download_result.file_path),
        take_notes_on_filing(download_result.file_path)
    )

    print("Running calculations...")
    stock_info = lookup(download_result.ticker)
    calculated_metrics = run_all_calculations(
        stock_info=stock_info,
        parse_result=parsed_report.parse_result,
        fiscal_quarter=parsed_report.fiscal_quarter,
    )

    print("Interpreting output...")
    interpreted_values = interpret_all_calculations(calculated_metrics)
    unusual_values = [value for value in interpreted_values if value.falls_outside_normal_range]

    print("Writing report...")
    report = await write_report(
        stock_info=stock_info,
        downloaded_filing=download_result,
        unusual_values=unusual_values,
        commentary=notes.risks + notes.opportunities + notes.upcoming_catalysts,
        parsed_values=parsed_report.parse_result,
    )

    print("Saving report...")
    save_report(report, download_result)

    print("Done!")


def save_report(report: str, downloaded_filing: DownloadedFiling) -> None:
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    report_file_name = (
        f"{downloaded_filing.ticker}_{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}.md"
    )
    report_path = OUTPUT_DIRECTORY / report_file_name
    with open(report_path, "w", encoding="utf-8") as file:
        file.write(report)
    print(f"Report saved to {report_path}")


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
