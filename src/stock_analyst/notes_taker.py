import asyncio
from pathlib import Path

from langchain.agents import create_agent
from pydantic import BaseModel, Field

from stock_analyst.llm_models import get_default_model
from stock_analyst.pdf_reader import load_pdf_with_markdown_tables


class Notes(BaseModel):
    risks: list[str] = Field(description="A list of significant risks that the company is facing.")
    opportunities: list[str] = Field(
        description="A list of significant opportunities that the company is taking advantage of."
    )
    upcoming_catalysts: list[str] = Field(
        description="A list of significant upcoming catalysts that could impact "
        "the company's performance and/or remove ambiguity from the report."
    )

    def merge(self, other: "Notes") -> "Notes":
        return Notes(
            risks=self.risks + other.risks,
            opportunities=self.opportunities + other.opportunities,
            upcoming_catalysts=self.upcoming_catalysts + other.upcoming_catalysts,
        )


notes_taker_agent = create_agent(
    model=get_default_model(),
    system_prompt="You are a financial analyst. Your job is to comb over the financial "
    "performance report and take notes on any interesting insights or patterns that you see.",
    response_format=Notes,
)


async def take_notes_on_filing(file_path: Path) -> Notes:
    pages = load_pdf_with_markdown_tables(file_path)
    notes = Notes(
        risks=[],
        opportunities=[],
        upcoming_catalysts=[],
    )
    requests = [take_notes_from_page(page) for page in pages]
    results = await asyncio.gather(*requests)
    for result in results:
        notes = notes.merge(result)
    return notes


async def take_notes_from_page(page: str) -> Notes:
    message = f"""
    I have a page from a financial performance report.
    Your job is to comb over the text on the page and take notes on any
    interesting insights or patterns that you see.

    IMPORTANT: Ignore any tables on the page. Only focus on the text.
    The tables are not relevant to the notes you are taking.

    Focus on the most significant risks, opportunities, and upcoming catalysts
    that could impact the company in a meaningful way.

    Here is the page:
    {page}
    """

    result = await notes_taker_agent.ainvoke({"messages": [{"role": "user", "content": message}]})
    return result["structured_response"]
