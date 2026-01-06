"""
Docstring for speedbuild_api.mcp_server.main

* Search feature       -- implemented; moving to testing
* Get feature          -- Implemented; moving to testing
* Validate feature

Question
--------
- How do we validate features via the MCP server
"""
from typing import Dict
from mcp.server.fastmcp import FastMCP

from ..db.relational_db.features import get_feature
from ..agent.code_chat.codebase_chat import CodeChat


mcp = FastMCP("speedbuild")

@mcp.tool()
def getFeature(id:int) -> Dict | None:
    return get_feature(id)

@mcp.tool()
def findFeature(query:str,framework:str) -> Dict:
    chat = CodeChat()
    response = chat.run(f"framework : {framework}\n\nquery : {query}")
    return response

if __name__ == "__main__":
    mcp.run(transport="stdio")