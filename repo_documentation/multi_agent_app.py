import time, os, sys
import argparse
from google.genai.errors import ClientError
import git

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)
from dotenv import load_dotenv
load_dotenv(dotenv_path="./.env")

from repo_agents.ast_agent import ASTAgent
import repo_agents.multi_agent_generation.multi_agent_conversation as mac
import repo_documentation.merging.merger as merger

# Define the global output directory for documentation artifacts
OUTPUT_DIR = os.path.join(parent_dir, "docs_output")
os.makedirs(OUTPUT_DIR, exist_ok=True) # Ensure it exists

def run_generate_documentation_for_file(file_path: str) -> str | None:
  """
  Generates documentation for a single file using the multi-agent system.
  Returns the generated Markdown content or None if generation failed.
  Individual files are NOT saved to disk in this function anymore.
  """
  start_time = time.time()

  # Initialize ASTAgent for context analysis. Pass the root_folder (cloned repo)
  # and the desired output_dir (project's docs_output).
  # The root_folder for ASTAgent should still be the cloned repo so that relative paths work correctly for code2flow.
  ast_agent = ASTAgent(root_folder=os.getenv("ROOT_FOLDER", "."), output_dir=OUTPUT_DIR)
  
  # The ASTAgent's get_callee_function_info now handles non-Python files gracefully.
  # Provide a more specific warning here.
  if not file_path.lower().endswith(".py"):
      print(f"Note: Skipping AST analysis for non-Python file: {os.path.basename(file_path)}. Proceeding with documentation without AST context.")
  elif not ast_agent.graph:
      print(f"Warning: AST analysis for '{os.path.basename(file_path)}' could not generate a call graph. Proceeding with documentation without AST context.")
  else:
      print(f"AST call graph available for '{os.path.basename(file_path)}' for context analysis.")
  
  print(f"Initiating multi-agent documentation generation for '{os.path.basename(file_path)}'...")
  
  markdown_content = None
  # Exponential backoff for rate limiting (delays in minutes)
  wait_times_seconds = [60, 120, 240, 480, 960, 1920] # 1m, 2m, 4m, 8m, 16m, 32m
  for i, wait_time_sec in enumerate(wait_times_seconds):
      try:
          markdown_content = mac.multi_agent_documentation_generation(file_path)
          break  # Success, exit loop
      except ClientError as e:
          if "429" in str(e) and i < len(wait_times_seconds) - 1:
              print(f"Rate limit exceeded. Retrying in {int(wait_time_sec / 60)} minute(s)...")
              time.sleep(wait_time_sec)
          else:
              print(f"Error: ClientError during documentation generation for {os.path.basename(file_path)}: {e}")
              return None
      except Exception as e:
          print(f"An unexpected error occurred during documentation generation for {os.path.basename(file_path)}: {e}")
          return None

  if not markdown_content:
      print(f"Error: Multi-agent documentation generation failed for {os.path.basename(file_path)} after multiple retries.")
      return None

  total = round(time.time() - start_time, 3)
  print(f"Process completed for {os.path.basename(file_path)} in {total}s. Markdown content generated.")

  return markdown_content

# --- Main execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate documentation for a GitHub repository, folder, or file."
    )
    parser.add_argument("repo_url", type=str, help="URL of the GitHub repository.")
    parser.add_argument(
        "target_path",
        type=str,
        help="'.' for the entire repository, or a path to a specific folder/file within the repository.",
    )

    args = parser.parse_args()

    files_to_process = []
    source_root_folder = None
    
    repo_url = args.repo_url.rstrip('/')
    target_path_in_repo = args.target_path

    clone_dir = os.path.join(parent_dir, "cloned_repos")
    os.makedirs(clone_dir, exist_ok=True)
    
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
    
    source_root_folder = repo_path
    os.environ["ROOT_FOLDER"] = source_root_folder
    print(f"Processing files in: {source_root_folder}")

    full_target_path = os.path.join(repo_path, target_path_in_repo)

    if target_path_in_repo == '.':
        # Process the entire cloned repository
        for root, _, filenames in os.walk(source_root_folder):
            for filename in filenames:
                # Include both Python and Ruby files
                if filename.endswith((".py", ".rb")):
                    files_to_process.append(os.path.join(root, filename))
    elif os.path.isdir(full_target_path):
        # Process a specific folder within the cloned repository
        for root, _, filenames in os.walk(full_target_path):
            for filename in filenames:
                # Include both Python and Ruby files
                if filename.endswith((".py", ".rb")):
                    files_to_process.append(os.path.join(root, filename))
    elif os.path.isfile(full_target_path):
        # Process a specific file within the cloned repository
        # Include both Python and Ruby files
        if full_target_path.endswith((".py", ".rb")):
            files_to_process.append(full_target_path)
        else:
            print(f"Error: Target file '{full_target_path}' is not a Python or Ruby file.")
            sys.exit(1)
    else:
        print(f"Error: Target path '{full_target_path}' not found or is invalid.")
        sys.exit(1)

    # This duplicate check for `if not files_to_process` is therefore removed.

    collected_file_docs = [] # To store (relative_path, markdown_content) tuples

    # Determine if a single file was explicitly targeted
    is_single_file_target = (len(files_to_process) == 1 and os.path.isfile(full_target_path))

    if is_single_file_target:
        target_file = files_to_process[0]
        print(f"\n--- Processing single file: {target_file} ---")
        markdown_content = run_generate_documentation_for_file(target_file)
        
        if markdown_content:
            # Save single file documentation directly to its own .md file
            output_filename = os.path.basename(target_file) + ".md"
            output_filepath = os.path.join(OUTPUT_DIR, output_filename)
            with open(output_filepath, "w") as f:
                f.write(markdown_content)
            print(f"Documentation for '{os.path.basename(target_file)}' saved to {output_filepath}")
        else:
            print(f"No documentation generated for {os.path.basename(target_file)}.")
    else: # Process multiple files or a folder/repo
        for i, target_file in enumerate(files_to_process):
            print(f"\n--- Processing file: {target_file} ---")
            markdown_content = run_generate_documentation_for_file(target_file)
            
            if markdown_content:
                relative_path = os.path.relpath(target_file, source_root_folder)
                collected_file_docs.append((relative_path, markdown_content))
            
        folder_overview_markdown = ""
        is_folder_or_repo_input = (args.target_path == '.' or os.path.isdir(full_target_path))
        if len(collected_file_docs) > 0 and is_folder_or_repo_input: # Generate overview if files were processed and input was folder/repo
            print("\n--- Generating folder/repository overview... ---")
            
            # Determine the name for the folder overview
            if args.target_path == '.':
                folder_name = os.path.basename(source_root_folder)
            else:
                folder_name = os.path.basename(full_target_path)
            
            # Prepare the context for the folder overview prompt
            files_doc_string_for_llm = ""
            for rel_path, doc_content in collected_file_docs:
                files_doc_string_for_llm += f"### File: `{rel_path}`\n\n{doc_content}\n\n"
            
            # Call the multi-agent system for folder overview
            try:
                folder_overview_markdown = mac.multi_agent_documentation_generation_for_folder(
                    folder_name, files_doc_string_for_llm
                )
            except ClientError as e:
                print(f"Error generating folder overview: {e}")
                folder_overview_markdown = f"## Error: Failed to generate folder overview due to an API error.\nDetails: {e}"
            except Exception as e:
                print(f"An unexpected error occurred during folder overview generation: {e}")
                folder_overview_markdown = f"## Error: An unexpected error occurred during folder overview generation.\nDetails: {e}"

        print("\n--- All individual files processed. Merging documentation... ---")
        merger.create_documentation(OUTPUT_DIR,
                                    folder_overview_content=folder_overview_markdown,
                                    collected_file_docs=collected_file_docs)
        print(f"Full project documentation merged into {os.path.join(OUTPUT_DIR, 'index.md')}")
