from autogen import AssistantAgent, UserProxyAgent
from repo_documentation.prompt import USR_PROMPT
from . import config


def load_assistant_agent():
    # Load the assistant agent for LLM-based documentation generation
    return AssistantAgent(
        name="assistant",
        system_message=USR_PROMPT,
        llm_config=config.llm_config,
        human_input_mode="NEVER"
    )


def initiate_chat(user: UserProxyAgent, assistant, prompt):
    user.initiate_chat(
        assistant,
        message=prompt,
        max_turns=1,
        silent=True
    )
