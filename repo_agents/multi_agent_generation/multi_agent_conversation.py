import os
import asyncio
from autogen import ConversableAgent, register_function
import gemini_settings as ai_service_settings
from repo_agents.multi_agent_generation.code_context_agent import CodeContextAgent
from repo_agents.multi_agent_generation.prompt import DOCUMENTATION_PROMPT, REVIEWER_PROMPT, REVISOR_PROMPT, REPO_DOCUMENTATION_PROMPT
from repo_documentation.utils import Mode, save_prompt_debug, read_file_content
import os
import asyncio
from autogen import ConversableAgent, register_function
import gemini_settings as ai_service_settings
from repo_agents.multi_agent_generation.code_context_agent import CodeContextAgent
from repo_agents.multi_agent_generation.prompt import DOCUMENTATION_PROMPT, REVIEWER_PROMPT, REVISOR_PROMPT, OVERALL_DOCS_SUMMARY_PROMPT
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
# This output_folder is for debug logs related to the multi-agent conversation itself
output_folder = os.path.join(root_folder, "docs_output") 

# Initialize CodeContextAgent with the cloned repo's root folder
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

def generate_overall_repo_documentation_from_markdowns(
    repo_name: str, repo_root_path: str, all_md_contents: dict
) -> str:
    """
    Generates overall documentation for the entire repository by summarizing
    the provided individual markdown documentation files.
    """
    formatted_md_contents = []
    for relative_path, content in all_md_contents.items():
        # Truncate content for prompt to avoid exceeding token limits,
        # or find a smarter way to summarize it if content is very long.
        truncated_content = content[:1000] # Use more characters to give better context
        if len(content) > 1000:
            truncated_content += "\n... (documentation truncated) ..."
        formatted_md_contents.append(f"### `{relative_path}`\n```markdown\n{truncated_content}\n```")

    individual_docs_summary_for_prompt = "\n\n".join(formatted_md_contents)

    print(f"DEBUG: Generating overall repo documentation from {len(all_md_contents)} individual markdown files.")

    chat_result = agent_manager.initiate_chats(
        [
            {
                "recipient": documentation_generation_agent,
                "message": OVERALL_DOCS_SUMMARY_PROMPT.format(
                    repo_name=repo_name,
                    repo_root_path=repo_root_path,
                    individual_docs_summary=individual_docs_summary_for_prompt
                ),
                "max_turns": 3, # Allow more turns for synthesis
                "summary_method": "last_msg",
            },
            {
                "recipient": review_agent,
                "message": REVIEWER_PROMPT, # Reviewer for the overall doc
                "max_turns": 1,
                "summary_method": "last_msg",
            },
            {
                "recipient": revise_agent,
                "message": REVISOR_PROMPT.format(file_content=""), # File content not applicable here
                "max_turns": 1,
                "summary_method": "last_msg",
            },
        ]
    )
    
    # Save prompt text for debug
    save_prompt_debug(output_folder, "overall_repo_summary_generation_agent_prompt", chat_result[0].chat_history[2]["content"], Mode.CREATE)
    save_prompt_debug(output_folder, "overall_repo_summary_reviewer_agent_prompt", chat_result[1].chat_history[0]["content"], Mode.CREATE)
    save_prompt_debug(output_folder, "overall_repo_summary_revisor_agent_prompt", chat_result[2].chat_history[0]["content"], Mode.CREATE)
    
    final_documentation_content = chat_result[2].chat_history[-1]["content"]
    print(f"DEBUG: Final overall repository documentation content:")
    print("--- START OVERALL AGENT OUTPUT ---")
    print(final_documentation_content)
    print("--- END OVERALL AGENT OUTPUT ---")
    return final_documentation_content

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
