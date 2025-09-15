import asyncio, os, sys
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(parent_dir)
# Add local code2flow clone to Python's path
sys.path.insert(0, os.path.join(parent_dir, "code2flow"))
from dotenv import load_dotenv
load_dotenv(dotenv_path="../../.env")

import google.generativeai as genai
from repo_agents.plugins.code_context_plugin import CodeContextPlugin
from repo_agents.multi_agent_generation.prompt import CODE_CONTEXT_PROMPT
from repo_documentation.utils import Mode, save_prompt_debug
from typing import Annotated

class CodeContextAgent:
  """
  This agent provides context explanation of code snippet.
  It is Self-contained, can be either included or excluded from the multi-agent conversation pattern.
  The purpose is to test whether the code context explanation increases the documentation quality.
  Additionally, as a lightweight code explainer, the user can consult with this agent for code context description.
  """
  def __init__(self) -> None:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    self.plugin = CodeContextPlugin()
    # Note: Using a model that supports tool calling. You can change `gemini-1.5-pro-latest` to another compatible model if needed.
    self.model = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest",
        tools=[self.plugin.get_file_content, self.plugin.get_callee_function_info]
    )

  async def code_context_explanation(self, file_path) -> Annotated[str, "The code context description."]:
    """
    Returns the code context explanation of a source file.
    """
    message = CODE_CONTEXT_PROMPT.format(file_path=file_path)
    # Save prompt text for debug
    output_folder = os.path.join(os.getenv("ROOT_FOLDER"), "docs_output")
    save_prompt_debug(output_folder, file_path + "_code_context", message, Mode.UPDATE)

    chat = self.model.start_chat(enable_automatic_function_calling=True)
    response = await chat.send_message_async(message)

    return response.text

# Test this agent
if __name__ == "__main__":
  cca = CodeContextAgent()
  file_path = "your-source-file-path."
  result = asyncio.run(cca.code_context_explanation(file_path))
  print(result)
