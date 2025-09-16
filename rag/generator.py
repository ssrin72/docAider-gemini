import sys, os
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)
from dotenv import load_dotenv
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.google import GoogleGeminiChatCompletion, GoogleGeminiPromptExecutionSettings
from semantic_kernel.prompt_template import PromptTemplateConfig
from repo_documentation.prompt import DOCUMENTATION_PROMPT
from exceptions import SemanticKernelError

load_dotenv(dotenv_path="../.env")

class DocumentationGenerator():
  """
  This class implements the RAG architecture for generating documentation for the code.
  It uses a retriever to get context information and uses a LLM-based generator to generate documentation.
  Semantic Kernel is central of the implementation.
  """
  def __init__(self):
    """
    Initialize a new instance of the DocumentationGenerator class
    """
    self.kernel = Kernel()
    self.chat_service_id = "documentation_generation"
    self.prompt = ""

    self._init()

  def _init(self):
    """
    Initialse kernel services and retrievers
    """
    # Add a chat completion service
    gemini_completion = GoogleGeminiChatCompletion(
        service_id=self.chat_service_id,
        model_id="gemini-2.5-pro",
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    self.kernel.add_service(gemini_completion)

  async def generate_documentation(self, file_path, file_content, root_folder, additional_docs) -> str:
    """
    This is a plugin function, which generates documentation for code.

    Args:
      file_path: the name of the source file.
      file_content: the source code.
      root_folder: the root folder of the repository.
      additional_docs: the additional docs.
    
    Returns:
      LLM-generated documentation in string
    """

    file_name = os.path.basename(file_path)
    prompt = DOCUMENTATION_PROMPT.format(
      file_name=file_name,
      file_content=file_content,
      root_folder=root_folder,
      additional_docs=additional_docs
    )
    self.prompt = prompt

    # Configure execution settings
    execution_settings = GoogleGeminiPromptExecutionSettings(
      temperature=0
    )

    # Configure the prompt template
    prompt_template_config = PromptTemplateConfig(
      template=prompt,
      name="documentation-generation",
      template_format="semantic-kernel",
      execution_settings=execution_settings
    )

    # Add summarization function to the kernel
    documentation_generator = self.kernel.add_function(
      function_name="documentation_generation",
      plugin_name="documentation_generator",
      prompt_template_config=prompt_template_config,
    )

    # Invoke kernel to generate documentation
    try:
      documentation = str(await self.kernel.invoke(documentation_generator))
      # Save documentation to the database
      print(f"Documentation generated for {file_name}.")
      return documentation
    except:
      raise SemanticKernelError(f"The generation for {file_name} failed. Please check kernel configurations and try again.")
