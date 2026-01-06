import os

from ....utils.parsers.javascript_typescript.jsParser import JsTxParser

from .extractCodeJs import getFileNameFromDir
from .reverseImport import convertToImportStatements


def list_all_files(folder_path):
    file_paths = []
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename == "feature.json":
                continue
            
            full_path = os.path.join(root, filename)
            file_paths.append(full_path)
    return file_paths

def getNewImportPath(file_path, dep_path):
    file_path = os.path.abspath(os.path.normpath(file_path))
    dep_path = os.path.abspath(os.path.normpath(dep_path))

    return os.path.relpath(dep_path,file_path)

async def updateFileImportInFile(filename,dependency,root_path):
    new_dict = {}
    parser = JsTxParser()
    file_path = "/".join(filename.split("/")[:-1])

    dependency = dependency.split("/")
    dependency_file = dependency[-1].lstrip()
    dependency_path = "/".join(dependency[:-1])

    _,chunks,_,import_deps = await parser.parse_code(filename,False,True)

    for key in import_deps.keys():
        full_file_path = getFileNameFromDir(dependency_path,dependency_file)
        
        if full_file_path is not None:
            dep = os.path.basename(full_file_path)
            key_base_name = os.path.basename(key)

            if key_base_name.endswith(dep) or key_base_name.endswith(dep.split(".")[0]):
                value = import_deps[key]
                new_key = getNewImportPath(file_path,dependency_path)
                new_key = f"{new_key}/{dependency_file}"
                new_dict[new_key] = value
            else:
                new_dict[key] = import_deps[key]
    
    # Update file here
    if new_dict.keys() != import_deps.keys():
        code = "\n".join(convertToImportStatements(new_dict))
        code += f"\n\n{"\n".join(chunks)}"

        with open(filename,"w") as file:
            file.write(code)

async def moveFile(file_path, folder):

    # check if file exists
    if not os.path.exists(file_path):
        return None
    
    # Move the file to the new location
    os.makedirs(folder, exist_ok=True)
    new_file_path = os.path.join(folder, os.path.basename(file_path))
    os.rename(file_path, new_file_path)

    # update file refrence in other files
    files = list_all_files("./output")
    for file in files:
        if file != file_path:
            await updateFileImportInFile(file,new_file_path,"./output")
