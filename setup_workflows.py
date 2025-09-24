import os
from workflows import update_docs_workflow_content, update_comments_workflow_content


def create_workflow():
    os.makedirs('/.github/workflows', exist_ok=True)
    with open('/.github/workflows/update-docs.yml', 'w') as f:
        f.write(update_docs_workflow_content)
    with open('/.github/workflows/update-comments.yml', 'w') as f:
        f.write(update_comments_workflow_content)
    
        
if __name__ == "__main__":
    print("Creating workflows...")
    create_workflow()
    print("Finished creating workflows: update-docs.yml and update-comments.yml ")