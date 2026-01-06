from rich.console import Console
from rich.text import Text
from rich.live import Live
from rich.panel import Panel
import readchar

class Selector:
    def __init__(self, options, title="Select an option"):
        self.options = options
        self.index = 0
        self.title = title
        self.console = Console(force_terminal=True)

    def render(self):
        text = Text()

        for i, option in enumerate(self.options):
            if i == self.index:
                text.append(f"▶ {option}\n", style="bold white on blue")
            else:
                text.append(f"  {option}\n")

        # Add instruction text
        text.append("\n", style="dim")
        text.append("Use ↑/↓ arrow keys to navigate, Enter to select, Ctrl-C to cancel", style="dim italic")

        return Panel(text, title=self.title, border_style="cyan")

    def run(self):
        try:
            with Live(
                self.render(),
                console=self.console,
                screen=True,
                refresh_per_second=30,
            ) as live:

                while True:
                    try:
                        key = readchar.readkey()

                        # Arrow Up
                        if key == readchar.key.UP:
                            self.index = (self.index - 1) % len(self.options)

                        # Arrow Down
                        elif key == readchar.key.DOWN:
                            self.index = (self.index + 1) % len(self.options)

                        # Enter
                        elif key in (readchar.key.ENTER, readchar.key.CR, readchar.key.LF, '\r', '\n'):
                            live.stop()
                            return self.options[self.index]

                        # Escape to quit
                        elif key == readchar.key.ESC:
                            live.stop()
                            return None

                        # Handle Ctrl-C from readchar
                        elif key == readchar.key.CTRL_C:
                            live.stop()
                            return None

                        live.update(self.render())
                    
                    except KeyboardInterrupt:
                        live.stop()
                        return None
        
        except KeyboardInterrupt:
            return None


def displaySelector(title,options):
    try:
        selector = Selector(
            options=options,
            title=title
        )

        choice = selector.run()
        if choice:
            return choice
        
    except KeyboardInterrupt:
        pass
    return None

if __name__ == "__main__":
    choice = displaySelector("Select Project Framework",["Django", "ExpressJS"])
    print(choice)