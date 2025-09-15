import os
from semantic_kernel.connectors.ai.google import GoogleGenerativeAIChatCompletion

# For Semantic Kernel
# Note: You might need to run `pip install semantic-kernel-connectors-google`
gemini_chat_completion_service = GoogleGenerativeAIChatCompletion(
    model_id="gemini-pro",
    api_key=os.getenv("GEMINI_API_KEY")
)

# For AutoGen
# Note: You might need to run `pip install "pyautogen[gemini]"`
autogen_llm_config = {
    "config_list": [{
        "model": "gemini-pro",
        "api_key": os.getenv("GEMINI_API_KEY"),
    }],
    "temperature": 0,
}
