import os
import repo_agents.multi_agent_generation.multi_agent_conversation as mac
from repo_agents.ast_agent import ASTAgent
from langchain.tools import tool
from cache.docs_cache import DocsCache
from repo_documentation.utils import save_cache, write_file_docs, read_file_content

# The root_folder for plugins should be the project's root for consistent output.
# The `ROOT_FOLDER` environment variable should be set to the project's root.
project_root_folder = os.path.abspath(os.getenv("ROOT_FOLDER"))
output_folder = os.path.join(project_root_folder, "docs_output")
ast_agent = ASTAgent(root_folder=project_root_folder) # Initialize with project_root_folder
cache = DocsCache()

@tool
def generate_documentation_for_file(file_path: str) -> None:
    """Generates documentation for a single file."""
    file_content = read_file_content(file_path)
    documentation = mac.multi_agent_documentation_generation(file_path)
    output_path = write_file_docs(
      output_folder,
      project_root_folder,
      file_path,
      documentation
    )
    cache.add(file_path, file_content, output_path)
    save_cache(output_folder, cache)
    print(f"Documentation for {file_path} generated and saved to {output_path}")

# Removed generate_overall_repo_documentation_tool as it's no longer the main application flow.
# The previous functionality of iterating through all files is now directly handled by multi_agent_app.py.
