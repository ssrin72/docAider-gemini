import time, os, sys
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

# The output directory for generated documentation.
_docs_output_dir = os.path.join(_project_root_folder, "docs_output")
os.makedirs(_docs_output_dir, exist_ok=True) # Ensure it exists

from repo_agents.ast_agent import ASTAgent # Re-import ASTAgent
import repo_agents.multi_agent_generation.multi_agent_conversation as mac

def run_generate_documentation_for_repo(cloned_repo_root_path: str):
  """
  Generates individual documentation for each Python file in an entire repository using the multi-agent system.
  Args:
      cloned_repo_root_path (str): The absolute path to the locally cloned repository root.
  """
  start_time = time.time()

  # Set ROOT_FOLDER environment variable for ASTAgent and other components
  os.environ["ROOT_FOLDER"] = cloned_repo_root_path

  # Initialize ASTAgent to get all Python files in the repository
  print("Initializing ASTAgent and identifying Python files for documentation...")
  ast_agent = ASTAgent(root_folder=cloned_repo_root_path)
  file_and_callee_function_dict = ast_agent.get_file_call_dict()
  print("Python files identified.")
  print(f"Files to document: {list(file_and_callee_function_dict.keys())}")

  print(f"Generating individual documentation for files in {cloned_repo_root_path} using multi-agent system...")
  
  all_files_documented = []
  for file_path_in_repo in file_and_callee_function_dict.keys():
      if file_path_in_repo == 'EXTERNAL':
          print(f"Skipping 'EXTERNAL' entry in call graph.")
          continue
      
      abs_target_file_path = os.path.join(cloned_repo_root_path, file_path_in_repo)
      if not os.path.exists(abs_target_file_path):
          print(f"Warning: File '{file_path_in_repo}' not found within cloned repository at {abs_target_file_path}. Skipping.")
          continue

      print(f"  - Generating documentation for {file_path_in_repo}...")
      wait_times = [30, 60, 120, 240, 480, 960] # Adjusted wait times for 30-second initial delay
      markdown_content = None
      for i, wait_time in enumerate(wait_times):
          try:
              # multi_agent_documentation_generation expects the absolute file path.
              markdown_content = mac.multi_agent_documentation_generation(abs_target_file_path)
              break  # Success
          except ClientError as e:
              if "429" in str(e) and i < len(wait_times) - 1:
                  print(f"Rate limit exceeded. Retrying in {int(wait_time)} seconds...")
                  time.sleep(wait_time)
              else:
                  raise e
      
      if not markdown_content or "failed to run" in markdown_content:
          print(f"Error: Multi-agent documentation generation failed for {file_path_in_repo}")
          print("Agent returned:", markdown_content)
          continue
      
      # Save the individual markdown document to the project's docs_output directory, mirroring source structure
      relative_dir = os.path.dirname(file_path_in_repo)
      target_output_dir_for_file = os.path.join(_docs_output_dir, relative_dir)
      os.makedirs(target_output_dir_for_file, exist_ok=True)
      
      file_name_md = os.path.basename(file_path_in_repo).replace(".py", ".md") # Ensure .md extension
      output_md_path = os.path.join(target_output_dir_for_file, file_name_md)
      
      with open(output_md_path, 'w', encoding='utf-8') as f:
          f.write(markdown_content)
      all_files_documented.append(output_md_path) # Store the path to the generated MD
      print(f"    Documentation for {file_path_in_repo} saved to {output_md_path}")
      time.sleep(30) # 30-second delay between files as requested

  if not all_files_documented:
      print("No files were successfully documented.")
      return
  
  print("\nAll individual file documentations generated. Now generating overall repository documentation...")
  
  # Read all generated markdown contents for context
  all_md_contents = {}
  for md_file_path in all_files_documented:
      try:
          with open(md_file_path, 'r', encoding='utf-8') as f:
              # Get path relative to _docs_output_dir for the overall prompt
              relative_path_to_doc = os.path.relpath(md_file_path, _docs_output_dir)
              all_md_contents[relative_path_to_doc] = f.read()
      except Exception as e:
          print(f"Warning: Could not read generated markdown file {md_file_path}: {e}")
  
  if not all_md_contents:
      print("No individual markdown files found to generate overall documentation. Skipping.")
  else:
      # Call a new multi-agent function for overall documentation from generated markdowns
      repo_name_for_doc = os.path.basename(cloned_repo_root_path).replace(".git", "")
      overall_repo_doc_content = None
      wait_times = [60, 120, 240, 480, 960, 1920]
      for i, wait_time in enumerate(wait_times):
          try:
              overall_repo_doc_content = mac.generate_overall_repo_documentation_from_markdowns(
                  repo_name_for_doc, cloned_repo_root_path, all_md_contents
              )
              break
          except ClientError as e:
              if "429" in str(e) and i < len(wait_times) - 1:
                  print(f"Rate limit exceeded during overall doc generation. Retrying in {int(wait_time)} seconds...")
                  time.sleep(wait_time)
              else:
                  raise e
          except Exception as e:
              print(f"An unexpected error occurred during overall documentation generation: {e}")
              if i < len(wait_times) - 1:
                  print(f"Retrying in {int(wait_time)} seconds...")
                  time.sleep(wait_time)
              else:
                  raise e

      if overall_repo_doc_content and "failed to run" not in overall_repo_doc_content:
          final_overall_doc_path = os.path.join(_docs_output_dir, f"{repo_name_for_doc}_overall_documentation.md")
          with open(final_overall_doc_path, 'w', encoding='utf-8') as f:
              f.write(overall_repo_doc_content)
          print(f"Overall repository documentation saved to: {final_overall_doc_path}")
      else:
          print(f"Error: Overall repository documentation generation failed.")

  total = round(time.time() - start_time, 3)
  print(f"\nTotal documentation generation process completed in {total}s.")
  print(f"All documentation files are saved in: {_docs_output_dir}")

# --- Main execution ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python repo_documentation/multi_agent_app.py <repo_url>")
        sys.exit(1)
        
    repo_url = sys.argv[1]
    
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
        
        run_generate_documentation_for_repo(cloned_repo_path)
    except git.exc.GitCommandError as e:
        print(f"Git cloning failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Clean up the temporary directory
        if temp_dir and os.path.exists(temp_dir):
            print(f"Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)
