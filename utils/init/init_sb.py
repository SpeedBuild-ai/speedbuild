import os
import json

from speedbuild.db.relational_db.main import init_db
from speedbuild.utils.cli.cli_select import displaySelector
from speedbuild.db.relational_db.project import create_project, delete_project

frameworks = ["django","express"]

def initSpeedbuildProject(root_path):
    config_path = os.path.join(root_path,".sb","config.json")
    dirName = os.path.dirname(config_path)
    init_db()

    reinitialized = False

    project_name = os.path.basename(os.path.abspath("."))

    if os.path.exists(config_path):
        try:
            with open(config_path,"r") as f:
                data = json.loads(f.read())
                delete_project(**{"project_id":data['id']})
                reinitialized = True
        except:
            pass

    if not os.path.exists(dirName):
        os.makedirs(dirName)

    framework = displaySelector("Select Project Framework",["Django", "Express"])

    if framework == None:
        return
    
    project_id = create_project(**{"name":project_name})

    with open(config_path,"w") as file:
        json.dump({
            "framework" : framework.lower(),
            "id":project_id
        },file,indent=4)

    if reinitialized:
        print("Project has been reinitialized")
    else:
        print("Speedbuild project successfully initialized")


def getSBProjectConfig(root_path):
    config_path = os.path.join(root_path,".sb","config.json")
    if not os.path.exists(config_path):
        return {}
    
    with open(config_path,"r") as file:
        return json.loads(file.read())
    
def updateSBConfig(root_path,config):
    config_path = os.path.join(root_path,".sb","config.json")
    
    if not os.path.exists(config_path):
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

    with open(config_path,"w") as file:
        json.dump(config,file,indent=4)

def getOrSetRepoId(project_path):
    project_config = getSBProjectConfig(project_path)

    if "repo_id" in project_config:
        repo_id = project_config['repo_id']
    else:
        repo_id = None

    if repo_id == None:
        repo_id = input("What SB repo id do you want to push to (leave blank if you dont want to push) :\n")
        try:
            repo_id = int(repo_id)
        except:
            repo_id = None
        project_config['repo_id'] = repo_id
        updateSBConfig(project_path,project_config)

    return repo_id


if __name__ == "__main__":
    initSpeedbuildProject(".")