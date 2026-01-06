import os

from pydantic import Field
from typing import Optional, TypedDict

from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver 
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import START, StateGraph, MessagesState
from langchain_core.messages import HumanMessage, SystemMessage

from speedbuild.utils.config.agent_config import getLLMConfig
from speedbuild.db.vector_db.vector_database import getCodeContext

from ..prompts.chat_system_prompt import system_prompt, format_system_prompt

class CodeChatOutputFormat(TypedDict):
    response: str = Field(
        description="Natural language response shown to the user"
    )

    feature_id: Optional[int] = Field(
        default=None,
        description="ID of selected reusable code features relevant to the request"
    )

    instruction: Optional[str] = Field(
        default=None,
        description="Clear, actionable customization instructions for adapting the feature(s)"
    )

    action: str = Field(
        description="One of: explain | apply_feature | ask_clarifying_question"
    )


class CodeChat():
    def __init__(self):
        model_name,provider, api_key = getLLMConfig("rag")
        model = init_chat_model(model=model_name,model_provider=provider, api_key=api_key)
        self.model = model.bind_tools([getCodeContext])
        self.format_llm = model.with_structured_output(CodeChatOutputFormat)
        self.build_graph()

        self.first_message = True


    def chat(self,state):
        res = self.model.invoke(state['messages'])
        print(res,"\n")
        return {"messages":res}
    
    def build_graph(self):
        builder = StateGraph(MessagesState)
        builder.add_node("chat",self.chat)
        builder.add_node("tools",ToolNode([getCodeContext]))

        builder.add_edge(START,"chat")
        builder.add_conditional_edges("chat",tools_condition)
        builder.add_edge("tools","chat")

        self.graph = builder.compile(checkpointer=InMemorySaver())

    def formatLLMResponse(self,response):
        return self.format_llm.invoke([
            SystemMessage(content=format_system_prompt),
            HumanMessage(content=response)
        ])

    def run(self,message,history="history_tag"):
        messages = [HumanMessage(content=message)]

        if self.first_message:
            self.first_message = False
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=message)
            ]
        
        response = self.graph.invoke({"messages":messages},{"configurable": {"thread_id":history}})
        response = response['messages'][-1].content

        return self.formatLLMResponse(response)
    

if __name__ == "__main__":
    chat = CodeChat()
    while True:
        query = input("Enter Message : \n")
        if query == "q":
            break

        response = chat.run(query)

        print(f"Speedbuild : {response}\n","-"*30)

