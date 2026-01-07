<div align="center">

# SpeedBuild

**Stop AI agents from reinventing your architecture every time you prompt them**

SpeedBuild enforces your patterns. Your AI agents generate code that follows your team's conventions, architecture, and proven implementations — automatically.

[![PyPI version](https://badge.fury.io/py/speedbuild.svg)](https://badge.fury.io/py/speedbuild)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Discord](https://img.shields.io/discord/YOUR_DISCORD_ID?color=7289da&label=Discord&logo=discord&logoColor=white)](https://discord.gg/speedbuild)

[Quick Start](#quick-start) • [Documentation](#documentation) • [Discord](https://discord.gg/speedbuild) • [Examples](#examples)

</div>

---

## Demo

> **[▶️ Watch SpeedBuild enforce patterns in real-time](https://youtu.be/your-demo-video)** *(45 seconds)*

**Without SpeedBuild:**
```
You: Add user authentication
Agent: [generates 200 lines of new auth code]
You: Add password reset  
Agent: [generates completely different auth pattern]
You: Add OAuth
Agent: [third auth implementation, zero consistency]
```

**With SpeedBuild:**
```
You: Add user authentication
Agent: [queries SpeedBuild, follows YOUR existing auth pattern]
You: Add password reset
Agent: [extends the SAME pattern, consistent with your architecture]  
You: Add OAuth
Agent: [integrates with YOUR pattern, deterministic output]
```

<!-- Add a demo GIF here when ready:
![SpeedBuild Demo](docs/demo.gif)
-->

---

## The Real Problem

### AI agents have no architectural memory

Every time you prompt an AI agent, it starts from zero:

- ❌ **Generates new implementations** instead of following your patterns
- ❌ **Ignores your architecture** and reinvents the wheel
- ❌ **Produces different output** for the same prompt across sessions
- ❌ **Doesn't learn** from your codebase or team conventions

**Result:** Inconsistent code. Endless refactoring. Architecture drift. Your codebase becomes a graveyard of different patterns for the same problems.

### SpeedBuild solves AI output variability

SpeedBuild is an **enforcement layer** that:

✅ **Extracts your patterns** from existing code  
✅ **Enforces those patterns** when agents generate new code  
✅ **Provides deterministic output** — same pattern, every time  
✅ **Grounds agents** in your architecture, not random internet examples

**Think: Architectural memory + pattern enforcement for AI agents.**

When you or your agent need to build something, SpeedBuild ensures it follows the patterns you've already established — automatically.

---

## Quick Start

### Installation

```bash
pip install speedbuild
```

### Initialize in your project

```bash
cd your-project
speedbuild init
```

### Configure LLM
configure your llm provider and which model to use for what (classification, documentation,rag)

```bash
speedbuild config
```

### Extract your patterns

SpeedBuild automatically discovers reusable patterns in your codebase:

```bash
speedbuild find
```

Or manually tag a specific pattern:

```bash
speedbuild extract
```

### Connect to your editor

Generate MCP config for VS Code, Cursor, or Claude Desktop:

```bash
speedbuild mcp-config
```

Copy the output into your editor's MCP settings file.

**Done.** Your agents now follow YOUR patterns.

---

## How It Works

### 1. SpeedBuild learns your patterns

```bash
$ speedbuild find

Scanning codebase...
Found 12 reusable patterns:
  ✓ Django REST API authentication (JWT + refresh tokens)
  ✓ Express middleware structure  
  ✓ Error handling patterns
  ✓ Database migration conventions
  ✓ API response formatting
  ...
```

SpeedBuild extracts:
- Code structure and organization
- Naming conventions
- Architecture decisions
- Proven implementations

### 2. Agents query SpeedBuild before generating

When you prompt your AI agent:

```
You: Add a new API endpoint for user profiles, use speedbuild to retrive patterns
```

The agent automatically:
1. **Queries SpeedBuild** for your API endpoint patterns
2. **Retrieves your conventions** (auth, validation, response format)
3. **Generates code** that follows YOUR established patterns
4. **Produces deterministic output** consistent with your architecture

### 3. Your architecture stays consistent

**Same pattern, every time:**
- Authentication? Uses your JWT implementation
- Error handling? Follows your error format
- Database queries? Uses your ORM patterns
- API structure? Matches your conventions

**No more:**
- "Why did the agent use a different auth pattern?"
- "This doesn't match our architecture"
- "I need to refactor this to be consistent"

---

## Real-World Impact

<table>
<tr>
<td width="50%">

### ❌ Without SpeedBuild

**Same prompt, different sessions:**

```python
# Session 1
@app.route('/users', methods=['POST'])
def create_user():
    # Generated auth check #1
    token = request.headers.get('Authorization')
    # New validation pattern
    # Different error handling
```

```python
# Session 2  
@app.route('/posts', methods=['POST'])
def create_post():
    # Generated auth check #2 (different!)
    # Different validation
    # Different error format
```

**Result:** Inconsistent codebase

</td>
<td width="50%">

### ✅ With SpeedBuild

**Same prompt, any session:**

```python
# Session 1
@app.route('/users', methods=['POST'])
@require_auth  # YOUR pattern
@validate_input(UserSchema)  # YOUR pattern
def create_user():
    # Follows YOUR error handling
    # Uses YOUR response format
```

```python
# Session 2
@app.route('/posts', methods=['POST'])  
@require_auth  # SAME pattern
@validate_input(PostSchema)  # SAME pattern
def create_post():
    # SAME error handling
    # SAME response format
```

**Result:** Consistent, predictable architecture

</td>
</tr>
</table>

---

## Features

### 🎯 Pattern Enforcement
- Extracts patterns from your existing code
- Enforces those patterns in new code generation
- Ensures consistency across your entire codebase
- Works for both humans and AI agents

### 🔒 Deterministic Output
- Same prompt → Same pattern → Same structure
- Eliminates AI output variability
- Predictable, reliable code generation
- No more "agent roulette"

### 🏗️ Architectural Memory
- Learns your team's conventions
- Remembers your architecture decisions
- Enforces coding standards automatically
- Scales from solo dev to enterprise teams

### 🤖 AI-Native
- Model Context Protocol (MCP) integration
- Works with Claude, Cursor, Continue, Cline
- Grounds agents in YOUR codebase
- Agents follow YOUR rules, not internet examples

### 🏠 Local-First
- Everything stored on your machine
- SQLite + ChromaDB embeddings
- Fully offline capable
- No code leaves your machine (by default)

### 🛠️ Framework Support
- ✅ Django
- ✅ Express.js
- 🚧 React (coming soon)
- 🚧 FastAPI (coming soon)

[Vote for the next framework →](https://github.com/yourusername/speedbuild/discussions)

---

## Usage Examples

### Example 1: Enforcing authentication patterns

```bash
# You've built JWT auth once in your Django API
$ speedbuild find

Found pattern: JWT Authentication
  Location: api/auth/
  Structure: token generation, refresh rotation, blacklisting
  Used: 15 times across 3 projects
```

**Now when you prompt your agent:**

```
You: Add authentication to the new posts endpoint, use speedbuild

Agent: [Queries SpeedBuild]
Agent: I'll use your existing JWT authentication pattern.
       [Generates code following YOUR exact auth pattern]
       - Same decorator structure
       - Same token validation
       - Same error responses
       - Same conventions
```

### Example 2: Consistent API endpoints

**Your pattern:** RESTful endpoints with consistent structure

```python
# SpeedBuild learns this pattern from your code:
@app.route('/api/<version>/<resource>', methods=['GET', 'POST'])
@require_auth
@validate_input(schema)
@handle_errors
def endpoint():
    # Your standardized response format
    return jsonify({
        'success': True,
        'data': result,
        'meta': pagination
    })
```

**Every new endpoint follows the same pattern:**

```
You: Create an endpoint for comments
Agent: [Generates following YOUR pattern]
       ✓ Same route structure
       ✓ Same decorators
       ✓ Same validation
       ✓ Same response format
```

### Example 3: Team-wide consistency

```bash
# Extract patterns once
$ speedbuild find

# Share patterns with team (coming Q2)
$ speedbuild push team

# Everyone's agents follow the SAME patterns
# No more "but the agent generated it differently for me"
```

---

## Why This Matters Now

### AI agents are powerful but unpredictable

- **Copilot:** Generates code from scratch every time
- **ChatGPT:** No memory of your architecture
- **Cursor/Claude:** Reinvents patterns with each prompt

They're fast, but they produce **inconsistent, non-deterministic output**.

### SpeedBuild makes agents deterministic

By enforcing your patterns, SpeedBuild transforms AI agents from:

**"Random code generators"** → **"Pattern-following architecture extensions"**

This is the missing piece for production AI-assisted development.

---

## Comparison

| Feature | SpeedBuild | GitHub Copilot | Cursor/Continue | Linters/Formatters |
|---------|-----------|----------------|-----------------|-------------------|
| Enforces YOUR patterns | ✅ | ❌ | ❌ | ⚠️ Style only |
| Deterministic AI output | ✅ | ❌ | ❌ | N/A |
| Architectural memory | ✅ | ❌ | ⚠️ Limited | ❌ |
| Pattern extraction | ✅ Auto | ❌ | ❌ | ❌ |
| Works offline | ✅ | ❌ | ❌ | ✅ |
| Grounds AI agents | ✅ | ❌ | ⚠️ Partial | ❌ |

**SpeedBuild sits between your code and AI agents** — ensuring agents follow your architecture instead of hallucinating new patterns.

---

## Roadmap

### ✅ Shipping Now
- Pattern extraction from existing codebases
- Semantic search and retrieval
- MCP server for editor integration  
- Local storage (SQLite + ChromaDB)
- Django & Express.js support

### 🚧 Coming Q1 2025
- Pattern validation layer
- More frameworks (React, FastAPI, Rails)
- Enhanced pattern enforcement rules
- Better DX and CLI improvements

### 💡 Coming Q2 2025
- **Team collaboration** — Share patterns across your org
- **Pattern versioning** — Track how patterns evolve
- **Cross-repo enforcement** — Consistent patterns across all projects
- **Private hosting** — For enterprises that need it

> 💡 **Local version stays free forever.** Team features (collaboration, versioning, hosting) fund development.

---

## Documentation

- **[Installation Guide](docs/installation.md)** — Get SpeedBuild running
- **[Pattern Extraction](docs/extraction.md)** — How SpeedBuild learns your patterns
- **[Pattern Enforcement](docs/enforcement.md)** — How SpeedBuild enforces consistency
- **[MCP Integration](docs/mcp-integration.md)** — Connect to editors and agents
- **[Framework Support](docs/frameworks.md)** — Supported frameworks and roadmap
- **[Architecture](docs/architecture.md)** — How SpeedBuild works under the hood
- **[Contributing](CONTRIBUTING.md)** — Build the future of deterministic AI

---

## FAQ

<details>
<summary><b>How does SpeedBuild enforce patterns?</b></summary>

When your AI agent is about to generate code, it queries SpeedBuild first. SpeedBuild:
1. Finds relevant patterns from your codebase
2. Provides them as context to the agent
3. The agent generates code following those patterns
4. Output is consistent with your architecture

It's like giving the agent a "style guide" of your actual code, automatically.

</details>

<details>
<summary><b>Does this replace linters/formatters?</b></summary>

No, it complements them. Linters enforce syntax and style (spaces, quotes, etc.). SpeedBuild enforces:
- Architecture patterns
- Code organization
- Implementation approaches
- Team conventions

Think: ESLint for syntax, SpeedBuild for architecture.

</details>

<details>
<summary><b>Will agents generate the exact same code every time?</b></summary>

The **pattern** will be the same. The implementation details may vary slightly, but:
- Structure: Same
- Architecture: Same
- Conventions: Same
- Approach: Same

It's deterministic at the pattern level, not the character level.

</details>

<details>
<summary><b>What if I don't have established patterns yet?</b></summary>

SpeedBuild still helps! It will:
1. Extract whatever patterns exist in your code
2. Help you be consistent with yourself going forward
3. As you establish patterns, SpeedBuild learns them

Start messy, stay consistent.

</details>

<details>
<summary><b>Does this work for human developers too?</b></summary>

Yes! Humans can query SpeedBuild the same way:

```
speedbuild find authentication pattern
speedbuild show me our error handling conventions
```

It's architectural memory for your entire team — human and AI.

</details>

<details>
<summary><b>What about pattern conflicts?</b></summary>

If SpeedBuild finds multiple patterns for the same thing:
1. It shows you all of them
2. You choose which pattern to follow
3. You can mark a pattern as "preferred"
4. Future generations use the preferred pattern

SpeedBuild helps you consolidate and standardize over time.

</details>

<details>
<summary><b>How is this different from RAG?</b></summary>

RAG retrieves relevant information. SpeedBuild:
- **Extracts structured patterns** (not just text)
- **Enforces those patterns** during generation
- **Validates consistency** with your architecture
- **Tracks pattern usage** across your codebase

It's RAG + enforcement + architectural understanding.

</details>

</details>

<details>
<summary><b>Is there a paid version?</b></summary>

Local use is **free forever**. Paid features (coming Q2 2025):
- Team collaboration and pattern sharing
- Pattern versioning and history
- Private hosting for enterprises
- Cross-repo pattern enforcement

Solo developers and small teams get full functionality for free, always.

</details>

---

## The Vision

### Today: Local pattern enforcement
You extract patterns from your code. Your agents follow them.

### Q2 2025: Team pattern enforcement  
Your team shares patterns. Everyone's agents follow the same rules.

### Future: Universal architectural memory
Patterns evolve across your organization. New projects start with established patterns. Architecture stays consistent at scale.

**This is infrastructure for the agentic era.**

AI agents are powerful, but they need grounding. SpeedBuild provides that grounding through pattern enforcement and architectural memory.

---

## Community

Join developers building deterministic AI:

- **[Discord](https://discord.gg/speedbuild)** — Get help, share patterns, discuss roadmap
- **[GitHub Discussions](https://github.com/yourusername/speedbuild/discussions)** — Feature requests and pattern ideas
- **[Twitter](https://twitter.com/speedbuild)** — Updates and examples
- **[Blog](https://speedbuild.dev/blog)** — Deep dives on pattern enforcement

---

## Contributing

We're building this **with** developers who are tired of inconsistent AI output.

Ways to contribute:
- 🐛 [Report bugs](https://github.com/yourusername/speedbuild/issues/new?template=bug_report.md)
- 💡 [Request features](https://github.com/yourusername/speedbuild/issues/new?template=feature_request.md)
- 🔧 [Submit PRs](https://github.com/yourusername/speedbuild/pulls) — Check [CONTRIBUTING.md](CONTRIBUTING.md)
- 📖 Improve documentation
- 🎨 Add framework support
- 🧪 Share your patterns and use cases

**Good first issues:** [`good first issue`](https://github.com/yourusername/speedbuild/labels/good%20first%20issue)

---

## Acknowledgments

Built on:
- [ChromaDB](https://github.com/chroma-core/chroma) — Vector database for pattern embeddings
- [Model Context Protocol](https://modelcontextprotocol.io/) — Agent integration standard
- [SQLite](https://www.sqlite.org/) — Local pattern storage

Inspired by every developer who's ever said:
*"Why did the agent generate this differently than last time?"*

---

## License

MIT — See [LICENSE](LICENSE) for details.

**Free forever for local use.** Team features fund development.

---

<div align="center">

## Stop reinventing. Start enforcing.

**SpeedBuild: Pattern enforcement for AI agents**

**[Install Now](#quick-start)** • **[Join Discord](https://discord.gg/speedbuild)** • **[Star on GitHub ⭐](https://github.com/yourusername/speedbuild)**

Made with ⚡ by developers tired of inconsistent AI output.

</div>