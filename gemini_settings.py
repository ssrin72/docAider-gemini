import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path='.env')

# Configuration for Gemini for AutoGen
autogen_llm_config = {
    "config_list": [
        {
            "model": os.getenv("GEMINI_MODEL"),
            "api_key": os.getenv("GEMINI_API_KEY"),
            "api_type": "google",
        }
    ],
    "temperature": 0,
}
