import json
import sys
from rich.panel import Panel
from rich.syntax import Syntax
from rich.layout import Layout
from rich.prompt import Prompt
from rich.console import Console

from .specs.client_conf import MCPLaunchSpec,claude_config, continue_config, cursor_config,kiro_config,vs_code_config

console = Console()

CLIENTS = {
    "Claude Desktop": claude_config,
    "Cursor": cursor_config,
    "Continue.dev": continue_config,
    "Kiro":kiro_config,
    "VS Code":vs_code_config,
    "Generic MCP": lambda s: s.__dict__,
}


def render_config(spec: MCPLaunchSpec, client: str):
    config = CLIENTS[client](spec)
    code = json.dumps(config, indent=2)

    syntax = Syntax(code, "json", theme="ansi_dark", line_numbers=False)

    layout = Layout()
    layout.split_column(
        Layout(
            Panel(
                f"[bold cyan]SpeedBuild MCP Configuration[/bold cyan]\n\n"
                f"[bold]Client:[/bold] {client}\n\n"
                "Copy & paste the configuration below:",
                border_style="cyan",
            ),
            size=6,
        ),
        Layout(
            Panel(
                syntax,
                border_style="green",
                title="MCP Config",
            ),
            size=20,
        ),
        Layout(
            Panel(
                "[bold][c][/bold] Copy  "
                "[bold][s][/bold] Switch Client  "
                "[bold][q][/bold] Quit",
                border_style="magenta",
            ),
            size=3,
        ),
    )

    console.clear()
    console.print(layout)

def capitalize_client_name(name):
    name = name.strip()
    names = name.split(" ")

    return " ".join([i.capitalize() for i in names])

def validate_mcp_entrypoint():
    try:
        import speedbuild.mcp.server  # noqa
        return True
    except Exception as e:
        raise RuntimeError(
            "SpeedBuild MCP server is not importable "
            f"from this environment: {e}"
        )

def mcp_conf_selector():
    spec = MCPLaunchSpec(
        name="speedbuild",
        command=sys.executable,
        args=["-m", "speedbuild.mcp.server"],
    )

    clients = [
        "Generic MCP",
        "Cursor",
        "VS Code",
        "Claude Desktop",
        "Kiro",
    ]


    client = Prompt.ask("Select MCP client", choices=clients)

    while True:
        render_config(spec, client)
        choice = Prompt.ask("Action", choices=["switch", "quit"])

        if choice == "quit":
            break

        if choice == "switch":
            client = Prompt.ask(
                "Select client",
                choices=list(CLIENTS.keys()),
                default=client,
            )
