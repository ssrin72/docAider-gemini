import os

# For AutoGen
# Note: You might need to run `pip install "pyautogen[gemini]"`
autogen_llm_config = {
    "config_list": [{
        "model": "gemini-2.5-pro",
        "api_key": os.getenv("GEMINI_API_KEY"),
    }],
    "temperature": 0,
}
