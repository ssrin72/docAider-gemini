import os
from dotenv import load_dotenv
from repo_agents.multi_agent_generation.multi_agent_conversation import
multi_agent_documentation_generation

def main():
    """
    Main function to run the documentation generation test.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Define the file to be documented
    # Using 'file.py' as an example.
    # Make sure this file exists at the root of your project.
    file_to_document = "file.py"

    if not os.path.exists(file_to_document):
        print(f"Error: The file '{file_to_document}' does not exist.")
        print("Please create it or change the 'file_to_document' variable to an
existing file.")
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