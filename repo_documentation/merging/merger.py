from typing import List, Tuple
import os

# Define the extension for Markdown files
MD_EXTENSION = '.md'

def create_documentation(docs_folder: str, folder_overview_content: str = "", collected_file_docs: List[Tuple[str, str]] = None, output_filename: str = "index.md") -> str:
    """
    Creates the full documentation for the project, including an overview, table of contents, and individual file documentation.
    
    Args:
        docs_folder (str): The folder where the final documentation will be saved.
        folder_overview_content (str): The markdown content for the repository/folder overview.
        collected_file_docs (List[Tuple[str, str]]): A list of tuples, where each tuple
                                                      contains (relative_file_path, markdown_content)
                                                      for individual files.
        output_filename (str): The desired filename for the generated documentation (e.g., "documentation.md").
    
    Returns:
        str: The full content of the generated documentation.
    """
    os.makedirs(docs_folder, exist_ok=True)
    
    # Generate table of contents based on collected file paths
    # Use collected_file_docs if provided, otherwise default to an empty list
    files_for_toc = [doc[0] for doc in collected_file_docs] if collected_file_docs else []
    
    # Sort by basename
    files_for_toc.sort(key=lambda x: os.path.basename(x))

    # Get table of contents
    tree = to_tree(files_for_toc)
    table_of_contents = get_table_of_contents(tree)

    # Get the documentation content from the collected_file_docs
    documentation_content = get_documentation_content(collected_file_docs)

    # Combine folder overview, table of contents and documentation content
    output = ""
    if folder_overview_content:
        output += f"{folder_overview_content}\n\n---\n\n" # Prepend folder overview

    output += f"# Project Documentation\n\n## Table of Contents\n{table_of_contents}\n\n{documentation_content}"

    # Write the combined content to the output file
    output_file = os.path.join(docs_folder, output_filename)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"Final documentation has been generated in {output_file}")
    return output

def create_file_card(file_path: str, docs: str):
    # Remove file extensions for display purposes
    file_name_display = file_path.replace('\\', '/').replace(MD_EXTENSION, '')
    # Format as a Markdown section
    return f"\n---\n\n## {file_name_display}\n\n{docs}\n"

def get_table_of_contents(tree, indent_level=0, prefix=""):
    table_of_contents = ""
    indent_space = "    " * indent_level

    # Separate directories and files
    directories = []
    files = []
    for key, value in tree.items():
        if key == 'files':
            files.extend(value)
        elif isinstance(value, dict):
            directories.append((key, value))
        else:
            files.append(key)

    # Sort directories alphabetically
    directories.sort(key=lambda x: x[0].lower())

    # Sort files alphabetically
    files.sort(key=str.lower)

    # Handle directories first
    for key, value in directories:
        table_of_contents += f'{indent_space}* 📁 {key}\n'
        table_of_contents += get_table_of_contents(value, indent_level + 1, prefix + key + "/")

    # Then handle files
    for file in files:
        # For TOC, link to the relevant section within the same markdown file
        link_text = os.path.basename(file).replace(MD_EXTENSION, '')
        anchor = link_text.lower().replace(' ', '-').replace('_', '-') # Basic slugification for markdown anchor
        table_of_contents += f'{indent_space}* 🐍 [{link_text}](#{anchor})\n'

    return table_of_contents

def get_documentation_content(collected_file_docs: List[Tuple[str, str]]):
    documentation_content = ""
    # Ensure collected_file_docs is not None before iterating
    if collected_file_docs:
        for relative_path, doc_content in collected_file_docs:
            # Create file card (as Markdown section) for each file using collected content
            documentation_content += create_file_card(relative_path, doc_content)
    return documentation_content

def to_tree(files):
    tree = {'files': []}
    for path in files:
        parts = path.split(os.sep)
        current = tree
        for part in parts[:-1]:
            if part not in current:
                current[part] = {'files': []}
            current = current[part]
        if parts[-1]:
            current['files'].append(parts[-1])
    return tree
