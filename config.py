
import os
from dotenv import load_dotenv

load_dotenv()

class AzureOpenAI:
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    OPENAI_API_VERSION = "2025-01-01-preview"
    MODEL_NAME = "gpt-4.1-2025-04-14"