from textual.screen import Screen
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.widgets import Static, Button,Input,Select
from textual.containers import Vertical, VerticalGroup,HorizontalGroup


class SingleModel(VerticalGroup):

    # Track if data has changed
    has_changes = reactive(False)

    def __init__(self,title:str,model_id:str,model_name:str=None, model_provider:str=None,**kwargs):
        super().__init__(**kwargs)
        self.model_heading = title
        self.model_id = model_id
        self.model_name = model_name
        self.model_provider = model_provider

    def compose(self) -> ComposeResult:
        providers = self.app.config.get('providers',{})
        providers = [i for i in providers if len(providers[i])>0]

        yield Static(self.model_heading)
        yield Static("You must select a model name and its provider", id=self.model_id)
        yield Input(placeholder="Model Name e.g gpt-4o-mini", id="mode_name", value=self.model_name)
        yield Select([(p, p) for p in providers], prompt="Select Model Provider", id="model_provider", value=self.model_provider if self.model_provider else Select.BLANK)
        yield HorizontalGroup(
            Button("Update", id=f"update_model", classes="hidden"),
            classes="pad align_right"
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        """Called when Input value changes"""
        if event.input.id == "mode_name":
            self.check_for_changes()
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Called when Select value changes"""
        if event.select.id == "model_provider":
            self.check_for_changes()
    
    def check_for_changes(self) -> None:
        """Compare current values with originals"""
        input_widget = self.query_one("#mode_name", Input)
        select_widget = self.query_one("#model_provider", Select)
        
        current_model_name = input_widget.value
        current_provider = select_widget.value
        
        # Normalize Select.BLANK and None for comparison
        original_provider = self.model_provider if self.model_provider else Select.BLANK
        original_model_name = self.model_name if self.model_name else ""
        
        # Check if anything changed
        if (current_model_name != original_model_name or 
            current_provider != original_provider):
            self.has_changes = True
        else:
            self.has_changes = False
    
    def watch_has_changes(self, has_changes: bool) -> None:
        """Show/hide update button based on changes"""
        button = self.query_one("#update_model", Button)
        
        if has_changes:
            button.remove_class("hidden")
        else:
            button.add_class("hidden")
    
    
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "update_model":
            error_msg = self.query_one(f"#{self.model_id}")
            
            input_widget = self.query_one("#mode_name", Input)
            model_name = input_widget.value
            
            provider_selector = self.query_one("#model_provider", Select)
            provider = provider_selector.value

            if provider is not Select.BLANK and model_name:
                error_msg.styles.display = "none"
                role = self.model_id.split("_")[0]
                self.app.add_model(role,model_name,provider)
            else:
                error_msg.styles.display = "block"

class ModelScreen(Screen):
    def compose(self) -> ComposeResult:
        # TODO : get actual values for model
        models = self.app.config.get('models',{})

        classification = models["classification"]
        documentation = models["documentation"]
        rag = models["rag"]

        with Vertical(id="Main"):
            yield SingleModel("Classification Model","classification_error",classification['model_name'],classification['provider'])
            yield SingleModel("Documentation Model","documentation_error",documentation['model_name'],documentation['provider'])
            yield SingleModel("RAG Model","rag_error",rag['model_name'],rag['provider'])
            yield Button("Back", id="back")