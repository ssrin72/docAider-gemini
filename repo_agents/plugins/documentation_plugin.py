import os
import repo_agents.multi_agent_generation.multi_agent_conversation as mac
from repo_agents.ast_agent import ASTAgent
from langchain.tools import tool
from cache.docs_cache import DocsCache
from repo_documentation.utils import save_cache, write_file_docs, read_file_content

root_folder = os.path.abspath(os.getenv("ROOT_FOLDER"))
output_folder = os.path.join(root_folder, "docs_output")
ast_agent = ASTAgent()
cache = DocsCache()

@tool
def generate_documentation_for_file(file_path: str) -> None:
    """Generates documentation for a file."""
    file_content = read_file_content(file_path)
    documentation = mac.multi_agent_documentation_generation(file_path)
    output_path = write_file_docs(
      output_folder,
      root_folder,
      file_path,
      documentation
    )
    cache.add(file_path, file_content, output_path)

@tool
def generate_all_documentation() -> None:
    """Generates documentation for all files under the root folder."""
    file_and_callee_function_dict = ast_agent.get_file_call_dict()
    
    for file_path, callee_functions in file_and_callee_function_dict.items():
      if file_path == 'EXTERNAL':  # Skip all external functions
        continue

      generate_documentation_for_file(file_path)
    
    save_cache(output_folder, cache)
