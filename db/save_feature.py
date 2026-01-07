import os
import json
from typing import Dict, List

from speedbuild.utils.paths import getProjectConfig

from .vector_db.vector_database import saveToVectorDB
from .relational_db.features import create_feature, feature_exist

def saveFeatureToDB(feature : Dict, framework:str, project_id : int, skip_vector_db=False) -> None:
    name = feature['name']
    code = feature['code']
    imports = feature.get('imports',[])
    dependencies = feature.get('deps',[])
    filename = feature['feature_filename']
    is_root = feature.get('is_root',False)
    documentation = feature.get('documentation',"")
    

    if not feature_exist(name,filename,code,project_id):
        dependencies = ",".join([i['imports'] for i in dependencies if isinstance(i,dict)])
        
        feature_id = create_feature(**{
            "doc": documentation,
            "name": name,
            "code":code,
            "code_import": imports,
            "dependencies": dependencies,
            "root_feature": is_root,
            "feature_filename": filename,
            "framework":framework,
            "project_id":project_id
        })

        imports = ",".join(imports)

        if not skip_vector_db:
            meta_data = {
                "doc": documentation if documentation else "",
                "name": name,
                "code_imports": imports,
                "dependencies": dependencies,
                "root_feature": is_root,
                "feature_filename": filename,
                "id": feature_id,
                "framework":framework,
                "project_id":project_id
            }

            saveToVectorDB(doc=f"{documentation}\n\n{code}",meta_data=meta_data)

def processFeatureDjangoSettings(settings_data : Dict, project_id : int ) -> str:
    name = f"{settings_data['feature']}_django_settings"
    settings = settings_data.get('settings',{})
    data = {
        "INSTALLED_APPS":settings.get('installed_apps',[]),
        "MIDDLEWARES":settings.get('middlewares',[[]])[0],
        "ImportStatements":settings.get('imports',[]),
        "Configurations":settings_data.get('configurations',[]),
        "PackageDependencies":settings_data.get("dependencies",[])
    }

    saveFeatureToDB({
        "name":name,
        "code":json.dumps(data),
        "feature_filename":"settings.py"
    },"django",project_id,True)

    return name

def saveFeatureFileToDB(file : str) -> None:
    if not os.path.exists(file):
        raise FileNotFoundError(f"Could not find file : {file}")
    
    project_sb_config = getProjectConfig() #getProjectConfig(True) # remove the True parameter in prod

    if "id" not in project_sb_config or "framework" not in project_sb_config:
        raise Exception("You need to initialized a speedbuild project first. run 'speedbuild init' ")
    
    project_id = project_sb_config['id']
    framework = project_sb_config['framework']

    with open(file,"r") as f:
        try:
            file_data = json.loads(f.read())
            settings_name = None

            if framework == "django":
                settings_conf = file_data['settings.py']
                del file_data['settings.py']

                settings_name = processFeatureDjangoSettings(settings_conf['feature_settings']['code'], project_id)

            for filename in file_data:
                for chunk in file_data[filename]:
                   feature_data = file_data[filename][chunk]

                   if settings_name is not None:
                       feature_data['deps'].append(settings_name) # add feature settings as part of dependencies

                   feature_data['feature_filename'] = filename
                   feature_data['name'] = chunk

                   saveFeatureToDB(feature_data,framework,project_id)

        except json.JSONDecodeError as error:
            raise ValueError(f"Feature file `{file}` is not valid json")
        
    # print("Feature Saved to DB")

def batch_save_features_to_db(feature_files : List[str]) -> None:
    for file_name in feature_files:
        saveFeatureFileToDB(file_name)


# if __name__ == "__main__":
#     saveFeatureFileToDB("/home/attah/.sb_zip/ManageSupplements.json")
#     # print(get_feature(2))