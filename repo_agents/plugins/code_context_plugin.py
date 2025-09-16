import os
from repo_agents.ast_agent import ASTAgent
from langchain.tools import tool

ast_helper = ASTAgent()

@tool
def get_file_content(file_path: str) -> str:
    """Gets the content of a file"""
    with open(file_path, "r") as file:
        return file.read()

@tool
def get_callee_function_info(file_path: str) -> str:
    """Gets callee function info"""
    return ast_helper.get_callee_function_info(file_path)
