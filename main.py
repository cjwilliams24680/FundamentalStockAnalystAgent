from filing_downloader import run_report_downloader
from document_parser import run_parser_table_by_table
import asyncio

from run_all_calculations import run_all_calculations
from stock_directory import lookup
from calculation_interpreter import interpret_all_calculations

async def main():
    input_ticker = input("Enter a ticker: ")
    download_result = await run_report_downloader(input_ticker)
    parse_result = await run_parser_table_by_table(download_result.file_path)
    calculated_metrics = run_all_calculations(
        stock_info=lookup(input_ticker),
        parse_result=parse_result,
    )
    interpreted_values = interpret_all_calculations(calculated_metrics)
    unusual_values = [value for value in interpreted_values if value.falls_outside_normal_range]
    print(unusual_values)

if __name__ == "__main__":
    asyncio.run(main())
