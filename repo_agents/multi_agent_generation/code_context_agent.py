import asyncio, os, sys
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(parent_dir)
from dotenv import load_dotenv
load_dotenv(dotenv_path="../../.env")

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from repo_agents.plugins import code_context_plugin
from repo_agents.multi_agent_generation.prompt import CODE_CONTEXT_PROMPT
from repo_documentation.utils import Mode, save_prompt_debug

class CodeContextAgent:
  """
  This agent provides context explanation of code snippet.
  It is Self-contained, can be either included or excluded from the multi-agent conversation pattern.
  The purpose is to test whether the code context explanation increases the documentation quality.
  Additionally, as a lightweight code explainer, the user can consult with this agent for code context description.
  """
  def __init__(self) -> None:
    self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0, google_api_key=os.getenv("GEMINI_API_KEY"))
    tools = [code_context_plugin.get_file_content, code_context_plugin.get_callee_function_info]
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant who can provide the contextual description and explanation of the code. Remember to ask for help if you're unsure how to proceed."),
            ("user", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    
    agent = create_tool_calling_agent(self.llm, tools, prompt)
    self.agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

  async def code_context_explanation(self, file_path: str) -> str:
    """
    Returns the code context explanation of a source file.
    """
    message = CODE_CONTEXT_PROMPT.format(file_path=file_path)
    # Save prompt text for debug
    output_folder = os.path.join(os.getenv("ROOT_FOLDER"), "docs_output")
    save_prompt_debug(output_folder, file_path + "_code_context", message, Mode.UPDATE)
    
    result = await self.agent_executor.ainvoke({"input": message})
    return str(result['output'])

# Test this agent
if __name__ == "__main__":
  cca = CodeContextAgent()
  file_path = "your-source-file-path."
  result = asyncio.run(cca.code_context_explanation(file_path))
  print(result)
