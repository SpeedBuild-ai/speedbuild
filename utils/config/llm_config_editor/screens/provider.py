from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Static, Button,Input,ListView, ListItem, Select
from textual.containers import Vertical, VerticalGroup,HorizontalGroup

class ProviderScreen(Screen):
    def compose(self) -> ComposeResult:
        providers = self.app.config.get('providers',{})

        with Vertical(id="Main"):
            yield VerticalGroup(
                Static("Your Providers"),
                ListView(id="my_providers"),
                HorizontalGroup(
                    Static("", classes="spacer"), 
                    Button("Remove", id="remove_provider", classes="remove_hide"),
                ),
                classes="pad"
            )

            yield VerticalGroup(
                Static("Add Provider"),
                Static("You must select a provider and enter its api key", id="provider_error"),
                Select([(p, p) for p in providers], prompt="Select provider", id="provider_selector"),

                Input(placeholder="API key", password=True, id="api_key")
            )

            yield HorizontalGroup(
                Button("Back", id="back"),
                Static("", classes="spacer"), 
                Button("Save", id="save_provider"),
                classes="btn_container"
            )

    def on_mount(self) -> None:
        """Prepopulate the ListView when screen mounts"""
        list_view = self.query_one("#my_providers", ListView)

        providers = self.app.config.get('providers',{})

        items = [i for i in providers if len(providers[i])>0]
        self.displayed_items = items

        for item in items:
            list_view.append(ListItem(Static(item)))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        details = self.query_one("#remove_provider")
        
        # Show the widget
        details.styles.display = "block"

    def on_button_pressed(self,event: Button.Pressed):
        list_view = self.query_one("#my_providers", ListView)
        providers = self.app.config.get('providers',{})

        match event.button.id:
            case "save_provider":
                error_msg = self.query_one("#provider_error")

                input_widget = self.query_one("#api_key", Input)
                api_key = input_widget.value

                provider_selector = self.query_one("#provider_selector", Select)
                provider = provider_selector.value

                if provider and api_key:
                    providers[provider] = api_key
                    self.app.update_providers(providers)
                    input_widget.value = ""
                    provider_selector.clear()

                    # Add to ListView
                    list_view.append(ListItem(Static(provider)))

                    error_msg.styles.display = "none"
                else:
                    # Show the widget
                    error_msg.styles.display = "block"


            case "remove_provider":
                # Get the currently selected index
                index = list_view.index
                if index is not None and index < len(list_view):
                    list_view.pop(index)
                    providers_name = self.displayed_items[index]
                    providers[providers_name] = ""
                    self.app.update_providers(providers)