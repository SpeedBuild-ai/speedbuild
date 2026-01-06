import os
from .sb_config import get_config

provider_to_api_key_name = {
    "openai":"OPENAI_API_KEY",
    "anthropic":"ANTHROPIC_API_KEY",
    "google":"GEMINI_API_KEY",
}

def getProviderAPIKey(role):
    config = get_config()

    try:
        return config['providers'][role]
    except:
        return None

def getLLMConfig(role):
    config = get_config()
    models = config.get('models',{})
    role_config = models.get(role,{})

    model_provider = role_config.get('provider',None) #os.environ.get("speedbuild_model_provider",None)
    model_name = role_config.get('model_name',None) #os.environ.get("speedbuild_model_name",None)
    provider_key = getProviderAPIKey(model_provider)

    llm_conf_set = True

    if model_provider == None or len(model_provider) == 0:
        llm_conf_set = False
    
    if model_name == None or len(model_name) == 0:
        llm_conf_set = False
    
    if provider_key == None:
        llm_conf_set = False

    if not llm_conf_set:
        raise ValueError(f"Run 'speedbuild config' to configure llm for {role}")
    
    return [model_provider,model_name,provider_key]


def setSpeedbuildConfig():
    config = get_config()
    # config_keys = config.keys()

    # providers = config.get("providers",{})
    # for i in providers:
    #     key = providers[i]
    #     if len(key.strip()) > 0:
    #         setProviderAPIKey(i,key)


    # if "default_model" in config_keys:
    #     model_name = os.environ.get("speedbuild_model_name",None)
    #     model_name_in_config = config['default_model']
        
    #     if model_name_in_config != model_name:
    #         os.environ['speedbuild_model_name'] = model_name_in_config

    # if "model_provider" in config_keys:
    #     model_provider = os.environ.get("speedbuild_model_provider",None)

    #     if config['model_provider'] != model_provider:
    #         os.environ["speedbuild_model_provider"] = config["model_provider"]

    # if "llm_keys" in config_keys and "model_provider" in config_keys:
    #     model_provider = config['model_provider']
    #     key_config = config["llm_keys"]

    #     provider_key = getProviderAPIKey(model_provider)
    #     key_name = provider_to_api_key_name[model_provider]

    #     if provider_key != key_config[model_provider]:
    #         os.environ[key_name] = key_config[model_provider]