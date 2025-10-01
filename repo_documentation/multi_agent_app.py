import time, os, sys
import markdown
from weasyprint import HTML
from google.genai.errors import ClientError
import git # New import for GitPython
import tempfile # New import for temporary directories
import shutil # New import for directory cleanup

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)
from dotenv import load_dotenv
load_dotenv(dotenv_path="./.env")

# This _project_root_folder refers to the docAider-gemini project's root.
_project_root_folder = os.getenv("ROOT_FOLDER")
if not _project_root_folder or _project_root_folder == "/":
    os.environ["ROOT_FOLDER"] = parent_dir
_project_root_folder = os.environ["ROOT_FOLDER"] # get updated value

# The output directory for PDFs should be within the project's docs_output folder.
_pdf_output_dir = os.path.join(_project_root_folder, "docs_output")
os.makedirs(_pdf_output_dir, exist_ok=True) # Ensure it exists

from repo_agents.ast_agent import ASTAgent
import repo_agents.multi_agent_generation.multi_agent_conversation as mac

def run_generate_documentation_for_file(cloned_repo_root_path: str, file_path_in_repo: str):
  """
  Generates documentation for a single file using the multi-agent system and saves it as a PDF.
  Args:
      cloned_repo_root_path (str): The absolute path to the locally cloned repository root.
      file_path_in_repo (str): The path of the target file relative to the cloned repository root.
  """
  start_time = time.time()

  abs_target_file_path = os.path.join(cloned_repo_root_path, file_path_in_repo)
  if not os.path.exists(abs_target_file_path):
      print(f"Error: Target file not found within cloned repository at {abs_target_file_path}")
      return

  # Ensure call graph exists for context analysis.
  # Initialize ASTAgent with the root of the cloned repository.
  print("Generating call graph for context analysis...")
  ASTAgent(root_folder=cloned_repo_root_path) # Pass the cloned repo path here
  print("Call graph generated.")
  
  print(f"Generating documentation for {file_path_in_repo} using multi-agent system...")
  
  wait_times = [60, 120, 240, 480, 960, 1920]
  markdown_content = None
  for i, wait_time in enumerate(wait_times):
      try:
          # multi_agent_documentation_generation expects the absolute file path.
          markdown_content = mac.multi_agent_documentation_generation(abs_target_file_path)
          break  # Success
      except ClientError as e:
          if "429" in str(e) and i < len(wait_times) - 1:
              print(f"Rate limit exceeded. Retrying in {int(wait_time / 60)} minute(s)...")
              time.sleep(wait_time)
          else:
              raise e
  
  if not markdown_content or "failed to run" in markdown_content:
      print(f"Error: Multi-agent documentation generation failed for {file_path_in_repo}")
      print("Agent returned:", markdown_content)
      return

  print("Documentation generation complete. Converting to PDF...")
      
  # Convert markdown to HTML
  html_content = markdown.markdown(markdown_content)
  
  # Convert HTML to PDF
  file_name_without_ext = os.path.splitext(os.path.basename(file_path_in_repo))[0]
  # Appended '_doc' to the PDF filename to distinguish it and save it in the dedicated output directory.
  pdf_file_name = f"{file_name_without_ext}_doc.pdf" 
  pdf_output_path = os.path.join(_pdf_output_dir, pdf_file_name) # Use the dedicated output directory
  
  print(f"Saving PDF to {pdf_output_path}...")
  # The base_url for HTML rendering should be the cloned repo root for resolving relative paths in markdown.
  HTML(string=html_content, base_url=cloned_repo_root_path).write_pdf(pdf_output_path)
  
  total = round(time.time() - start_time, 3)
  print(f"Process completed in {total}s.")
  print(f"PDF documentation saved to: {pdf_output_path}")

  print("Waiting for 1 minute before processing next file...")
  time.sleep(60)

# --- Main execution ---
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python repo_documentation/multi_agent_app.py <repo_url> <file_path_in_repo>")
        sys.exit(1)
        
    repo_url = sys.argv[1]
    file_path_in_repo = sys.argv[2]
    
    temp_dir = None
    try:
        # Create a temporary directory for cloning the repository
        temp_dir = tempfile.mkdtemp()
        print(f"Cloning repository {repo_url} into {temp_dir}...")
        
        repo_name = os.path.basename(repo_url).replace(".git", "") # Extract repo name
        cloned_repo_path = os.path.join(temp_dir, repo_name)
        
        # GitPython expects the URL to end with .git for cloning
        if not repo_url.endswith('.git'):
            repo_url += '.git'
        
        git.Repo.clone_from(repo_url, cloned_repo_path)
        print("Repository cloned successfully.")
        
        run_generate_documentation_for_file(cloned_repo_path, file_path_in_repo)
    except git.exc.GitCommandError as e:
        print(f"Git cloning failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Clean up the temporary directory
        if temp_dir and os.path.exists(temp_dir):
            print(f"Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)
