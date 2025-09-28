import os
import argparse
import git # For cloning repositories
import shutil # For cleaning up cloned repositories

from repo_agents.single_agent_generation.documentation_agent import DocumentationAgent

def main():
    parser = argparse.ArgumentParser(description="Generate documentation for a file, folder, or Git repository.")
    parser.add_argument("input_path", help="Path to a file, folder, or a Git repository URL.")
    parser.add_argument("--output_dir", default="docs_output",
                        help="Directory where generated documentation will be saved. Defaults to 'docs_output' in the current working directory.")
    args = parser.parse_args()

    input_path = args.input_path
    output_dir = os.path.abspath(args.output_dir)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    repo_cloned_path = None
    target_root_folder = None # The root of the code we are documenting

    # Check if input is a Git URL
    if input_path.startswith("http") or input_path.startswith("git@"):
        print(f"Cloning repository from {input_path}...")
        # Create a temporary directory for cloning
        repo_name = input_path.split('/')[-1].replace('.git', '')
        repo_cloned_path = os.path.join(os.getcwd(), f"temp_cloned_{repo_name}")
        if os.path.exists(repo_cloned_path):
            shutil.rmtree(repo_cloned_path) # Clean up previous temp clone if exists
        
        try:
            git.Repo.clone_from(input_path, repo_cloned_path)
            target_root_folder = repo_cloned_path
            print(f"Repository cloned to {repo_cloned_path}")
        except git.GitCommandError as e:
            print(f"Error cloning repository: {e}")
            return
    else:
        # Resolve absolute path for file or folder
        abs_input_path = os.path.abspath(input_path)
        
        if not os.path.exists(abs_input_path):
            print(f"Error: Input path '{abs_input_path}' does not exist.")
            return

        if os.path.isfile(abs_input_path):
            target_root_folder = os.path.dirname(abs_input_path)
        elif os.path.isdir(abs_input_path):
            target_root_folder = abs_input_path
        else:
            print(f"Error: Invalid input path type for '{abs_input_path}'.")
            return

    # Initialize DocumentationAgent
    agent = DocumentationAgent(root_folder=target_root_folder, output_dir=output_dir)

    files_to_document = []
    if os.path.isfile(abs_input_path): # If original input was a single file
        files_to_document.append(abs_input_path)
    elif target_root_folder: # If it's a directory or cloned repo
        print(f"Scanning for all files in {target_root_folder}...")
        for root, _, files in os.walk(target_root_folder):
            for file in files:
                # Exclude common non-source/binary files if desired, or include all
                # For now, include all regular files for documentation attempt
                full_file_path = os.path.join(root, file)
                if os.path.isfile(full_file_path): # Ensure it's a file, not a directory
                    files_to_document.append(full_file_path)

    if not files_to_document:
        print("No files found to document.")
        if repo_cloned_path:
            shutil.rmtree(repo_cloned_path)
        return

    print(f"Generating documentation for {len(files_to_document)} files...")
    for file_path in files_to_document:
        # The generate_documentation_for_file expects file_path relative to root_folder
        relative_file_path = os.path.relpath(file_path, target_root_folder)
        print(f"  - Documenting: {relative_file_path}")
        agent.generate_documentation_for_file(relative_file_path)

    print(f"\nDocumentation generation complete. Output saved to: {output_dir}")

    # Clean up cloned repository
    if repo_cloned_path:
        print(f"Cleaning up temporary cloned repository at {repo_cloned_path}...")
        shutil.rmtree(repo_cloned_path)

if __name__ == "__main__":
    main()
