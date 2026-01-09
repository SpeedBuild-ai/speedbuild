# SpeedBuild
[![PyPI version](https://badge.fury.io/py/speedbuild.svg)](https://badge.fury.io/py/speedbuild)
![License: Apache](https://img.shields.io/badge/license-Apache%20License%202.0-yellow)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)


SpeedBuild is a local tool that extracts reusable code features from your existing codebase and makes them available through an MCP server. This helps AI coding tools (like Cursor, Claude, or Copilot) reference past implementations when generating new code, leading to more consistent results.

It runs entirely on your machine, uses your own LLM API keys, and stores data locally in Chroma (for vectors) and SQLite.

Currently focused on Django and Express projects, with support for their common patterns.

## How it works

1. Initialize in your project:
   ```
   speedbuild init
   ```

2. Extract and store reusable features from your code:
   ```
   speedbuild find
   ```

3. Get the MCP configuration:

   Note : you need FastMCP installed to use speedbuild MCP
   ```
   pip install fastmcp
   ```
   After installing FastMCP run
   ```
   speedbuild mcp-config
   ```
   Copy the output and paste it into your IDE or AI tool (e.g., Cursor or VS Code settings for MCP servers).

That's it. Now, when you ask your AI tool to implement something (e.g., "add user registration like we do it"), it can pull references from your extracted features, including dependencies.

You provide your own LLM API keys. You can configure different models/providers for tasks like:
- Classification (finding features)
- Documentation (generating docs)
- Retrieval (natural language code search)

Everything runs locally—no data leaves your system.

## Installation

```
pip install speedbuild
```
or check the releases on GitHub.
``` 
speedbuild config
```

to setup llm configuration and specify which models to use. 

NOTE !! you need to install the relevant lanchain provider package for your model provider of choice.

```
# for openai
pip install langchain-openai

# for google
pip install langchain-google-vertexai langchain-google-genai

# for anthropic
langchain-anthropic 
```

## Future plans

Phase 2 will add:
- Versioning of extracted features
- Collaboration (sharing across team members)
- Monitoring

These will be paid features.
