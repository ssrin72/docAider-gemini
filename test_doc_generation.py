import os
import sys

# Add local code2flow clone to Python's path
# This ensures that the cloned repository is used for imports.
sys.path.insert(0, os.path.abspath("code2flow"))

from dotenv import load_dotenv
from repo_agents.multi_agent_generation.multi_agent_conversation import multi_agent_documentation_generation

def main():
    """
    Main function to run the documentation generation test.
    """
    # Load environment variables from .env file
    load_dotenv()

    if len(sys.argv) < 2:
        print("Usage: python test_doc_generation.py <file_path>")
        sys.exit(1)
    
    file_to_document = sys.argv[1]

    if not os.path.exists(file_to_document):
        print(f"Error: The file '{file_to_document}' does not exist.")
        return

    print(f"Generating documentation for: {file_to_document}")

    # Generate the documentation
    try:
        documentation = multi_agent_documentation_generation(file_to_document)
        print("\n--- Generated Documentation ---")
        print(documentation)
        print("---------------------------\n")
        print("Documentation generation complete.")
    except Exception as e:
        print(f"An error occurred during documentation generation: {e}")

if __name__ == "__main__":
    main()
