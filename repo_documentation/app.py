import time, os, sys
import git # Added for cloning Git repositories
import tempfile # Added for creating temporary directories
import shutil # Added for cleaning up temporary directories

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")

from repo_agents.single_agent_generation.documentation_agent import DocumentationAgent
from repo_documentation.merging.merger import create_documentation

def _clone_repo(repo_url, temp_dir):
    """Clones a Git repository into a specified temporary directory."""
    print(f"Cloning {repo_url} into {temp_dir}")
    try:
        git.Repo.clone_from(repo_url, temp_dir)
        print("Repository cloned successfully.")
        return temp_dir
    except Exception as e:
        print(f"Error cloning repository: {e}")
        return None

def run_documentation_generation_process(repo_url: str, target_path: str):
    """
    Handles cloning the repository, generating documentation, and cleaning up.
    """
    start_time = time.time()
    cloned_repo_root_path = None
    output_docs_folder = None
    
    repo_name = repo_url.split('/')[-1].replace('.git', '') # Extract repo name from URL

    temp_clone_dir = tempfile.mkdtemp()
    try:
        cloned_repo_root_path = _clone_repo(repo_url, temp_clone_dir)
        if not cloned_repo_root_path:
            return

        # Initialize DocumentationAgent with the cloned repository's root path
        da = DocumentationAgent(root_folder=cloned_repo_root_path)
        
        # This is the temporary folder where DocumentationAgent writes its markdown/raw docs
        agent_output_md_folder = os.path.join(cloned_repo_root_path, "docs_output")
        # This is the desired final output folder for the HTML documentation
        final_output_html_folder = os.path.join(cloned_repo_root_path, "docs_output", repo_name)
        
        # Ensure the final output directory exists
        os.makedirs(final_output_html_folder, exist_ok=True)

        full_target_path = os.path.join(cloned_repo_root_path, target_path)

        if target_path == ".":
            print(f"Generating documentation for all Python files in the repository: {cloned_repo_root_path}")
            for root, _, files in os.walk(cloned_repo_root_path):
                for file in files:
                    if file.endswith(".py"):
                        abs_file_path = os.path.join(root, file)
                        print(f"  Generating documentation for file: {abs_file_path}")
                        da.generate_documentation_for_file(abs_file_path)
        elif os.path.isfile(full_target_path):
            if full_target_path.endswith(".py"):
                print(f"Generating documentation for file: {full_target_path}")
                da.generate_documentation_for_file(full_target_path)
            else:
                print(f"Skipping documentation for non-Python file: {full_target_path}")
        elif os.path.isdir(full_target_path):
            print(f"Generating documentation for folder: {full_target_path} and its Python files")
            # Iterate through Python files in the specified folder and its subdirectories
            for root, _, files in os.walk(full_target_path):
                for file in files:
                    if file.endswith(".py"):
                        abs_file_path = os.path.join(root, file)
                        print(f"  Generating documentation for file: {abs_file_path}")
                        da.generate_documentation_for_file(abs_file_path)
            print(f"Note: A separate summary documentation for the folder '{target_path}' itself is not generated as per current single-agent capabilities.")
        else:
            print(f"Error: Target path '{target_path}' not found or is not a file/directory in the repository '{repo_url}'.")
            return

    finally:
        # Generate HTML documentation if specified, before cleaning up the temporary directory
        if os.getenv("FORMAT") == "html" and os.path.exists(agent_output_md_folder):
            print(f"Generating HTML documentation from {agent_output_md_folder}")
            # The create_documentation function is assumed to read from agent_output_md_folder
            # and write HTML files back into that same folder.
            create_documentation(agent_output_md_folder)

            # Move the generated HTML documentation to the final_output_html_folder
            if os.path.exists(agent_output_md_folder):
                print(f"Moving generated documentation from {agent_output_md_folder} to {final_output_html_folder}")
                for item in os.listdir(agent_output_md_folder):
                    s = os.path.join(agent_output_md_folder, item)
                    d = os.path.join(final_output_html_folder, item)
                    if os.path.isdir(s):
                        # Use copytree if target already exists, or rename if not.
                        # For simplicity, if item is a directory, just move it.
                        # This assumes items are not conflicting with existing directories in destination.
                        shutil.move(s, d)
                    else:
                        shutil.move(s, d)
        
        # Clean up the temporary cloned repository
        if cloned_repo_root_path and os.path.exists(cloned_repo_root_path):
            print(f"Cleaning up temporary repository: {cloned_repo_root_path}")
            shutil.rmtree(cloned_repo_root_path)

    total = round(time.time() - start_time, 3)
    print(f"Documentation generation completed in {total}s.")

if __name__ == "__main__":
    if len(sys.argv) == 3:
        repo_url = sys.argv[1]
        target_path = sys.argv[2]
        run_documentation_generation_process(repo_url, target_path)
    else:
        print("Usage: python repo_documentation/app.py <github_repo_url> <path_to_file_or_folder_in_repo>")
        print("       path_to_file_or_folder_in_repo can be '.' for the entire repository.")
        sys.exit(1) # Exit with an error code for incorrect usage
