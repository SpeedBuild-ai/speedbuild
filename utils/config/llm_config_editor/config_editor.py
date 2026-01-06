import os
import json
from typing import Dict

from textual.widgets import Button,Static
from textual.app import App, ComposeResult
from textual.containers import Vertical, HorizontalGroup

from .screens.model import ModelScreen
from .screens.provider import ProviderScreen

from speedbuild.utils.paths import get_user_root

class ConfigEditor(App):
    # CSS_PATH = "./design.tcss"
    CSS = """
        #Main {
        align: center middle;
        width: 100%;
        height: 100%;
        overflow-y: auto;  /* Enable vertical scrolling */
        margin:1;
    }

    HorizontalGroup{
        width: 100%;
        height: auto;
    }

    .HorizontalCenter {
        align: center middle;
    }

    Button{
        height:3;
    }

    Static {
        padding: 1;
    }

    .fit_content{
        width:auto;
    }

    .spacer {
        width: 1fr;  /* Takes up all available space */
    }


    Input{
        margin: 1;
    }

    Select{
        height:5;
        margin:1;
        padding:0;
    }

    .center_text{
        text_align:center;
    }

    VerticalGroup{
        background:#303030;
        width:50%;
        margin:1 0;
    }

    .btn_container{
        width:50%;
    }

    .pad{
        padding:1;
    }

    ListView {
        height: 10;
        background:#303030;
    }

    ListView > ListItem.--highlight {
        background: blue 50%;
    }

    #remove_provider{
        display:none;
    }

    #provider_error, #classification_error, #documentation_error, #rag_error{
        color:red;
        display:none;
    }

    .align_right{
        align: right middle;
    }

    .hidden {
        display: none;
    }
    """

    def __init__(self):
        super().__init__()
        config_path = get_user_root()
        self.config_file_path = os.path.join(config_path,"config.json")
        self.config = self.get_config()

    def get_config(self):
        if not os.path.exists(self.config_file_path):
            return {
                "providers": {
                    "openai":"",
                    "anthropic":"",
                    "google":""
                },
                "models": {
                    "classification": {
                        "model_name":"",
                        "provider":""
                    },
                    "documentation": {
                        "model_name":"",
                        "provider":""
                    },
                    "rag": {
                        "model_name":"",
                        "provider":""
                    },
                },
            }
        
        with open(self.config_file_path,"r") as f:
            return json.loads(f.read())

    def save_config(self,data):
        with open(self.config_file_path,"w") as f:
            json.dump(data,f,indent = 4)

    def update_providers(self,providers:Dict):
        self.config['providers'] = providers
        self.save_config(self.config)

    def add_model(self,role:str,name:str,provider:str):
        self.config['models'][role] = {
            "model_name":name,
            "provider":provider
        }
        self.save_config(self.config)
    
    def compose(self) -> ComposeResult:
        with Vertical(id="Main"):
            yield Static("SpeedBuild LLM Configurations", id="my_label", classes="center_text")
            yield HorizontalGroup(
                Button("LLM Providers", id="provider"),
                Button("Models", id="models"),
                Button("Exit", id="exit"),
                classes="HorizontalCenter"
            )

    def on_button_pressed(self,event:Button.Pressed):
        match event.button.id:
            case "exit":
                self.app.exit()
            case "provider":
                self.push_screen(ProviderScreen())
            case "back":
                self.app.pop_screen()
            case "models":
                self.push_screen(ModelScreen())
            