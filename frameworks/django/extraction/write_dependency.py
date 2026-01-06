import os
import re

from ....utils.django.manage_url import merge_urls
from ....utils.parsers.python.parser import PythonBlockParser
from ....utils.django.var_utils import get_assigned_variables
from ....utils.template.write_feature_file import writeCodeToFeatureFile

from .feature_dependencies import arrangeChunks, getBlockDependencies, getCodeBlockFromFile, removeDuplicates

parser = PythonBlockParser()

def getWritePath(file_path, output_dir):
    path = file_path.split("/")
    write_dir = os.path.join("output",output_dir)

    if len(path) == 1 :
        dest = os.path.join(write_dir,path[0])
        # dest = path[0]    
    else:
        
        file_name = os.path.basename(file_path) #path.pop()
        file_folder = os.path.basename(os.path.dirname(file_path))#path.pop()

        dest = os.path.join(write_dir,file_folder)
        # dest = file_folder

        if not os.path.exists(dest):
            os.makedirs(dest, exist_ok=True)

        dest = os.path.join(dest,file_name)
    return dest


def writeCodeToFile(file_path,code,imports,deps,writeAfter=False, output_dir=None):

    """
    write feature code to template file
    """

    if code == None:
        return
    
    feature_relative_path = os.path.join("output",output_dir,)
    
    feature_file_path = os.path.join(
        os.path.abspath("."),
        feature_relative_path,
        "feature.json"
    )

    dest = getWritePath(file_path,output_dir)


    name = get_assigned_variables(code,True)
    documentation = None

    if isinstance(name,set):
        name = "name_less"
    else:
        # generate doc here
        documentation = None

    code_info = {
        "code":code,
        "name":name,
        "file_name":dest.replace(feature_relative_path,"").lstrip(),
        "imports":imports,
        "dependencies":deps,
        "doc":documentation
    }
    writeCodeToFeatureFile(feature_file_path,code_info)

    # if os.path.exists(dest):

    #     file_code = []
    #     file_imports = []

    #     # append to file
    #     with open(dest, "r") as file:
    #         data = file.read()  # Step 1: Read existing content

    #         old_content = parser.parse_code(data)
    #         for chunk in old_content:
    #             if chunk.startswith("import ") or chunk.startswith("from "):
    #                 file_imports.append(chunk)
    #             else:
    #                 file_code.append(chunk)


    #     imports.extend(file_imports)
    #     file_code.append(code)

    #     code =  file_code

    #     if len(imports) > 0:  # Step 3: Write new content
    #         imports = removeDuplicates(imports)

    #     if len(code) > 0:
    #         # TODO: we might need to rearrange chunks
    #         code = "\n\n".join([chunk for chunk in code if chunk is not None])


    # with open(dest,"w") as file:
    #     if(len(imports)>0):
    #         file.write("\n".join(imports))
    #         file.write("\n\n")
    #     if code is not None:
    #         file.write(code)

    # # # TODO : sort code, problem with sorting in views.py
    # if "urls.py" not in dest and "views.py" not in dest:
    #     sortFile(dest)


def extract_settings_references(code):
    pattern = r'settings\.\w+'
    confs = [i.replace("settings.","").strip() for i in re.findall(pattern, code)]

    return confs

def checkIfFeatureAlreadyInFile(file_path,feature):
    if os.path.exists(file_path) == False:
        return False
    
    with open(file_path) as file:
        chunks = parser.parse_code(file.read())
        names = []
        for chunk in chunks:
            chunk_name = get_assigned_variables(chunk,True)
            if len(chunk_name) > 0:
                names.append(chunk_name)

        # print("checking ",file_path," ",names, " feture ", feature)
        return feature in names
    
def get_temp_file_path(file_path, project_root,project_name,app_name):
    # print("working with ", file_path)
    # file_path_list = file_path.split("/")
    file = os.path.basename(file_path)#file_path_list.pop().strip()

    main_path = os.path.dirname(file_path)#"/".join(file_path_list)
    
    parent_dir = os.path.basename(main_path)#file_path_list.pop()

    main_path = os.path.basename(main_path) #main_path.split("/")[-1].strip()

    # print(app_name, " here ", parent_dir)
    # print(main_path, "  pth ",project_name)

    app_name = app_name.strip()
    parent_dir = parent_dir.strip()

    if project_name.strip() == main_path.strip():
        # TODO : convert this to write to root
        templtae_file_path = file
        

    elif app_name != parent_dir:
        # check if .sb_utils folder exist
        # if not create folder
        templtae_file_path = os.path.join(".sb_utils",file)

    else:
        templtae_file_path = os.path.join("sb_app",file)

    return templtae_file_path

def OneStep(
        file_path,
        feature,
        project_root,
        folders_in_project_root,
        writeToFile=True,
        app_name="/",
        use_email=False,
        settings_conf=[],
        project_name=None,
        output_dir = None,
        processed = []
        ):
    
    feature_tag = f"{file_path}::{feature}"
    
    # Prevent infinite recursion - add to processed FIRST
    if feature_tag in processed:
        return [set(), use_email, settings_conf]
    
    processed.append(feature_tag)
    
    # print("here testing ",feature_tag)
    
    packages = set()
    use_email = use_email

    if os.path.exists(file_path):
        with open(file_path,"r") as file:
            data = file.read()
            file_dependencies = PythonBlockParser().parse_code(data)

            for chunk in file_dependencies:
                if chunk.startswith("import ") or chunk.startswith("from "):
                    if "django.core.mail" in chunk:
                        use_email = True

            # get feature
            feature_code = getCodeBlockFromFile(feature,file_dependencies)

            if feature_code == None:
                # print("we deyhere with ",feature,len(feature),"\n\n",file,"\n\n")
                raise ModuleNotFoundError("Could not find feature declaration in file. please ensure you've properly spelt feature name")

            # get feature dependencies
            feature_dependencies = getBlockDependencies(feature_code,file_dependencies)

            # get feature imports
            deb_imports = []
            
            for entry in feature_dependencies:
                # print("getting dependencies ",entry)
                package_path = entry['packagePath'].strip()
                imports = entry['imports'].strip()

                if package_path == imports:
                    deb_imports.append(f"import {imports}")
                elif package_path != ".":
                    package_path_words = package_path.split(".")
                    file_name = package_path_words[-1]

                    if package_path_words[0] in folders_in_project_root:
                        new_package_path = f".sb_utils.{file_name}"
                        deb_imports.append(f"from {new_package_path} import {imports}")
                    else:
                        deb_imports.append(f"from {package_path} import {imports}")
            
            for index,importLine in enumerate(deb_imports):
                line = importLine.split("import")[0]
                line = line.replace("from","").strip()

                if len(line) > 0 and line.startswith(".") == False:
                    folder_name = line.split(".")[0]
                    if folder_name in folders_in_project_root:
                        importLine = importLine.replace(line,line[len(folder_name):])
                        deb_imports[index] = importLine
            
            # Process ALL dependencies (children) first
            if len(feature_dependencies) > 0:
                for feature_dep in feature_dependencies:
                    path,dep = [feature_dep['packagePath'], feature_dep['imports']]
                    
                    if path != ".":
                        if path.startswith("."):
                            new_path = os.path.dirname(file_path)
                            new_path = os.path.join(new_path,f"{path[1:]}.py")
                            path = new_path
                        else:
                            package = path.split(".")[0]

                            if package != "django":
                                if package not in folders_in_project_root:
                                    packages.add(package)
                            else:
                                full_import = path + f".{dep}"

                                if full_import.startswith("django.conf.settings"):
                                    new_settings_conf = extract_settings_references(feature_code)
                                    settings_conf.extend(new_settings_conf)
                                
                            path = path.split(".")
                            path = os.path.join(project_root, "/".join(path)+".py")

                        # Recursively process child dependencies

                        if " as " in dep: # remove alias name from dependency before processing
                            dep = dep.split(" as ")[0].strip()

                        feature_packages,use_email,settings_conf = OneStep(
                            path, dep, project_root, folders_in_project_root,
                            True, app_name, use_email, settings_conf, 
                            project_name, output_dir, processed
                        )
                        packages = packages.union(feature_packages)
                    else:
                        # Recursively process child dependencies
                        feature_packages, use_email, settings_conf = OneStep(
                            file_path, dep, project_root, folders_in_project_root,
                            True, app_name, use_email, settings_conf,
                            project_name, output_dir, processed
                        )
                        packages = packages.union(feature_packages)
            
            # After ALL children are written, write parent
            if writeToFile:
                template_file_path = get_temp_file_path(file_path,project_root,project_name,app_name)
                writeCodeToFile(template_file_path,feature_code, deb_imports,feature_dependencies,output_dir=output_dir)
    
    return [packages, use_email, settings_conf]

def getOldFile(filePath):
    with open(filePath) as file:
        return file.read()

def getFileImportsAndCode(chunks):
    imports = []
    code = []
    
    for chunk in chunks:
        if chunk.startswith("import ") or chunk.startswith("from "):
            # individualImports = getIndividualImports(chunk)
            imports.append(chunk)
        else:
            code.append(chunk.strip())

    return [imports,code]

def writeToFile(filePath,content,fileName):

    dest = filePath

    if fileName not in filePath:
        dest = os.path.join(filePath,fileName)

    if os.path.exists(dest):  

        currentFileContent = getOldFile(dest)

        if "urls.py" == fileName:
            file_content = merge_urls(currentFileContent.split("\n"),content.split("\n"))

        else:
            # TODO : handle conflicts here
            file_content = ""

            currentFileChunks = parser.parse_code(currentFileContent)
            codeUpdateChunk = parser.parse_code(content) #new update from sb deploy
            
            imports, currentFileCode = getFileImportsAndCode(currentFileChunks)
            newImports, newCode = getFileImportsAndCode(codeUpdateChunk)
            
            # get chunks name from currentFileCode
            currentFileChunksNames = []
            for chunk in currentFileCode:
                name = get_assigned_variables(chunk,True)
                if isinstance(name,str):
                    currentFileChunksNames.append(name)
                else:
                    # add a default value just to retain chunk order
                    currentFileChunksNames.append(0)

            # process new code and decide on insert position
            # default insert position is 0
            for chunk in newCode:
                name = get_assigned_variables(chunk,True)
                if isinstance(name,str):
                    if name in currentFileChunksNames:
                        """ Conflict Identified """
                        conflictChunkPosition = currentFileChunksNames.index(name) #assuming name appears only once
                        oldCode = currentFileCode[conflictChunkPosition]

                        if oldCode != chunk:
                            # pop code
                            currentFileCode.pop(conflictChunkPosition)

                            # add conflict markers
                            conflictCode = f"<<<<<<< SpeedBuild update \n{oldCode}\n=======\n{chunk}\n>>>>>>>"
                            currentFileCode.insert(conflictChunkPosition, conflictCode)

                        continue

                currentFileCode.insert(0,chunk) # fresh non merge conflict code

            imports.extend(newImports) # merge current and new imports

            if imports:  # Step 3: Write new content
                imports = removeDuplicates(imports)
                imports = "\n".join(imports)
                file_content += f"{imports} \n\n\n"

            code = removeDuplicates(currentFileCode)
            code = "\n\n".join(code)

            file_content += code  # Append old content to new content

        with open(dest,"w") as file:
            file.write(file_content)

    else:
        with open(dest,"w") as file:
            file.write(content)


def sortFile(file_name):
    with open(file_name,"r") as file:
        data = file.read()
        codeChunks = []
        imports = []

        chunks = PythonBlockParser().parse_code(data)

        for chunk in chunks:
            if chunk.startswith("import ") or chunk.startswith("from "):
                imports.append(chunk)
            else:
                codeChunks.append(chunk)

        arranged_chunks = []
        processed = []
    
    file_imports = "\n".join(imports)
    processedChunks = arrangeChunks(codeChunks,arranged_chunks,processed)
    file_code = "\n\n".join(processedChunks)

    with open(file_name,"w") as sortedFile:
        newData = f"{file_imports}\n\n{file_code}"
        sortedFile.write(newData)