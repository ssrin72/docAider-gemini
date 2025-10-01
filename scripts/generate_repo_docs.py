import os
import sys
import argparse
from dotenv import load_dotenv
import shutil # For cleaning up temporary directory

# Ensure the project root is in the path to import sibling modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

# Load environment variables from the project root .env file
# (This is mainly for local testing. GitHub Actions will use secrets.)
load_dotenv(dotenv_path=os.path.join(project_root, ".env"))

from repo_documentation.multi_agent_app import run_generate_documentation_for_file
import repo_documentation.merging.merger as merger
import repo_agents.multi_agent_generation.multi_agent_conversation as mac

def generate_repo_documentation(repo_path: str, output_filepath: str):
    """
    Generates documentation for the entire repository at repo_path and saves it
    to a single Markdown file at output_filepath.
    
    Args:
        repo_path (str): The root directory of the repository to document.
        output_filepath (str): The full path to the output Markdown file (e.g., 'documentation.md').
    """
    print(f"Starting documentation generation for repository: {repo_path}")
    print(f"Output will be saved to: {output_filepath}")

    files_to_process = []
    # Determine the absolute path of the docAider-gemini tool directory within the target repository
    # `project_root` is the absolute path to the docAider-gemini directory itself (e.g., /path/to/calcpy/docAider-gemini)
    tool_abs_path_in_repo = project_root 

    # Collect all Python and Ruby files in the repository
    for root, dirs, filenames in os.walk(repo_path):
        # Exclude the entire docAider-gemini tool directory and its contents from processing
        if root.startswith(tool_abs_path_in_repo):
            dirs[:] = []  # Don't recurse into this directory
            continue

        # Exclude standard VCS and temporary directories from being traversed
        if '.git' in dirs:
            dirs.remove('.git')
        if '.doc_gen_temp' in dirs:
            dirs.remove('.doc_gen_temp')
        if 'docs_output' in dirs:
            dirs.remove('docs_output')
        
        for filename in filenames:
            full_file_path = os.path.join(root, filename)
            
            # Exclude common non-code files, hidden files, and documentation files
            if filename.startswith('.') or \
               filename.endswith(('.bak', '.tmp', '.log', '.md', '.txt', '.yml', '.yaml', '.json', '.html', '.css', '.js')):
                continue
            
            # Add only Python and Ruby source files
            if filename.endswith((".py", ".rb")):
                files_to_process.append(full_file_path)

    if not files_to_process:
        print(f"No Python or Ruby files found in '{repo_path}' to document.")
        # Ensure the directory for the output file exists
        output_dir = os.path.dirname(output_filepath)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        # Create an empty or placeholder documentation file
        with open(output_filepath, "w") as f:
            f.write("# Repository Documentation\n\nNo Python or Ruby files found in this repository to generate documentation for.\n")
        return

    collected_file_docs = [] # To store (relative_path, markdown_content) tuples

    # Create a temporary output directory for debug files from run_generate_documentation_for_file
    temp_output_dir = os.path.join(repo_path, ".doc_gen_temp")
    os.makedirs(temp_output_dir, exist_ok=True)

    for i, target_file in enumerate(files_to_process):
        print(f"\n--- Processing file {i+1}/{len(files_to_process)}: {os.path.relpath(target_file, repo_path)} ---")
        # Pass repo_path as root_folder and temp_output_dir as output_dir
        markdown_content = run_generate_documentation_for_file(target_file, repo_path, temp_output_dir)
        
        if markdown_content:
            relative_path = os.path.relpath(target_file, repo_path)
            collected_file_docs.append((relative_path, markdown_content))
    
    # Clean up the temporary output directory
    if os.path.exists(temp_output_dir):
        shutil.rmtree(temp_output_dir)

    folder_overview_markdown = ""
    if collected_file_docs:
        print("\n--- Generating repository overview... ---")
        folder_name = os.path.basename(repo_path)
        
        # Prepare the context for the folder overview prompt
        files_doc_string_for_llm = ""
        for rel_path, doc_content in collected_file_docs:
            files_doc_string_for_llm += f"### File: `{rel_path}`\n\n{doc_content}\n\n"
        
        try:
            # Set the ROOT_FOLDER environment variable for the overview generation as well
            original_root_env = os.getenv("ROOT_FOLDER")
            os.environ["ROOT_FOLDER"] = repo_path
            folder_overview_markdown = mac.multi_agent_documentation_generation_for_folder(
                folder_name, files_doc_string_for_llm
            )
            if original_root_env is not None:
                os.environ["ROOT_FOLDER"] = original_root_env
            else:
                del os.environ["ROOT_FOLDER"]
        except Exception as e:
            print(f"Error generating repository overview: {e}")
            folder_overview_markdown = f"## Error: Failed to generate repository overview due to an error.\nDetails: {e}"

    print("\n--- All individual files processed. Merging documentation... ---")
    
    # The merger.create_documentation function expects an output_dir for index.md,
    # but we want a single file. We will pass the directory of the output_filepath.
    output_dir_for_merger = os.path.dirname(output_filepath) if os.path.dirname(output_filepath) else "."
    
    # Call create_documentation with the desired output filename
    merger.create_documentation(
        docs_folder=output_dir_for_merger,
        folder_overview_content=folder_overview_markdown,
        collected_file_docs=collected_file_docs,
        output_filename=os.path.basename(output_filepath)
    )
    print(f"Repository documentation saved to {output_filepath}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate documentation for the current repository."
    )
    parser.add_argument(
        "--repo_path",
        type=str,
        default=".",
        help="The root directory of the repository to document (default: current directory)."
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default="documentation.md",
        help="The name of the output Markdown file (default: documentation.md)."
    )
    args = parser.parse_args()

    # Ensure the output directory exists if it's not the current directory
    output_dir = os.path.dirname(args.output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    generate_repo_documentation(os.path.abspath(args.repo_path), os.path.abspath(args.output_file))
