import asyncio
from pathlib import Path

from langchain.agents import create_agent
from pydantic import BaseModel, Field

from stock_analyst.llm_provider import DEFAULT_MODEL
from stock_analyst.pdf_reader import load_pdf_with_markdown_tables


class CommentaryParseResult(BaseModel):
    risks: list[str] = Field(description="A list of significant risks that the company is facing. If you don't see any, return an empty list.", default_factory=list)
    opportunities: list[str] = Field(description="A list of significant opportunities that the company is taking advantage of. If you don't see any, return an empty list.", default_factory=list)
    upcoming_catalysts: list[str] = Field(description="A list of significant upcoming catalysts that could impact the company's performance and/or remove ambiguity from the report. If you don't see any, return an empty list.", default_factory=list)

    def merge(self, other: "CommentaryParseResult") -> "CommentaryParseResult":
        return CommentaryParseResult(
            risks=self.risks + other.risks,
            opportunities=self.opportunities + other.opportunities,
            upcoming_catalysts=self.upcoming_catalysts + other.upcoming_catalysts,
        )

_COMMENTARY_PARSING_PROMPT = """
You are a financial analyst. Your job is to comb over the financial 
performance report and take notes on any interesting insights or patterns that you see."""

_COMMENTARY_PARSING_AGENT = create_agent(
    model=DEFAULT_MODEL,
    system_prompt=_COMMENTARY_PARSING_PROMPT,
    response_format=CommentaryParseResult,
)

async def parse_commentary_from_report(path_to_report: Path) -> CommentaryParseResult:
    pages = load_pdf_with_markdown_tables(path_to_report)
    commentary = CommentaryParseResult(
        risks=[],
        opportunities=[],
        upcoming_catalysts=[],
    )
    requests = [_parse_commentary_from_page(page) for page in pages]
    results = await asyncio.gather(*requests)
    for result in results:
        commentary = commentary.merge(result)
    return commentary


async def _parse_commentary_from_page(page: str) -> CommentaryParseResult:
    message = f"""
    I have a page from a financial performance report.
    Your job is to comb over the text on the page and take notes on any
    interesting insights or patterns that you see.

    IMPORTANT: Ignore any tables on the page. Only focus on the text.
    The tables are not relevant to the notes you are taking.

    Ignore any legal disclaimers on the page.

    Focus on the most significant risks, opportunities, and upcoming catalysts
    that could impact the company in a meaningful way. Only return clear observable facts.
    Don't make up any information. Don't add comments like "I don't see any risks" or "I don't see any opportunities".
    Only return the facts.

    Here is the page:
    {page}
    """

    result = await _COMMENTARY_PARSING_AGENT.ainvoke({"messages": [{"role": "user", "content": message}]})
    return result["structured_response"]
