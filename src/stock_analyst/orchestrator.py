import asyncio
from datetime import datetime

from stock_analyst.interpretation_runner import interpret_calculated_values
from stock_analyst.quantitative_data_parser import parse_quantitative_values_from_report
from stock_analyst.report_download_models import DownloadedReport
from stock_analyst.commentary_parser import parse_commentary_from_report
from stock_analyst.paths import OUTPUT_DIRECTORY
from stock_analyst.report_writer import write_report
from stock_analyst.calculations_runner import run_all_calculations
from stock_analyst.stock_directory import lookup
from stock_analyst.user_input_collector import collect_user_input

async def run_orchestrator():
    download_result = await collect_user_input()
    if not download_result:
        return

    print("Parsing filing...")
    parsed_report, notes = await asyncio.gather(
        parse_quantitative_values_from_report(download_result.file_path),
        parse_commentary_from_report(download_result.file_path)
    )

    print("Running calculations...")
    stock_info = lookup(download_result.ticker)
    calculated_metrics = run_all_calculations(
        stock_info=stock_info,
        parse_result=parsed_report.raw_data,
        fiscal_quarter=parsed_report.fiscal_quarter,
    )

    print("Interpreting output...")
    interpreted_values = interpret_calculated_values(calculated_metrics)
    unusual_values = [value for value in interpreted_values if value.falls_outside_normal_range]

    print("Writing report...")
    report = await write_report(
        stock_info=stock_info,
        downloaded_filing=download_result,
        unusual_values=unusual_values,
        commentary=notes.risks + notes.opportunities + notes.upcoming_catalysts,
        parsed_values=parsed_report.raw_data,
    )

    print("Saving report...")
    _save_report(report, download_result)

    print("Done!")


def _save_report(report: str, downloaded_filing: DownloadedReport) -> None:
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    report_file_name = (
        f"{downloaded_filing.ticker}_{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}.md"
    )
    report_path = OUTPUT_DIRECTORY / report_file_name
    with open(report_path, "w", encoding="utf-8") as file:
        file.write(report)
    print(f"Report saved to {report_path}")
