from dataclasses import dataclass

from langchain.agents import create_agent
from pydantic import BaseModel, Field

from stock_analyst.llm_provider import DEFAULT_MODEL


class EndOfEarningsPeriodParseResult(BaseModel):
    end_date: str = Field(
        description="The date of the last day of the reported quarter. "
        "If the end date is not present, return an empty string.",
        examples=["March 31, 2026", "April 30, 2026"],
    )
    month: str = Field(
        description="The month of the last day of the reported quarter. "
        "If the end date is not present, return an empty string.",
        examples=["March", "April"],
    )


@dataclass
class EarningsPeriodInfo:
    quarter: str
    end_date: str
    columns_to_use: list[str]


def get_earnings_period_info(parse_result: EndOfEarningsPeriodParseResult) -> EarningsPeriodInfo:
    match parse_result.month.lower():
        case "march" | "april" | "may":
            return EarningsPeriodInfo(
                quarter="Q1",
                end_date=parse_result.end_date,
                columns_to_use=["13-weeks", "3 months", "year to date", "ytd"],
            )
        case "june" | "july" | "august":
            return EarningsPeriodInfo(
                quarter="Q2",
                end_date=parse_result.end_date,
                columns_to_use=["26-weeks", "6 months", "year to date", "ytd"],
            )
        case "september" | "october" | "november":
            return EarningsPeriodInfo(
                quarter="Q3",
                end_date=parse_result.end_date,
                columns_to_use=["39-weeks", "9 months", "year to date", "ytd"],
            )
        case "december" | "january" | "february":
            return EarningsPeriodInfo(
                quarter="Q4",
                end_date=parse_result.end_date,
                columns_to_use=[
                    "52-weeks",
                    "12 months",
                    "full year",
                    "annual",
                    "for the year ended",
                    "year to date",
                    "ytd",
                ],
            )
        case _:
            raise ValueError(f"Invalid month: {parse_result.month}")


_end_of_earnings_period_parsing_system_prompt = """
You are a financial analyst.

You are given a 10Q document.

10Q documents are lengthy documents that are sometimes difficult for agents to process.
Your job is to trim down the document to the most relevant parts and clean it up,
so that it is easier for the parsing agent to process.
"""

_end_of_earnings_period_parsing_agent = create_agent(
    system_prompt=_end_of_earnings_period_parsing_system_prompt,
    model=DEFAULT_MODEL,
    response_format=EndOfEarningsPeriodParseResult,
)


async def extract_end_of_earnings_period(pages: list[str]) -> EndOfEarningsPeriodParseResult:
    for page in pages:
        parse_result = await _extract_end_of_earnings_period_from_page(page)
        if parse_result.end_date and parse_result.month:
            # The end date should usually be on the first page of the document.
            # The loop is to handle unusual documents that have the end date on a different page.
            return parse_result
    raise ValueError("No end of period found in the document")


async def _extract_end_of_earnings_period_from_page(page: str) -> EndOfEarningsPeriodParseResult:
    message = f"""
I have a page from an earnings report. I'm trying to figure out the end of the earnings period that is being reported.

There should be a statement in the document that says something like
"For the quarter ended [quarter_end_date]".
If you see that statement on this page, please extract that quarter_end_date.

Here is the page:
{page}
"""

    result = await _end_of_earnings_period_parsing_agent.ainvoke(
        {"messages": [{"role": "user", "content": message}]}
    )
    return result["structured_response"]
