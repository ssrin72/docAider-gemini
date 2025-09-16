import os, sys, asyncio
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(parent_dir)
from dotenv import load_dotenv
load_dotenv(dotenv_path="./.env")
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage
from repo_agents.plugins import github_info_plugin, documentation_plugin
from typing import Annotated

class GitRepoAgent:
  """
  The entry point of the multi-agent documentation generation.
  The agent is responsible for getting git repo information and generating documentation
  It uses GithubInfoPlugin and DocumentationPlugin as tools.
  """
  def __init__(self) -> None:
    self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0, google_api_key=os.getenv("GEMINI_API_KEY"))
    tools = [
        github_info_plugin.get_all_repos,
        github_info_plugin.get_repo_owner,
        github_info_plugin.get_branches,
        github_info_plugin.get_all_files_in_repo,
        github_info_plugin.get_file_content,
        documentation_plugin.generate_documentation_for_file,
        documentation_plugin.generate_all_documentation,
    ]
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful repository copilot. Remember to ask for help if you're unsure how to proceed."),
            ("placeholder", "{chat_history}"),
            ("user", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    
    agent = create_tool_calling_agent(self.llm, tools, prompt)
    self.agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    self.history = []

  async def chat_with_agent(self, message) -> Annotated[str, "AI agent response"]:
    result = await self.agent_executor.ainvoke({
        "input": message,
        "chat_history": self.history
    })
    
    response = str(result['output'])
    print("Assistant > " + response)
    self.history.extend([
        HumanMessage(content=message),
        AIMessage(content=response),
    ])
    return response

  def generate_all_documentation(self) -> None:
    """
    Generates documentation for all files under the ROOT_FOLDER.
    Alternatively, you can chat with the agent to get your repo information, generate documentation for specified file, and also generate all documentation in one command.
    The chat_with_agent option is recommended for fully manipulating the repo agent.
    """
    documentation_plugin.generate_all_documentation.invoke({})
  
# Test this agent
if __name__ == "__main__":
  copilot = GitRepoAgent()
  # If you want to chat with git repo agent, use the following code:
  print("Hello! I am your Github repo copilot.")
  print("Due to current AST analysis performs locally, we do not support relative paths.")
  print("Instead, you need to provide the absolute path of your file.")
  print("Note: the `samples` folder has the files for testing purpose.")
  print("I can help you find Github information, for example, you can ask: Show me the content of the file XXX in the repo XXX")
  print("See my plugin file to find out what functions I can do.")
  print("To terminate this conversation, you can say 'exit'.")
  while True:
    user_input = input("User > ")
    if user_input == "exit":
      break
    asyncio.run(copilot.chat_with_agent(user_input))

  # documentation_plugin.generate_documentation_for_file("/Users/chengqike/Desktop/summer_project/repo-copilot/samples/data_processor.py")
