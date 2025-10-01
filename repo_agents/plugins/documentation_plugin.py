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
    """Generates documentation for a single file. (Note: This tool is for individual file documentation,
    the main application now generates overall repository documentation.)"""
    file_content = read_file_content(file_path)
    documentation = mac.multi_agent_documentation_generation(file_path) # Calls the original individual file generation
    output_path = write_file_docs(
      output_folder,
      project_root_folder, # Pass project_root_folder
      file_path,
      documentation
    )
    cache.add(file_path, file_content, output_path)
    save_cache(output_folder, cache)
    print(f"Documentation for {file_path} generated and saved to {output_path}")

@tool
def generate_overall_repo_documentation_tool() -> None:
    """Generates overall documentation for the entire repository.
    (Note: This tool is a wrapper for the new overall repo documentation logic,
    which is primarily driven by the main application script.)"""
    # This tool simply calls the overall repo generation function from multi_agent_conversation
    # It assumes ROOT_FOLDER is set to the cloned repo's path during execution of the main app.
    cloned_repo_root_path = os.getenv("ROOT_FOLDER") # Get the dynamic root from environment
    if not cloned_repo_root_path:
        print("Error: ROOT_FOLDER environment variable is not set. Cannot generate overall repo documentation.")
        return

    print(f"Tool: Initiating overall repository documentation generation for {cloned_repo_root_path}...")
    overall_doc_content = mac.generate_overall_repo_documentation(cloned_repo_root_path)

    if overall_doc_content:
        repo_name = os.path.basename(cloned_repo_root_path)
        output_md_path = os.path.join(output_folder, f"{repo_name}_repo_documentation.md")
        with open(output_md_path, 'w', encoding='utf-8') as f:
            f.write(overall_doc_content)
        print(f"Tool: Overall repository documentation saved to: {output_md_path}")
    else:
        print("Tool: Overall repository documentation generation failed.")

# Renamed generate_all_documentation to indicate its specific purpose and
# to avoid confusion with the new overall repo documentation.
# The previous functionality of iterating through all files is now
# superseded by the overall repo documentation approach, or can be triggered
# per-file if needed. For now, it's removed as it's not directly used
# in the new overall flow.
