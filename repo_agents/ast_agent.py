import os
import code2flow
from code2flow.code2flow import utils as graph_utils
from repo_documentation.utils import get_additional_docs_calls

class ASTAgent:
  """
  This agent performs Abstract Syntax Tree (AST) analysis and generates a call graph of files.
  """
  def __init__(self, root_folder: str = None) -> None:
    if root_folder:
      self.root_folder = root_folder
    else:
      self.root_folder = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    
    self.output_folder = os.path.join(self.root_folder, "docs_output")
    os.makedirs(self.output_folder, exist_ok=True) # Ensure output directory exists

    graph_utils.generate_graph(self.root_folder, self.output_folder)
    self.graph = graph_utils.get_call_graph(self.output_folder)
    self.file_to_calls = graph_utils.get_file_to_functions(self.graph)
    self.bfs_explore = graph_utils.explore_call_graph(self.graph)

    # Explicitly find all Python files in the repository
    print(f"DEBUG: ASTAgent root_folder: {self.root_folder}")
    self._all_python_files_in_repo = self._find_all_python_files(self.root_folder)
    print(f"DEBUG: _find_all_python_files returned: {self._all_python_files_in_repo}")


  def _find_all_python_files(self, directory):
      """
      Walks the directory and returns a list of all Python file paths,
      relative to the self.root_folder.
      """
      python_files = []
      for root, _, files in os.walk(directory):
          for file in files:
              if file.endswith(".py"):
                  relative_path = os.path.relpath(os.path.join(root, file), self.root_folder)
                  python_files.append(relative_path)
      return python_files

  def get_callee_function_info(self, file_path) -> str:
    """
    Returns callee functions in a file.
    If the file_path is not in self.file_to_calls (meaning code2flow didn't find specific calls),
    it returns an empty list of calls.
    """
    calls = self.file_to_calls.get(file_path, [])
    callee_function_info = get_additional_docs_calls(calls, self.graph, self.bfs_explore)
    return callee_function_info
  
  def get_file_call_dict(self) -> dict:
    """
    Returns a dict mapping: (file, callee functions).
    It combines files identified by code2flow with all Python files found in the repository.
    For files found only by walking the directory, their value will be an empty list of calls.
    """
    combined_file_dict = self.file_to_calls.copy()

    for relative_path in self._all_python_files_in_repo:
        if relative_path not in combined_file_dict:
            combined_file_dict[relative_path] = []
    
    print(f"DEBUG: Final combined_file_dict keys: {list(combined_file_dict.keys())}")
    return combined_file_dict
