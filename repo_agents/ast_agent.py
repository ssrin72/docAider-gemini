import os
from code2flow.code2flow import utils as graph_utils
from repo_documentation.utils import get_additional_docs_calls

class ASTAgent:
  """
  This agent performs Abstract Syntax Tree (AST) analysis and generates a call graph of files.
  """
  def __init__(self) -> None:
    self.root_folder = os.getenv("ROOT_FOLDER")
    if not self.root_folder or self.root_folder == "/":
        # Fallback to project root if ROOT_FOLDER is not set or is invalid.
        # This makes the path relative to this file's location.
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.root_folder = project_root
    else:
        self.root_folder = os.path.abspath(self.root_folder)

    self.output_folder = os.path.join(self.root_folder, "docs_output")
    graph_utils.generate_graph(self.root_folder, self.output_folder)
    self.graph = graph_utils.get_call_graph(self.output_folder)
    self.file_to_calls = graph_utils.get_file_to_functions(self.graph)
    self.bfs_explore = graph_utils.explore_call_graph(self.graph)

  def get_callee_function_info(self, file_path) -> str:
    """
    Returns callee functions in a file
    """
    calls = self.file_to_calls[file_path]
    callee_function_info = get_additional_docs_calls(calls, self.graph, self.bfs_explore)
    return callee_function_info
  
  def get_file_call_dict(self) -> dict:
    """
    Returns a dict mapping: (file, callee functions)
    """
    return self.file_to_calls
