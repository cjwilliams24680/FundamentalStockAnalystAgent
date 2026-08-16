from filing_downloader import run_report_downloader
from document_parser import run_parser_table_by_table
import asyncio

async def main():
    input_ticker = input("Enter a ticker: ")
    download_result = await run_report_downloader(input_ticker)
    run_parser_table_by_table(download_result.file_path)

if __name__ == "__main__":
    asyncio.run(main())
