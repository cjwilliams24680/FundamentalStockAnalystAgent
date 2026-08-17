from enum import Enum, auto
import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

load_dotenv(override=True)

class ModelConfig(Enum):
    REMOTE_ONLY = auto()
    LOCAL_ONLY = auto()
    DEFAULT = auto()

def _load_model_config() -> ModelConfig:
    match os.getenv("LLM_CONFIG"):
        case "remote_only":
            return ModelConfig.REMOTE_ONLY
        case "local_only":
            return ModelConfig.LOCAL_ONLY
        case _:
            return ModelConfig.DEFAULT


MODEL_CONFIG = _load_model_config()

def _get_default_model():
    if MODEL_CONFIG != ModelConfig.REMOTE_ONLY:
        return ChatOllama(model="gemma4", temperature=0)
    else:
        # gpt-5.6-luna rejects function tools with reasoning_effort on the
        # Chat Completions endpoint; the Responses API supports both.
        return ChatOpenAI(model="gpt-5.6-luna", use_responses_api=True)

DEFAULT_MODEL = _get_default_model()
_HIGH_EFFORT_MODEL = ChatOpenAI(model="gpt-5.6-sol", use_responses_api=True)

def get_high_effort_model():
    if MODEL_CONFIG == ModelConfig.LOCAL_ONLY:
        raise ValueError("High effort model is not available in local mode")
    return _HIGH_EFFORT_MODEL

def get_model_name() -> str:
    if isinstance(DEFAULT_MODEL, ChatOllama):
        return DEFAULT_MODEL.model
    else:
        return DEFAULT_MODEL.model_name
