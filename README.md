# Fundamental Stock Analyst Agent

An agent-based fundamental stock analyst: LLM agents parse SEC quarterly reports (10-Q PDFs)
into structured raw values, pure Python functions compute fundamental-analysis metrics from
them, and interpretation agents read the results.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency management
- An OpenAI API key and/or a local [Ollama](https://ollama.com/) install, depending on the
  `LLM_CONFIG` setting (see below; the default uses both)

## Setup

1. Install dependencies:

   ```sh
   uv sync
   ```

2. Create a `.env` file in the repo root with your OpenAI API key:

   ```sh
   OPENAI_API_KEY=sk-...
   ```

   Optionally set `LLM_CONFIG` to control which models the agents use:

   - unset (default) — local Ollama model for most agents, OpenAI for the
     high-effort steps (needs both Ollama and an OpenAI key)
   - `remote_only` — OpenAI models for everything (no Ollama needed)
   - `local_only` — local Ollama only; steps that require the high-effort
     OpenAI model (such as the filing downloader) will error

3. Build the stock directory (fetches US-listed stock data from the Nasdaq screener,
   requires network access):

   ```sh
   uv run build-directory
   ```

## Running the analysis

```sh
uv run analyze
```

This prompts for a ticker symbol and runs the full pipeline: downloading and parsing the
company's latest quarterly report, computing the fundamental metrics, and writing an
interpreted markdown report to `output/`.

## Example reports

Example reports produced by the agent can be found in
[`output/`](https://github.com/cjwilliams24680/FundamentalStockAnalystAgent/tree/main/output).

## Development

```sh
uv run pytest         # run the tests
uv run ruff check     # lint (add --fix to auto-fix)
uv run ruff format    # format
```

See `docs/fundamental_metrics.md` for what each metric means and
`docs/calculation_notes.md` for how the calculations are implemented.
