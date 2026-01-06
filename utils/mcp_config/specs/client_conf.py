from dataclasses import dataclass
from typing import List, Dict

"""
    MCP client
    ----------
    1) cursor           -- known  -- done
    2) antigravity      -- known  -- skip
    3) vs code          -- known  -- done
    4) jetbrains
    5) claude desktop   -- known
    6) codex            -- skip for now
    7) kiro             -- known
    8) continue
"""

@dataclass
class MCPLaunchSpec:
    name: str
    command: str
    args: List[str]
    env: Dict[str, str] | None = None

def claude_config(spec: MCPLaunchSpec) -> dict:
    return {
        "mcpServers": {
            spec.name: {
                "command": spec.command,
                "args": spec.args,
                **({"env": spec.env} if spec.env else {})
            }
        }
    }

def cursor_config(spec: MCPLaunchSpec) -> dict:
    return {
        "mcpServers": {
            spec.name: {
                "command": spec.command,
                "args": spec.args,
                "description":"A set of tools for reusing code and code patterns to fit team patterns and structure",
                **({"env": spec.env} if spec.env else {})
            }
        }
    }

def continue_config(spec: MCPLaunchSpec) -> dict:
    return {
        "mcpServers": [
            {
                "name": spec.name,
                "command": spec.command,
                "args": spec.args,
                **({"env": spec.env} if spec.env else {})
            }
        ]
    }

def vs_code_config(spec: MCPLaunchSpec) -> dict:
    return {
        "mcpServers": {
            spec.name: {
                "command": spec.command,
                "args": spec.args,
                **({"env": spec.env} if spec.env else {})
            }
        }
    }

def kiro_config(spec: MCPLaunchSpec) -> dict:
    return {
        "mcpServers": {
            spec.name:{
                "command": spec.command,
                "args": spec.args,
                "disabled":False,
                **({"env": spec.env} if spec.env else {})
            }
        }
    }