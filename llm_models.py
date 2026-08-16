from langchain_ollama import ChatOllama
import os

def get_default_model(use_local_llm: bool=os.getenv("USE_LOCAL_LLM")):
    if use_local_llm:
        return ChatOllama(model="gemma4", temperature=0)
    else:
        return "openai:gpt-5.6-luna"
