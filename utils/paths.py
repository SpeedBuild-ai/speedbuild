import os
import json
from pathlib import Path

def get_user_root():
    home = str(Path.home())
    sb_root = os.path.join(home,".sb")

    if not os.path.exists(sb_root):
        os.makedirs(sb_root, exist_ok=True)

    return sb_root

def getProjectRootPath():
    root = os.path.abspath(".")
    sb_project_root = os.path.join(root,".sb")

    if not os.path.exists(sb_project_root):
        os.makedirs(sb_project_root,exist_ok=True)

    return sb_project_root


def getProjectConfig(test=False):

    if test:
        root = "/home/attah/Documents/jannis/api/jannis_api/.sb"
    else:
        root = getProjectRootPath()

    config_path = os.path.join(root,"config.json")

    if not os.path.exists(config_path):
        raise Exception("You need to initialized a speedbuild project first. run 'speedbuild init' ")
    
    try:
        with open(config_path,"r") as f:
            return json.loads(f.read())
    except json.JSONDecodeError:
        raise Exception("Invalid config file, please reinitialize project by runing 'speedbuild init' ")

