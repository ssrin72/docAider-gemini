import os
import argparse
import sys

# Ensure the root folder for imports is correctly set for this script
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.insert(0, project_root)

from repo_documentation.update_app import DocumentationUpdate

def generate_or_update_documentation(repo_path: str, branch: str, file_path: str = None, comment: str = None):
    """
    Generates or updates documentation for the specified repository and branch.
    If file_path is provided, it updates documentation for that specific file.
    If comment is provided, it updates documentation based on the comment.
    """
    print(f"Starting documentation update for repo: {repo_path}, branch: {branch}")
    print(f"File path: {file_path if file_path else 'All changed files'}")
    
    try:
        doc_updater = DocumentationUpdate(
            repo_path=repo_path, 
            branch=branch, 
            file_path=file_path, 
            comment=comment
        )
        
        if comment and file_path:
            doc_updater.update_documentation_based_on_comment(file_path, comment, doc_updater.repo.head.commit)
        else:
            doc_updater.run()
        print("Documentation generation/update process completed successfully.")
    except Exception as e:
        print(f"An error occurred during documentation generation/update: {e}")
        # Re-raise the exception to indicate failure in the CI/CD pipeline
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate or update documentation for a local repository.")
    parser.add_argument("--repo_path", required=True, help="Path to the repository to document (e.g., '.').")
    parser.add_argument("--branch", required=True, help="The branch to process (e.g., 'main', 'master').")
    parser.add_argument("--file_path", help="Optional: Specific file path to update documentation for.")
    parser.add_argument("--comment", help="Optional: Comment text for updating documentation based on a specific query.")
    
    args = parser.parse_args()
    
    generate_or_update_documentation(args.repo_path, args.branch, args.file_path, args.comment)
