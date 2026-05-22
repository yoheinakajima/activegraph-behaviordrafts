import os


def llm_available() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))
