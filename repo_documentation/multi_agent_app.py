import time, os, sys
import markdown
from weasyprint import HTML
from google.genai.errors import ClientError
import git

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)
from dotenv import load_dotenv
load_dotenv(dotenv_path="./.env")

from repo_agents.ast_agent import ASTAgent
import repo_agents.multi_agent_generation.multi_agent_conversation as mac

def run_generate_documentation_for_file(file_path: str):
  """
  Generates documentation for a single file using the multi-agent system and saves it as a PDF.
  """
  start_time = time.time()

  # Ensure call graph exists for context analysis. The ASTAgent constructor does this.
  print("Generating call graph for context analysis...")
  ast_agent = ASTAgent()
  print("Call graph generated.")
  
  print(f"Generating documentation for {file_path} using multi-agent system...")
  # This function orchestrates the multi-agent conversation and returns the final markdown.
  
  wait_times = [60, 120, 240, 480, 960, 1920] # 1m, 2m, 4m, 8m, 16m, 32m
  markdown_content = None
  for i, wait_time in enumerate(wait_times):
      try:
          markdown_content = mac.multi_agent_documentation_generation(file_path)
          break  # Success
      except ClientError as e:
          if "429" in str(e) and i < len(wait_times) - 1:
              print(f"Rate limit exceeded. Retrying in {int(wait_time / 60)} minute(s)...")
              time.sleep(wait_time)
          else:
              raise e
  
  if not markdown_content or "failed to run" in markdown_content:
      print(f"Error: Multi-agent documentation generation failed for {file_path}")
      print("Agent returned:", markdown_content)
      return

  print("Documentation generation complete. Converting to PDF...")
      
  # Convert markdown to HTML
  html_content = markdown.markdown(markdown_content)
  
  # Convert HTML to PDF
  file_name_without_ext = os.path.splitext(os.path.basename(file_path))[0]
  pdf_file_name = f"{file_name_without_ext}.pdf"
  pdf_output_path = os.path.join(ast_agent.root_folder, pdf_file_name)
  
  print(f"Saving PDF to {pdf_output_path}...")
  HTML(string=html_content, base_url=ast_agent.root_folder).write_pdf(pdf_output_path)
  
  total = round(time.time() - start_time, 3)
  print(f"Process completed in {total}s.")
  print(f"PDF documentation saved to: {pdf_output_path}")

  # A delay of 1 minute between processing each file to avoid rate limiting.
  print("Waiting for 1 minute before processing next file...")
  time.sleep(60)

# --- Main execution ---
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python repo_documentation/multi_agent_app.py <repo_url> <file_path_in_repo>")
        sys.exit(1)
        
    repo_url = sys.argv[1]
    file_path_in_repo = sys.argv[2]

    clone_dir = os.path.join(parent_dir, "cloned_repos")
    if not os.path.exists(clone_dir):
        os.makedirs(clone_dir)
    
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    repo_path = os.path.join(clone_dir, repo_name)

    if os.path.exists(repo_path):
        print(f"Repository found at {repo_path}. Skipping clone.")
    else:
        print(f"Cloning repository from {repo_url} to {repo_path}...")
        try:
            git.Repo.clone_from(repo_url, repo_path)
            print("Repository cloned successfully.")
        except git.exc.GitCommandError as e:
            print(f"Error cloning repository: {e}")
            sys.exit(1)
    
    # Set ROOT_FOLDER to the cloned repo, so ASTAgent uses it.
    os.environ["ROOT_FOLDER"] = repo_path

    target_file = os.path.join(repo_path, file_path_in_repo)
    if not os.path.exists(target_file):
        print(f"Error: Target file not found at {target_file}")
    else:
        run_generate_documentation_for_file(target_file)
