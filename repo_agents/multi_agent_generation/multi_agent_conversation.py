import os
import asyncio
from autogen import ConversableAgent, register_function
import gemini_settings as ai_service_settings
from repo_agents.multi_agent_generation.code_context_agent import CodeContextAgent
from repo_agents.multi_agent_generation.prompt import DOCUMENTATION_PROMPT, REVIEWER_PROMPT, REVISOR_PROMPT, REPO_DOCUMENTATION_PROMPT
from repo_documentation.utils import Mode, save_prompt_debug, read_file_content
from typing import Annotated

"""
Multi-agent conversation pattern: sequential chats
Code context agent: provides description and explanation for code context (optional)
Documentation generation agent: generates documentation for the code
Review agent: checks the quality of generated documentation and provides improvement suggestions
Revise agent: Revises the documentation based on the reviewer's comments
Agent manager: is the mediator of the conversation
"""

# The root_folder for agents will now be the cloned repo's root when processing
root_folder = os.path.abspath(os.getenv("ROOT_FOLDER"))
output_folder = os.path.join(root_folder, "docs_output") # This output_folder is for debug logs

# CodeContextAgent might not be directly used for overall repo documentation,
# but keeping it here for its call graph generation capability which might be useful
# for understanding file relationships, though not explicitly used in this flow for prompting.
code_context_agent = CodeContextAgent(root_folder=root_folder)

documentation_generation_agent = ConversableAgent(
  name="documentation_generation_agent",
  system_message="You are an AI documentation assistant, and your task is to generate comprehensive documentation.",
  llm_config=ai_service_settings.autogen_llm_config,
  human_input_mode="NEVER"
)

review_agent = ConversableAgent(
  name="documentation_reviewer",
  system_message="You are a documentation reviewer who can check the quality of the generated documentation and improve it.",
  llm_config=ai_service_settings.autogen_llm_config,
  human_input_mode="NEVER"
)

revise_agent = ConversableAgent(
  name="documentation_revisor",
  system_message="You are a documentation revisor who can revise the documentation based on the review agent's suggestions",
  llm_config=ai_service_settings.autogen_llm_config,
  human_input_mode="NEVER"
)

agent_manager = ConversableAgent(
  name="agent_manager",
  llm_config=False,
  human_input_mode="NEVER"
)

def _find_all_python_files(directory):
    """
    Walks the directory and returns a list of all Python file paths,
    relative to the given directory.
    """
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                relative_path = os.path.relpath(os.path.join(root, file), directory)
                python_files.append(relative_path)
    return python_files

def generate_overall_repo_documentation(repo_root_path: str) -> str:
  """
  Generates overall documentation for the entire repository.
  """
  # Find all Python files in the repository
  repo_file_list = _find_all_python_files(repo_root_path)
  formatted_file_list = "\n".join([f"- `{f}`" for f in repo_file_list])

  print(f"DEBUG: Files identified for overall repo documentation: {formatted_file_list}")

  chat_result = agent_manager.initiate_chats(
    [
      {
        "recipient": documentation_generation_agent,
        "message": REPO_DOCUMENTATION_PROMPT.format(
          repo_root_path=repo_root_path,
          repo_file_list=formatted_file_list
        ),
        "max_turns": 2, # Allow multiple turns for generation
        "summary_method": "last_msg",
      },
      {
        "recipient": review_agent,
        "message": REVIEWER_PROMPT,
        "max_turns": 1,
        "summary_method": "last_msg",
      },
      {
        "recipient": revise_agent,
        "message": REVISOR_PROMPT.format(file_content=""), # File content is not relevant for overall repo doc revision
        "max_turns": 1,
        "summary_method": "last_msg",
      },
    ]
  )
  
  # Save prompt text for debug
  # Note: The debug output_folder here might be problematic if not explicitly set to the final output dir.
  # For overall repo doc, we might want a dedicated debug folder or handle paths carefully.
  # For now, let's keep it consistent with the existing `output_folder` variable.
  save_prompt_debug(output_folder, "overall_repo_generation_agent_prompt", chat_result[0].chat_history[2]["content"], Mode.CREATE)
  save_prompt_debug(output_folder, "overall_repo_reviewer_agent_prompt", chat_result[1].chat_history[0]["content"], Mode.CREATE)
  save_prompt_debug(output_folder, "overall_repo_revisor_agent_prompt", chat_result[2].chat_history[0]["content"], Mode.CREATE)
  
  final_documentation_content = chat_result[2].chat_history[-1]["content"]
  print(f"DEBUG: Final overall repository documentation content:")
  print("--- START AGENT OUTPUT ---")
  print(final_documentation_content)
  print("--- END AGENT OUTPUT ---")
  return final_documentation_content

# The old multi_agent_documentation_generation is kept for backward compatibility if needed elsewhere.
# However, multi_agent_app.py will now call generate_overall_repo_documentation.
def multi_agent_documentation_generation(file_path) -> str:
  file_content = read_file_content(file_path)

  chat_result = agent_manager.initiate_chats(
    [
      {
        "recipient": documentation_generation_agent,
        # Context: the prompt, including instructions and doc template,
        # Carryover: the output of the code context agent.
        "message": DOCUMENTATION_PROMPT.format(
          file_path=file_path,
          file_name=os.path.basename(file_path),
          file_content=file_content # Pass file content
        ),
        "max_turns": 2,
        "summary_method": "last_msg",
      },
      {
        "recipient": review_agent,
        # Context: the source code,
        # Carryover: the output of the doc gen agent.
        "message": REVIEWER_PROMPT,
        "max_turns": 1,
        "summary_method": "last_msg",
      },
      {
        "recipient": revise_agent,
        # Context: None,
        # Carryover: the documentation.
        "message": REVISOR_PROMPT.format(file_content=file_content),
        "max_turns": 1,
        "summary_method": "last_msg",
      },
    ]
  )
  # Save prompt text for debug
  save_prompt_debug(output_folder, file_path + "_generation_agent", chat_result[0].chat_history[2]["content"], Mode.CREATE)
  save_prompt_debug(output_folder, file_path + "_reviewer_agent", chat_result[1].chat_history[0]["content"], Mode.CREATE)
  save_prompt_debug(output_folder, file_path + "_revisor_agent", chat_result[2].chat_history[0]["content"], Mode.CREATE)
  
  final_documentation_content = chat_result[2].chat_history[-1]["content"]
  print(f"DEBUG: Final documentation content for {file_path}:")
  print("--- START AGENT OUTPUT ---")
  print(final_documentation_content)
  print("--- END AGENT OUTPUT ---")
  return final_documentation_content
