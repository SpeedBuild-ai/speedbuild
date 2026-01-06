import os
import json

def getFeatureFile(file_path):
    
    if os.path.exists(file_path):
        with open(file_path,"r") as file:
            file_data = json.loads(file.read())
    else:
        file_data = {}
        os.makedirs(os.path.dirname(file_path),exist_ok=True)

    return file_data

def get_doc(file_path:str,file_name:str,dependency:str):
    """
    Retrieve Code Documentation
    
    :param file_path (str) : absolute path to root project
    :param file_name (str) : source file name of dependency code 
    :param dependency (str) : dependecy name
    """
    file_data = getFeatureFile(file_path)

    if file_name.endswith(".py"):
        file_name = file_name[:-3]

    file_name = file_name.split(".")[-1]
    potential_files = [i for i in file_data if i.endswith(f"{file_name}.py")]

    for file_name in potential_files:
        if file_name in file_data and dependency in file_data[file_name]:
            return file_data[file_name][dependency]['doc']
    
    return None

def writeCodeToFeatureFile(file_path,code_info):
    file_data = getFeatureFile(file_path)

    code_name = code_info['name']
    file_name = code_info['file_name']
    dependencies = code_info.get('dependencies',[])
    imports = code_info.get('imports',[])
    code = code_info.get('code')

    if file_name not in file_data:
        file_data[file_name] = {}

    if code_name not in file_data[file_name]:
        file_data[file_name][code_name] = {
            "code":code,
            "imports":imports,
            "deps":dependencies,
            "doc":code_info.get('doc',None)
        }

    elif code_name == "name_less":
        for i in dependencies:
            if i not in file_data[file_name][code_name]['deps']:
                file_data[file_name][code_name]['deps'].append(i)

        for i in imports:
            if i not in file_data[file_name][code_name]['imports']:
                file_data[file_name][code_name]['imports'].append(i)

        file_data[file_name][code_name]['code'] += f"\n{code}"


    if '/' not in file_name:
        file_data[file_name][code_name]["is_root"] = True

    with open(file_path,"w") as file:
        json.dump(file_data,file,indent=4)

        
# if __name__ == "__main__":
    # print(get_doc("/home/attah/Documents/jannis/api/jannis_api/output/sb_output_markConsultationAsPaid/feature.json","userprofile.views","markConsultationAsPaid"))