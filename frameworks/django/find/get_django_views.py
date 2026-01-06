# Goal Merge all the pieces together to perform a complete system.
import hashlib
import os
import asyncio

from .django_info import get_django_feature_views

from ....agent.classifier.main import FeatureClassifier

from ....utils.file import findFilePath
from ....utils.parsers.python.parser import PythonBlockParser
from ....utils.django.var_utils import get_assigned_variables
from ....utils.parsers.javascript_typescript.jsParser import JsTxParser

feature_cache = {}
reusable_feature_semaphore = asyncio.Semaphore(5)

async def getFeatureCode(file_name,feature_name,framework="django"):
    global feature_cache

    if file_name not in feature_cache:

        if not os.path.exists(file_name):
            raise FileExistsError(f"File : {file_name} does not exist")
        
        if framework == "django":
            file_code = {}
            with open(file_name,"r") as file:
                chunks = PythonBlockParser().parse_code(file.read())

                for chunk in chunks:
                    chunk_name = get_assigned_variables(chunk,True)
                    if isinstance(chunk_name,str):
                        file_code[chunk_name] = chunk

        elif framework == "express":
            parser = JsTxParser()
            _,_,file_code,_ = await parser.parse_code(file_name)

        # save file features to cache
        feature_cache[file_name] = file_code

    else:
        # get file code from cache
        file_code = feature_cache.get(file_name)

    if feature_name not in file_code:
        raise AssertionError(f"could not find {feature_name} in {file_name}")
    
    return file_code.get(feature_name)

def hash_code(code: str) -> str:
    h = hashlib.sha256()
    h.update((code + "V1").encode("utf-8"))
    return h.hexdigest()

# HERE
async def isFeatureReusable(feature,framework,feature_cache={}):
    if framework == "django":
        code = await getFeatureCode(feature['view_file'], feature['view_name'])
    else:
        code = await getFeatureCode(feature['source'], feature['path'],"express")

    code_hash = hash_code(code)

    if code_hash in feature_cache:
        return (feature_cache[code_hash] != "NOT_REUSABLE",feature,None)

    async with reusable_feature_semaphore:
        info = await FeatureClassifier(framework).classifyFeature(code)

    return (info.classification != "NOT_REUSABLE",feature,code_hash)

def GetAllDjangoExposedFeatures(project_path):
    settings_path = GetDjangoSettingsPath(project_path)
    django_views = get_django_feature_views(project_path,settings_path)

    return django_views

def GetDjangoSettingsPath(project_path):
    project_asgi_path = findFilePath(project_path, "asgi.py")

    if len(project_asgi_path) == 0:
        raise ValueError("Could not find project asgi.py file")
    elif len(project_asgi_path) > 1:
        raise ValueError("found multiple asgi.py file")
    
    main_project_folder = os.path.dirname(project_asgi_path[0])
    settings_path = os.path.join(project_path,main_project_folder)

    settings_path = findFilePath(settings_path,"settings.py")
    
    if len(settings_path) == 0:
        raise ValueError("Could not find project settings.py file")
    elif len(settings_path) > 1:
        raise ValueError("found multiple settings.py file")

    return f"{main_project_folder}.settings"



# if __name__ == "__main__":
#     project_path = "/home/attah/Documents/jannis/api/jannis_api"
#     asyncio.run(GetReusableFeatures(project_path))