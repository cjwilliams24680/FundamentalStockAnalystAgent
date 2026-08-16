from dataclasses import dataclass
from pydantic import BaseModel, Field
from llm_models import get_default_model
from langchain.agents import create_agent

class DateOfReport(BaseModel):
    quarter_end_date: str = Field(description="The date of the last day of the reported quarter. If the end date is not present, return an empty string.", examples=["March 31, 2026", "April 30, 2026"])
    month: str = Field(description="The month of the last day of the reported quarter. If the end date is not present, return an empty string.", examples=["March", "April"])


@dataclass
class QuarterParsingParameters:
    quarter: str
    end_date: str
    columns_to_use: list[str]

def get_quarter_parsing_parameters(quarter_info: DateOfReport) -> QuarterParsingParameters:
    match quarter_info.month.lower():
        case "march" | "april" | "may":
            return QuarterParsingParameters(quarter="Q1", end_date=quarter_info.quarter_end_date, columns_to_use=["13-weeks", "3 months", "year to date", "ytd"])
        case "june" | "july" | "august":
            return QuarterParsingParameters(quarter="Q2", end_date=quarter_info.quarter_end_date, columns_to_use=["26-weeks", "6 months", "year to date", "ytd"])
        case "september" | "october" | "november":
            return QuarterParsingParameters(quarter="Q3", end_date=quarter_info.quarter_end_date, columns_to_use=["39-weeks", "9 months", "year to date", "ytd"])
        case "december" | "january" | "february":
            return QuarterParsingParameters(quarter="Q4", end_date=quarter_info.quarter_end_date, columns_to_use=["52-weeks", "12 months", "full year", "annual", "for the year ended", "year to date", "ytd"])
        case _:
            raise ValueError(f"Invalid month: {quarter_info.month}") 

data_extraction_system_prompt = """
You are a financial analyst.

You are given a 10Q document.

10Q documents are lengthy documents that are sometimes difficult for agents to process.
Your job is to trim down the document to the most relevant parts and clean it up, so that it is easier for the parsing agent to process.
"""

date_of_report_extraction_agent = create_agent(
    system_prompt=data_extraction_system_prompt,
    model=get_default_model(),
    response_format=DateOfReport,
)

async def extract_quarter_info(pages: list[str]) -> DateOfReport:
    for page in pages:
        quarter_info = await extract_quarter_info_from_page(page)
        if quarter_info.quarter_end_date and quarter_info.month:
            # The end date should usually be on the first page of the document.
            # The loop is to handle unusual documents that have the end date on a different page.
            return quarter_info
    raise ValueError("No quarter info found in the document")

async def extract_quarter_info_from_page(page: str) -> DateOfReport:
    message = f"""
I have a page from a 10Q report. I'm trying to figure out the date of the report.

There should be a statement in the document that says something like "For the quarter ended [quarter_end_date]".
If you see that statement on this page, please extract that quarter_end_date.

Here is the page:
{page}
"""

    result = await date_of_report_extraction_agent.ainvoke({"messages": [{"role": "user", "content": message}]})
    return result["structured_response"]