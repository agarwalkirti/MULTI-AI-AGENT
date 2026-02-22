from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    FAST_API_URL = "http://127.0.0.1:9999/chat"

    ALLOWED_MODEL_NAMES =[
        "llama-3.1-8b-instant",
        "meta-llama/llama-guard-4-12b",
        "meta-llama/Llama-3.1-8B"
    ]

settings=Settings()
