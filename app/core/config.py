import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
# API_BASE_URL = "https://teddybackend-q8ki.onrender.com/api/v1"
API_BASE_URL=os.getenv("API_BASE_URL")
print(f"API_BASE_URL: {API_BASE_URL}")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# FastAPI Configuration
APP_TITLE = "Teddy - Personal Finance Assistant API"
APP_DESCRIPTION = "A RAG-based personal finance assistant that helps you manage your expenses"
APP_VERSION = "1.0.0"
