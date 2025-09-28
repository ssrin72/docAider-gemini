import os
import asyncio
from autogen import ConversableAgent, register_function
import gemini_settings as ai_service_settings
from repo_agents.multi_agent_generation.code_context_agent import CodeContextAgent
from repo_agents.multi_agent_generation.prompt import DOCUMENTATION_PROMPT, REVIEWER_PROMPT, REVISOR_PROMPT, FOLDER_OVERVIEW_PROMPT
from repo_documentation.utils import Mode, save_prompt_debug, read_file_content
from autogen_utils.utils import initiate_chat, last_message, load_user_agent
from typing import Annotated

"""
Multi-agent conversation pattern: sequential chats
Code context agent: provides description and explanation for code context (optional)
Documentation generation agent: generates documentation for the code
Review agent: checks the quality of generated documentation and provides improvement suggestions
Revise agent: Revises the documentation based on the reviewer's comments
Agent manager: is the mediator of the conversation
"""

code_context_agent = CodeContextAgent()

documentation_generation_agent = ConversableAgent(
  name="documentation_generation_agent",
  system_message="""You are an AI documentation assistant. Your primary task is to generate comprehensive code-level documentation following a specified Markdown format.
You will be provided with the file content, file name, and *additional contextual documentation (including called function info)*.
Your task is to use ALL this information to generate the documentation according to the provided Markdown format.
DO NOT attempt to call any external tools; the necessary context will be provided to you directly.
""",
  llm_config={**ai_service_settings.autogen_llm_config, "max_tokens": 4096}, # Override max_tokens for longer responses
  human_input_mode="NEVER"
)

review_agent = ConversableAgent(
  name="documentation_reviewer",
  system_message="You are a documentation reviewer for code level documentation who can check the quality of the generated documentation and improve it.",
  llm_config=ai_service_settings.autogen_llm_config,
  human_input_mode="NEVER"
)

revise_agent = ConversableAgent(
  name="documentation_revisor",
  system_message="You are a documentation revisor who can revise the documentation based on the review agent's suggestions. Only revise the suggested parts. DO NOT DELETE/REMOVE any part of the existing documentation that is not explicitly suggested for revision.",
  llm_config=ai_service_settings.autogen_llm_config,
  human_input_mode="NEVER"
)

agent_manager = ConversableAgent(
  name="agent_manager",
  llm_config=False,
  human_input_mode="NEVER"
)

# Initialize UserProxyAgent for chat initiation
user_proxy = load_user_agent()

def code_context_explainer(
  file_path: Annotated[str, "The file path"]
) -> Annotated[str, "The code context description"]:
  """
  This function calls the method `code_context_agent.code_context_explanation`.
  The purpose is to register the function to agents.
  This encapsulation is necessary because agents can only call functions, but not methods.
  """
  return asyncio.run(code_context_agent.code_context_explanation(file_path))

# Tool use: register functions to agents
# Tool use: register functions to agents
# The code_context_explainer is called directly in multi_agent_documentation_generation
# to populate 'additional_docs' in the prompt. The documentation_generation_agent
# should not attempt to call it as a tool during the chat, as this can lead to
# "Function not found" errors if the LLM hallucinates incorrect arguments or calls it redundantly.
# Removing this registration prevents the agent from attempting to call it.

def multi_agent_documentation_generation(file_path) -> str:
  # Ensure ASTAgent uses the correct root and output folders, and reset its graph status
  global code_context_agent # Declare global for the correct instance name
  code_context_agent.root_folder = os.getenv("ROOT_FOLDER", ".")
  code_context_agent.output_folder = os.path.join(os.getenv("ROOT_FOLDER", "."), "docs_output")
  code_context_agent._graph_generated = False 

  file_content = read_file_content(file_path)
  file_name = os.path.basename(file_path)

  additional_docs = ""
  try:
    additional_docs = code_context_explainer(file_path)
    print(f"AST analysis for {file_name} completed.")
  except Exception as e:
    print(f"Warning: AST analysis for {file_name} failed: {e}. Proceeding without additional context from AST.")
  
  # Use the imported DOCUMENTATION_PROMPT directly
  prompt = DOCUMENTATION_PROMPT.format(
    file_path=file_path,
    file_name=file_name,
    file_content=file_content,
    additional_docs=additional_docs
  )

  chat_result_gen = initiate_chat(user_proxy, documentation_generation_agent, prompt, max_turns=50) # Increased turns
  
  if chat_result_gen is None or not hasattr(chat_result_gen, 'chat_history') or not chat_result_gen.chat_history:
      print(f"Error: Documentation generation chat for {file_name} failed or returned empty chat history.")
      return "Error: Documentation generation failed."

  documentation = last_message(documentation_generation_agent)

  # Review and revise loop
  review_prompt = REVIEWER_PROMPT.format(Generated_documentation=documentation)
  chat_result_review = initiate_chat(user_proxy, review_agent, review_prompt, max_turns=50) # Increased turns
  
  if chat_result_review is None or not hasattr(chat_result_review, 'chat_history') or not chat_result_review.chat_history:
      print(f"Warning: Review chat for {file_name} failed or returned empty chat history. Skipping revision.")
      suggestions = "" # Treat as no suggestions if review failed
  else:
      suggestions = last_message(review_agent)

  final_documentation = documentation # Default to original if no revision occurs

  if "no suggestion" not in suggestions.lower() and "no suggestions" not in suggestions.lower() and "no feedback" not in suggestions.lower() and suggestions:
    revise_prompt = REVISOR_PROMPT.format(
      file_content=file_content,
      generated_documentation=documentation, # Corrected variable name
      suggestions=suggestions
    )
    chat_result_revise = initiate_chat(user_proxy, revise_agent, revise_prompt, max_turns=50) # Increased turns
    
    if chat_result_revise is None or not hasattr(chat_result_revise, 'chat_history') or not chat_result_revise.chat_history:
        print(f"Warning: Revision chat for {file_name} failed or returned empty chat history. Using original documentation.")
    else:
        revised_documentation = last_message(revise_agent)
        final_documentation = revised_documentation
  
  # Save prompt text for debug (using chat_result_gen, chat_result_review, chat_result_revise)
  root_folder = os.path.abspath(os.getenv("ROOT_FOLDER"))
  output_folder = os.path.join(root_folder, "docs_output")
  
  # Ensure chat_result_gen is valid before accessing chat_history for debug logging
  if chat_result_gen and hasattr(chat_result_gen, 'chat_history') and len(chat_result_gen.chat_history) > 2:
      save_prompt_debug(output_folder, file_path + "_generation_agent", chat_result_gen.chat_history[2]["content"], Mode.CREATE)
  else:
      print(f"Warning: Could not save generation agent debug prompt for {file_name} due to invalid chat_result_gen.")

  # Ensure chat_result_review is valid before accessing chat_history for debug logging
  if chat_result_review and hasattr(chat_result_review, 'chat_history') and chat_result_review.chat_history:
      save_prompt_debug(output_folder, file_path + "_reviewer_agent", chat_result_review.chat_history[0]["content"], Mode.CREATE)
  else:
      print(f"Warning: Could not save reviewer agent debug prompt for {file_name} due to invalid chat_result_review.")

  # Only save revisor debug if revision actually happened AND chat_result_revise is valid
  if ("no suggestion" not in suggestions.lower() and "no suggestions" not in suggestions.lower() and "no feedback" not in suggestions.lower() and suggestions) and \
     chat_result_revise and hasattr(chat_result_revise, 'chat_history') and chat_result_revise.chat_history:
      save_prompt_debug(output_folder, file_path + "_revisor_agent", chat_result_revise.chat_history[0]["content"], Mode.CREATE)
  else:
      if final_documentation != documentation: # If revision was attempted but failed to log
          print(f"Warning: Revision was attempted for {file_name} but could not save revisor agent debug prompt.")
          
  return final_documentation

def multi_agent_documentation_generation_for_folder(folder_name: str, files_documentation: str) -> str:
  """
  Generates a high-level overview for a folder/repository using the multi-agent system.
  """
  prompt = FOLDER_OVERVIEW_PROMPT.format(
      folder_name=folder_name,
      files_documentation=files_documentation
  )

  # Use the documentation generation agent for the folder overview as well
  chat_result = initiate_chat(user_proxy, documentation_generation_agent, prompt, max_turns=50) # Increased turns for folder overview

  if chat_result is None or not hasattr(chat_result, 'chat_history') or not chat_result.chat_history:
      print(f"Error: Folder overview chat for {folder_name} failed or returned empty chat history.")
      return "Error: Folder overview generation failed."

  folder_overview = last_message(documentation_generation_agent)
  return folder_overview
