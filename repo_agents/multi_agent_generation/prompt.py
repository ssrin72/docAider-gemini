CODE_CONTEXT_PROMPT = """
First you need to get the content of this file (source code): {file_path}.
Next, gather information on all callee functions within the same file path. 
Understanding these callee functions will help you comprehend the context of the WHOLE file content.
Your task is to generate a concise yet thorough explanation for the file.

Please use the following output template:

The content of the file (source code) is as follows:
`Put the file content here.`

Explanation of Every Class and Function:
`Provide a detailed and thorough description of every class and function, including their purpose, functionality, and any important implementation details.`

Input/Ouput Examples:
Provide input and output examples for each class and function in the file, with detailed explanations.

Called functions information:
`Provide detailed information about called functions, including how each function interacts with other parts of the code, any relationships or dependencies, and the context in which these functions are used.`

"""

DOCUMENTATION_PROMPT = """
You will be provided with the file content, file name, and *additional contextual documentation (including called function info)*.
Based on all this provided information, generate documentation for the source code based on the Standard Markdown Format. DO NOT SKIP any section or subsection of the Standard Format.
The purpose of the documentation is to help developers and beginners understand the function and specific usage of the code. INCLUDE DETAILED description for EVERY CLASS and FUNCTION in the file.
Please add notes for any part that you are confused about or if you have any suggestions to the code.

The file path is: {file_path}

The Standard Markdown Format is as follows:

# {file_name}

## Strategic Purpose and Overview:
PROVIDE A STRATEGIC AND CONTEXTUAL OVERVIEW of the entire file. Explain its primary purpose, how it fits into the broader project structure, and its key components. Describe any important architectural patterns, main data flows, or high-level interactions between its internal components and external dependencies.

## ClassDef NameOfClass or FunctionDef NameOfFunction 

PROVIDE A DETAILED DESCRIPTION of the Class or Function. Include a thorough analysis of its purpose, functionality, and crucial implementation details.
FOR CLASSES: If this class inherits from another class, explain *why* it inherits from that specific parent and what functionality it extends or overrides.
(Detailed and CERTAIN code analysis)

### Method NameOfMethod (method BELONGING to a class)
PROVIDE A DETAILED DESCRIPTION of the Method, including its specific functionality, key components, and critical details. Explain its role within the class and any notable interactions with other methods or attributes.
(Detailed and CERTAIN code analysis)

**Parameters**:

**Returns**:

**Note**: INCLUDE any important considerations, usage notes, or potential pitfalls relevant to this class or Method.

#### Examples:
Provide output/input examples for EACH METHOD.
**Input Examples**: 

```
Provide an input examples for a specified data type (e.g., list, double, int) and include a detailed explanation.
```

**Output Example**:

```
Provide an output example for a specified data type (e.g., list, double, int) and include a detailed explanation.
```

## FunctionDef NameOfFunction (functions that DOES NOT BELONG to a class but are still present in the file)

PROVIDE A DETAILED DESCRIPTION of the function, including its functionality, key components and key details.
(Detailed and CERTAIN code analysis)

**Parameters**:

**Returns**:

**Note**: INCLUDE any important considerations, usage notes, or potential pitfalls relevant to this class or function.

### Examples:
Provide output/input examples for each FUNCTION.
**Input Examples**: 

```
Provide an input examples for a specified data type (e.g., list, double, int) and include a detailed explanation.
```

**Output Example**:

```
Provide an output example for a specified data type (e.g., list, double, int) and include a detailed explanation.
```

## Called_functions:
PROVIDE DETAILED DESCRIPTION of what every called function does, including explanation of the interaction, the context in which it is used, and *how its execution contributes to the overall purpose or functionality* of the current class/function/file. Explain *why* this dependency exists.
"""

FOLDER_OVERVIEW_PROMPT = """
You are an expert AI documentation assistant. Your task is to generate a comprehensive, high-level overview for a given folder or repository, based on the individual documentation of its constituent files. Your goal is to provide a "SCOT" (Strategic, Contextual, Overall, Technical) perspective.

**Context:** You are provided with the paths and generated documentation for several files within a folder or repository. Your task is to synthesize this information into a cohesive, high-level summary that explains the overall purpose of the folder/repo, the relationships and dependencies between the files, and how each file contributes to the folder's collective functionality. Focus on architectural insights, data flow, and key abstractions rather than just listing individual functions.

**Provided File Documentations:**
{files_documentation}

**Instructions:**
Please generate the folder/repository overview in Markdown format, following this structure:

# Folder/Repository Overview: {folder_name}

## Strategic Purpose and Vision:
Explain the overarching goal of this folder/repository within the larger project. What problem does it solve? What is its strategic importance?

## Architectural Overview and Key Components:
Describe the main architectural patterns, design principles, and key components (files, major classes, subsystems) within this folder/repository.

## Inter-file Relationships and Data Flow:
Analyze and describe how the different files within this folder/repository interact with each other. Detail the main data flows, control flows, and dependencies (e.g., File A calls functions in File B, Class C inherits from Class D in another file). Explain *why* these relationships exist and their significance. Use concrete examples if possible.

## Contribution of Each File:
Briefly explain the specific role and contribution of each documented file to the overall functionality of the folder/repository. How do they collectively achieve the strategic purpose?

## Technical Considerations and Best Practices:
Highlight any important technical considerations, design choices, trade-offs, or best practices observed in the folder's implementation.

## Potential Areas for Improvement/Future Work:
Suggest any areas where the folder's structure, design, or implementation could be improved or extended in the future.
"""

REVIEWER_PROMPT = """

This is the generated documentation for the source code. Please check its quality and accuracy, and provide suggestions for improvement. Your Suggestions HAVE TO BE specific and clear, so that the revisor can EASILY understand and implement them WITHOUT the knowledge of codebase.
Note:
1. DO NOT change the documentation, your task is to review and provide suggestions for it.
2. Your suggestions should not contain REMOVE/DELETE instructions.
3. Your suggestions may involve ADDING Function Description for missing functions, Input/Output examples for missing functions to the ##Examples section, or improving the clarity of the documentation.
Please use the following output template:
`Generated documentation`
(-Documentation ends-)

Reviewer agent sugesstions:
`Put your comments and suggestions for improvement here`


"""


REVISOR_PROMPT = """
The file content (source code):
{file_content}
(-Source code ends-)

This is the code-level documentation for the source code:
{generated_documentation}
(-Documentation ends-)

And Reviewer agent's comments/suggestions:
{suggestions}
(-Suggestions ends-)

Please IMPROVE the documentation according to the SUGGESTIONS, which involves adding missing function descriptions, input/output examples, or improving the clarity of the documentation.
DO NOT DELETE/REMOVE any part of the existing documentation unless it's directly addressed by a suggestion.
Your output should be the SAME FORMAT as the existing documentation, with the necessary improvements.
"""
