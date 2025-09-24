import os
import chardet
from github import Github, Auth
from langchain.tools import tool

g = Github(auth=Auth.Token(os.getenv("GITHUB_ACCESS_TOKEN")))

def _is_ascii(decoded_content):
    """
    Returns True if the decoded_content is ASCII, False otherwise.
    """
    result = chardet.detect(decoded_content)
    encoding = result["encoding"]
    return encoding == "ascii"

@tool
def get_all_repos() -> list:
    """Gets all of my repositories"""
    repos = []
    for repo in g.get_user().get_repos():
        repos.append(repo.name)
    return repos

@tool
def get_repo_owner(repo_name: str) -> str:
    """Gets the owner of the repository"""
    for repo in g.get_user().get_repos():
        if repo.name == repo_name:
            return repo.owner.login
    return "Owner not found"

@tool
def get_branches(repo_name: str) -> list:
    """Gets all branches of the repository"""
    repo_owner = get_repo_owner(repo_name)
    branches = []
    for b in g.get_repo(f"{repo_owner}/{repo_name}").get_branches():
        branches.append(b.name)
    return branches

@tool
def get_all_files_in_repo(repo_name: str) -> list:
    """Returns all of the files in a repository (Including submodules)."""
    repo_owner = get_repo_owner(repo_name)
    repo = g.get_repo(f"{repo_owner}/{repo_name}")
    contents = repo.get_contents("")
    files = []
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        else:
            files.append(file_content.path)
    return files

@tool
def get_file_content(file_name: str, repo_name: str) -> str:
    """Returns the content of a file in the repo."""
    repo_owner = get_repo_owner(repo_name)
    repo = g.get_repo(f"{repo_owner}/{repo_name}")
    decoded_content = repo.get_contents(file_name).decoded_content
    if _is_ascii(decoded_content):
        return decoded_content.decode("utf-8")
    else:
        return ""
