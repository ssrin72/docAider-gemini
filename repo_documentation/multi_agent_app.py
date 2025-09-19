import time, os, sys, re
import markdown
from weasyprint import HTML

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)
from dotenv import load_dotenv
load_dotenv(dotenv_path="./.env")

from repo_agents.multi_agent_generation.git_repo_agent import GitRepoAgent
from repo_documentation.merging.merger import create_documentation

from repo_agents.ast_agent import ASTAgent
from celery_worker.tasks import run_multi_agent_documentation_generation

def run_generate_documentation_for_file(file_path: str):
  """
  Invoke this function to trigger the doc gen process (multi-agent pattern).
  Tradeoff: Expensive (multi-agent conversation consumes more tokens), more accurate (more detailed documentation)
  Ensure you have all environment variables set up correctly. Check `.env_example` file to find out what they are.
  """
  start_time = time.time()

  # Ensure call graph exists for context analysis. The ASTAgent constructor does this.
  print("Generating call graph for context analysis...")
  ASTAgent()
  print("Call graph generated.")
  
  print(f"Generating documentation for {file_path} using multi-agent system...")
  # This function orchestrates the multi-agent conversation and returns the final markdown.
  print("Sending documentation generation task to celery worker...")
  
  markdown_content = None
  # Retry logic for rate limiting
  for attempt in range(3): # Try up to 3 times
      task = run_multi_agent_documentation_generation.delay(file_path, _root_folder)
      try:
          markdown_content = task.get(timeout=1800)
          break # Success
      except Exception as e:
          if ("RESOURCE_EXHAUSTED" in str(e) or "429" in str(e)) and attempt < 2:
              retry_delay_match = re.search(r"retryDelay': '(\d+)s", str(e))
              delay = 60
              if retry_delay_match:
                  delay = int(retry_delay_match.group(1)) + 5 # Add a small buffer
              
              print(f"Rate limit hit. Retrying in {delay} seconds... (Attempt {attempt + 2}/3)")
              time.sleep(delay)
          else:
              markdown_content = f"failed to run: {e}"
              break # Fail on other errors or last attempt
  
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
  pdf_output_path = os.path.join(_root_folder, pdf_file_name)
  
  print(f"Saving PDF to {pdf_output_path}...")
  HTML(string=html_content, base_url=_root_folder).write_pdf(pdf_output_path)
  
  total = round(time.time() - start_time, 3)
  root_folder = os.path.abspath(os.getenv("ROOT_FOLDER"))
  output_folder = os.path.join(root_folder, "docs_output")
  create_documentation(output_folder)
  print(f"Documentation generation completed in {total}s.")

# Test it
run_generate_documentation()