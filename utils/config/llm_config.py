import os
import json
from pathlib import Path

from speedbuild.utils.paths import get_user_root

user_home = get_user_root()
config_path = os.path.join(user_home,"config.json")

supported_models = {
    "openai":["gpt-4o"],
    "anthropic":[],
}

def get_sb_config():
    if not os.path.exists(config_path):
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path,"w") as file:
            file.write("{}")

        return {}

    with open(config_path,"r") as file:
        data = json.loads(file.read())
        return data

def save_config(config):
    if not os.path.exists(config_path):
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
    with open(config_path, "w") as file:
        json.dump(config, file, indent=4)

def get_config():
    config = get_sb_config()
    return config

def setAPIKey(provider,api_key):
    if provider not in supported_models.keys():
        raise ValueError(f"Please choose from our LLM supported providers {list(supported_models.keys())}")
    
    config = get_sb_config()

    keys_dictionary = {}
    if "llm_keys" in config.keys():
        keys_dictionary = config['llm_keys']

    if len(api_key) == 0 and provider in keys_dictionary.keys():
        del keys_dictionary[provider]
    else:
        keys_dictionary[provider] = api_key

    
    config['llm_keys'] = keys_dictionary

    save_config(config)

def updateDefaultLLMModel(provider,model_name):
    config = get_sb_config()

    if provider not in supported_models.keys():
        raise ValueError("Please choose from our supported providers ",list(supported_models.keys()))
    
    if model_name not in supported_models[provider]:
        raise ValueError(f"Supported Models for provider : {provider} are {supported_models[provider]}")
    
    config['default_model'] = model_name
    config['model_provider'] = provider
    save_config(config)