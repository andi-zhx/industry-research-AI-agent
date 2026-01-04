# config/llm.py

import os
from crewai import LLM

def get_deepseek_llm():
    return LLM(
        model="openai/deepseek-chat",
        base_url=os.getenv("DEEPSEEK_API_BASE"),
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        temperature=0.3,
        timeout=1800,
        max_tokens=8000,
        max_retries=3
    )
