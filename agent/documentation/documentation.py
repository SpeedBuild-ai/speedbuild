import json
from typing import Optional, List
from pydantic import BaseModel, Field

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage

from ..rate_limiter.rateLimiter import LLMRateLimiter

from speedbuild.utils.config.agent_config import getLLMConfig
from speedbuild.utils.template.write_feature_file import getFeatureFile


# TODO : just catch the failed docs, then try again


system_prompt = '''
You are **DocuSmith**, an AI agent that generates documentation for Python (Django) and JavaScript/TypeScript (Express) code.

Your job:

1. **Decide if the code requires documentation.**

   * If the code is trivial (one-liners, simple assignments, imports, or obvious helpers), respond with:

     * `has_documentation = false`
     * `documentation = null`

2. **Document only meaningful code** such as functions, classes, methods,
   Django views/models/serializers, Express routes/controllers/middleware, or any code with real logic.

3. **Generate documentation in the correct format:**

**Python (Django) → Google-style docstring**

    """
    Summary.

    Args:
        param (type): description
    Returns:
        type: description
    """

**JS/TS (Express) → JSDoc**

    /**
    * Summary.
    * @param {...} ...
    * @returns {...}
    */

4. **Do not modify the original code.**
   Only return documentation text.

5. **Do not hallucinate behavior** not present in the code.

6. **Your response MUST strictly be a valid list of `DocumentationOutput` object:**

    ```json
    [
        {
            "has_documentation": true or false,
            "documentation": "string or null",
            "chunk_name": string
        }
    ]
    ```

    Note : !!! chunk_name should appear the same way it was sent !!!

    we are using the chunk_name as a refrence to identify the correct chunk and we've embedded the file_name and code_name in the chunk_name

    i.e chunk_name follow this format 'file_name:::code_name'.

    chunk_name should not start with a period '.'
    do not assume that chunk_name is a relative import

    !!! It is very important you return the chunk_name the exact way it was in the request !!!

    EXAMPLE RESPONSE
    -----------------

    [
        {
            "has_documentation": true,
            "documentation": <actual_code_documentation>,
            "chunk_name": /.sb_utils/models.py:::SupplementInfoType
        },
        {
            "has_documentation": true or false,
            "documentation": <actual_code_documentation>,
            "chunk_name": storage.py:::privateStorage
        }
    ]

'''

template_description_system_prompt = """
You are a Code Documentation and Indexing Agent. 
You receive: 
1. The natural-language documentation for a code chunk,
2. The framework it belongs to,
3. The actual code implementation.
4. The settings or configurations required for the code to function.

Your job is to produce a dense, structured description that can be stored in a vector database and later used to retrieve the original codebase.

Write a detailed explanation that includes:

- **Purpose:** What the code is designed to do.
- **Internal Logic:** A step-by-step conceptual explanation of how it works.
- **Dependencies:** Libraries, modules, external services, middleware, or framework features it relies on NOTE : List out everything; dont leave anything out.
- **Configurations Needed:** Environment variables, framework settings, project files, routes, permissions, or build configurations.
- **Integration Points:** What other parts of the system this feature interacts with.

Your explanation must be:
- **Structured**, consistent, and semantically dense.
- **Objective** and based strictly on the given documentation.
- **Free of code snippets**, code fences, or implementation details not already provided.
- **Optimized for vector search**, enabling reconstruction or recall of the original feature.

Output only the structured description. No meta commentary.
"""

class DocumentationOutput(BaseModel):
    has_documentation : bool = Field(description="determine if given code should be documented")
    documentation : Optional[str] = Field(description="code documentation")
    chunk_name : str = Field(description="name of code chunk being documented")

class LLMOutput(BaseModel):
    documentations : List[DocumentationOutput] = Field(description="chunks documentation")

class TemplateDescriptionOutput(BaseModel):
    description : str = Field(description="Detailed Template description")
    tags : List[str] = Field(description="Tags that can be use to group template")

async def DocumentCode(code):
    model_provider, model = ("openai","gpt-4o")#getLLMConfig()    
    model = init_chat_model(model_provider=model_provider, model=model)
    model = model.with_structured_output(LLMOutput)

    res =  await model.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=code)
    ])

    return res.documentations


class DocumentationGenerator():

    def __init__(self):
        self.documentation_generated = {}
        model_provider, model, api_key  = getLLMConfig("documentation")    
        model = init_chat_model(model_provider=model_provider, model=model, api_key=api_key)

        self.regular_model_with_structured_output = model.with_structured_output(LLMOutput)
        self.template_description_model = model.with_structured_output(TemplateDescriptionOutput)

        self.rate_limmiter_manager = LLMRateLimiter()

    def gatherCodeContext(self,dependencies):
        context = {}
        for dep in dependencies:
            if dep in self.documentation_generated:
                context[dep] = self.documentation_generated[dep]

        return json.dumps(context)
    
    def get_doc(file_path:str,file_name:str,dependency:str):
        """
        Retrieve Dependency Code Documentation
        
        :param file_path (str) : absolute path to root project
        :param file_name (str) : source file name of dependency code 
        :param dependency (str) : dependecy name
        """
        file_data = getFeatureFile(file_path)

        if file_name.endswith(".py"):
            file_name = file_name[:-3]

        file_name = file_name.split(".")[-1]
        potential_files = [i for i in file_data if i.endswith(f"{file_name}.py")]

        for file_name in potential_files:
            if file_name in file_data and dependency in file_data[file_name]:
                return file_data[file_name][dependency]['doc']
        
        return None

    async def generateDocs(self,code,dependencies=[]):
        # TODO : check if dependencies is not in current batch. if its not add it's doc as extra context

        res = await self.rate_limmiter_manager.call(
            self.regular_model_with_structured_output,
            input = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=code)
            ]
        )

        # print("rate limitter response ",res)

        documentations = res.documentations

        return documentations
    
    def generateTemplateDescription(self,entry_info,configurations,framework="Django"):
        # retrieve yaml and configuration file
        # pass it to llm to generate description

        # llm responds with description
        # and 5 tags that describe template
        chunk_name, code, source = entry_info
        documentation = self.documentation_generated[f"{source}:::{chunk_name}"]
        query = f"""Documentation : {documentation}\n\nFramework : {framework}\n\nCode Implementation: {code}\n\nSettings/Configurations : {json.dumps(configurations)}"""
        
        print("our query \n\n", query,"\n\n")
        res = self.template_description_model.invoke([
            SystemMessage(content=template_description_system_prompt),
            HumanMessage(content=query)
        ])
        
        return res