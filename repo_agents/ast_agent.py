import os
import code2flow
from code2flow.code2flow import utils as graph_utils
from repo_documentation.utils import get_additional_docs_calls

class ASTAgent:
  """
  This agent performs Abstract Syntax Tree (AST) analysis and generates a call graph of files.
  """
  def __init__(self, root_folder: str = None, output_dir: str = None) -> None:
    self._initial_root_folder_arg = root_folder
    self._initial_output_dir_arg = output_dir

    self.root_folder = None
    self.output_folder = None
    self.graph = None
    self.file_to_calls = None
    self.bfs_explore = None
    self._graph_generated = False # Flag to track if graph has been generated

  def _ensure_graph_generated(self):
    if self._graph_generated:
      return

    # Resolve root_folder
    root_folder = self._initial_root_folder_arg
    if root_folder is None:
        root_folder = os.getenv("ROOT_FOLDER")
        if not root_folder:
            # Default to the project's root if ROOT_FOLDER env var is not set
            root_folder = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    self.root_folder = os.path.abspath(root_folder)

    # Resolve output_folder
    output_dir = self._initial_output_dir_arg
    if output_dir is None:
        # If output_dir is not provided, default to a temporary directory within the current working directory.
        output_dir = os.path.join(os.getcwd(), "temp_ast_output")
    self.output_folder = os.path.abspath(output_dir)
    
    os.makedirs(self.output_folder, exist_ok=True)
    
    # Generate graph.
    graph_utils.generate_graph(self.root_folder, self.output_folder)
    
    try:
        self.graph = graph_utils.get_call_graph(self.output_folder)
    except Exception as e:
        self.graph = {}
        print(f"Warning: Failed to load call graph from {self.output_folder}: {e}")
    
    self.file_to_calls = graph_utils.get_file_to_functions(self.graph)
    self.bfs_explore = graph_utils.explore_call_graph(self.graph)
    self._graph_generated = True

  def get_callee_function_info(self, file_path: str) -> str:
    """
    Returns callee functions in a file.
    For non-Python files, this currently returns an empty string as AST analysis (code2flow) is Python-specific.
    """
    if not file_path.lower().endswith(".py"):
        # This message is now printed in multi_agent_app.py, so we just return an empty string here.
        return ""

    self._ensure_graph_generated() # Ensure graph is generated before accessing it
    if not self.graph: # If graph generation failed, return empty info
        # This warning is also now handled in multi_agent_app.py
        return ""
    
    calls = self.file_to_calls.get(file_path, [])
    if not calls:
        return "" # No calls found for this file

    callee_function_info = get_additional_docs_calls(calls, self.graph, self.bfs_explore)
    return callee_function_info
  
  def get_file_call_dict(self) -> dict:
    """
    Returns a dict mapping: (file, callee functions)
    """
    self._ensure_graph_generated() # Ensure graph is generated before accessing it
    return self.file_to_calls
