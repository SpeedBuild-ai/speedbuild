import time
from rich.console import Console

class StatusManager:
    def __init__(self,show_percentage=False,max_value=0,step=0):
        self.console = Console()
        self.status = None
        self.show_percentage = show_percentage
        self.percentage = 0
        self.max_value = max_value
        self.step = step
        self.counter = 0

    def start_status(self,msg):
        self.status = self.console.status(f"[bold cyan]{msg}[/bold cyan]")
        self.status.start()
        return self.status

    def update_status(self, message):
        if self.show_percentage:
            self.status.update(f"[bold cyan] [ {self.percentage}% ] : {message}[/bold cyan]")
        else:
            self.status.update(f"[bold cyan]{message}[/bold cyan]")

    def update_progress(self):
        self.counter += self.step
        self.percentage = int(round((self.counter * 100) / self.max_value))

    def stop_status(self, msg=None):
        self.status.stop()
        if msg:
            self.console.print(f"[bold cyan]{msg}[/bold cyan]")

    def print_message(self,msg):
        self.console.print(f"[cyan]{msg}[/cyan]")


if __name__ == "__main__":
    manager = StatusManager(show_percentage=True,max_value=5,step=1)
    manager.start_status("Hello world")
    time.sleep(2)
    manager.update_status("We are at step 1")
    manager.update_progress()
    time.sleep(2)
    manager.update_status("We are at step 2")
    manager.update_progress()
    time.sleep(2)
    manager.update_status("We are nearing the end")
    manager.update_progress()
    time.sleep(2)
    manager.update_status("Wrapping up")
    manager.update_progress()
    time.sleep(2)
    manager.stop_status("Process Finished Successfully")