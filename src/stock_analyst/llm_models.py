import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

load_dotenv(override=True)


def get_default_model(use_local_llm: bool | None = None):
    if use_local_llm is None:
        # os.getenv returns a string, and any non-empty string (including
        # "false") is truthy, so the value must be parsed explicitly.
        use_local_llm = os.getenv("USE_LOCAL_LLM", "").strip().lower() in ("1", "true", "yes")
    if use_local_llm:
        return ChatOllama(model="gemma4", temperature=0)
    else:
        # gpt-5.6-luna rejects function tools with reasoning_effort on the
        # Chat Completions endpoint; the Responses API supports both.
        return ChatOpenAI(model="gpt-5.6-luna", use_responses_api=True)


def get_high_effort_model():
    return ChatOpenAI(model="gpt-5.6-sol", use_responses_api=True)


def get_model_name() -> str:
    model = get_default_model()
    if isinstance(model, ChatOllama):
        return model.model
    else:
        return model.model_name
