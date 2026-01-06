import os
import json
from pathlib import Path

from ....utils.parsers.javascript_typescript.jsParser import JsTxParser 
from ....utils.parsers.javascript_typescript.handleModuleExport import getModuleExport 
from ....utils.parsers.javascript_typescript.js_var_names import get_variable_name_and_type
from ....utils.template.write_feature_file import writeCodeToFeatureFile 

from .jsDep import getChunkDependencies
from .handle_js_route import getRoutePathAndMethodsOrReturnNone
from .reverseImport import convertToImportStatements, getDepFromImportDict, mergeImportDict

parser = JsTxParser()

async def processEntryFile(file_name,file_dependencies,project_root,packages,output_path):

    _,chunks,chunks_name,import_dict = await parser.parse_code(file_name)

    for chunk in chunks:
        deps = None
        skip_chunk = False
        words = chunk.split(".")
        if len(words) > 1:
            route_info = getRoutePathAndMethodsOrReturnNone(chunk,chunks)

            if route_info is not None:
                deps = getChunkDependencies(chunk,chunks_name,False)
                _, dep_to_path_mappings = getExtraDependencies(import_dict)

                for dep in deps:
                    if dep in dep_to_path_mappings.keys():
                        full_path = os.path.normpath(f"{project_root}/{dep_to_path_mappings[dep]}")
                        # print("Full path is ", full_path,full_path.replace(project_root,"").lstrip("/"))

                        if full_path.replace(project_root,"").lstrip("/") not in file_dependencies:
                            skip_chunk = True
                            break

        # is_ignore = len([i for i in deps if dep_to_path_mappings[i] in file_dependencies]) > 0
        if not skip_chunk:
            # print("Processing \n",chunk, "\n","#"*10)

            # feature,entry_file,is_feature_name=True,packages=set(),processed=set(),ignore_paths=None)
            packages, _  = await extractFeatureCode(chunk,file_name,project_root,output_path,False,packages,set(),file_dependencies) # extract code

    return packages

def getExtraDependencies(import_deps):
    extra_dependencies = []
    dep_to_path_mappings = {}

    for item in import_deps:
        element = import_deps[item]

        for depItem in element:
            if depItem["alias"] != None:
                deps = [depItem['alias']]
            elif "ext_deps" in depItem.keys() and len(depItem["ext_deps"]) > 0:
                deps = depItem['ext_deps']
            else:
                deps = [depItem['dep']]
            
            extra_dependencies.extend(deps)

            # create dep to path mapping
            for singleDep in deps:
                dep_to_path_mappings[singleDep] = item

    return [extra_dependencies,dep_to_path_mappings]


def getFileNameFromDir(dir,filename):
    if len(dir.strip()) == 0:
        return None
    
    current_files = os.listdir(dir)
    filename = filename.split(".")[0]

    for file in current_files:
        if file.split(".")[0].strip() == filename:
            # print(f"{dir}/{file}", " Found file")
            return os.path.join(dir,file)#f"{dir}/{file}"
    
    return None


async def extractFeatureCode(feature,entry_file,project_root,output_path,is_feature_name=True,packages=set(),processed=set(),ignore_paths=None):
    # add file to processed
    processed.add(os.path.normpath(entry_file))

    entry_file_fullpath = entry_file

    file_root = os.path.dirname(entry_file) #entry_file.split("/")[:-1]
    # file_root = "/".join(file_root)

    _,_,chunks_names,import_deps = await parser.parse_code(entry_file)
    extra_dependencies, dep_to_path_mappings = getExtraDependencies(import_deps)

    chunk_deps = getChunkDependencies(feature,chunks_names,is_feature_name,extra_dependencies)

    # print(chunk_deps,"\n")
    chunk = chunks_names[feature] if is_feature_name else feature

    chunk_imports = {}

    # process deps
    for dep in chunk_deps:

        if dep in dep_to_path_mappings.keys():
            dep_path = dep_to_path_mappings[dep]
            dep_list = chunk_imports[dep_path] if dep_path in chunk_imports.keys() else []

            # print(f"Get dependency {dep} from {dep_path}")

            if ignore_paths is not None and dep_path in ignore_paths:
                continue
            
            dep_list.append(dep)



            # get new dependency file path
            file_path = str(Path(file_root) / Path(dep_path))
            # full_file_path = file_path.split("/")
            file_name = os.path.basename(file_path) #full_file_path.pop(-1)

            full_file_path = os.path.dirname(file_path)#"/".join(full_file_path)

            full_file_path = getFileNameFromDir(full_file_path,file_name)

            dep_info = None

            if dep_path in import_deps.keys():
                import_info = import_deps[dep_path] 
                dep_info = getDepFromImportDict(import_info,[dep])

            if dep_info is not None:
                root_import = dep_info[0]['standalone'] == True if 'standalone' in dep_info[0].keys() else False
            else:
                root_import = False

            
            # check if dep is a custom file or an external package
            if full_file_path is not None and not root_import:
                packages, processed = await extractFeatureCode(dep,full_file_path,project_root,output_path,True,packages,processed)
            elif full_file_path is not None and root_import:
                # print("Manageing root import for ", dep)
                _,deps_chunks,dep_chunks_names,deps_import_deps = await parser.parse_code(full_file_path)

                if dep in dep_chunks_names.keys():
                    packages, processed = await extractFeatureCode(dep,full_file_path,project_root,output_path,True,packages,processed) # process normally
                else:
                    # try to find module.export
                    for dep_chunk in deps_chunks:
                        if dep_chunk.strip().startswith("module.export"):
                            packages, processed = await extractFeatureCode(dep_chunk,full_file_path,project_root,output_path,False,packages,processed) 
                            break
                
            else:
                # print(f"External Package {dep} Found")
                packages.add(dep_path)

            # print("dependencies list are ", dep_list)
            
            # if deb_object is not None:
            chunk_imports[dep_path] = dep_list

        else:
            # print(f"Get dependency {dep} from current file")
            if dep != feature:
                await extractFeatureCode(dep,entry_file,project_root,output_path)

    # print(f"Finished processing {entry_file}\n\n")

    for path in chunk_imports:
        chunk_imports[path] = getDepFromImportDict(import_deps[path],chunk_imports[path])

    entry_file = os.path.basename(os.path.normpath(entry_file)).lstrip("/")#os.path.normpath(entry_file).replace(project_root,"")

    # if entry_file.startswith("/"):
    #     entry_file = entry_file[1:]

    entry_file_folders = os.path.relpath(os.path.abspath(entry_file_fullpath), project_root).lstrip("/")

    output_file = output_path

    if len(entry_file_folders) > 0:
        output_file = os.path.join(output_path,os.path.dirname(entry_file_folders))

    # print("#"*20," ",output_file)
    # TODO : here
    full_path = os.path.join(output_file, entry_file)

    deps_in_file = set()

    # print("full filepath is ",full_path, " folders are ",entry_file_folders)

    if os.path.exists(full_path):
        # add to file
        _,chunks,chunks_names,import_deps = await parser.parse_code(full_path)

        if chunk not in chunks:
            chunks.append(chunk)
            
        mergeImport = mergeImportDict(import_deps,chunk_imports)

        file_imports = convertToImportStatements(mergeImport)
        file_code = chunks

    else:
        # make dir
        if len(os.path.dirname(full_path).strip()) > 0:
            os.makedirs(os.path.dirname(full_path),exist_ok=True)
            # print("creating folder ", os.path.dirname(full_path))
        file_imports = convertToImportStatements(chunk_imports)
        file_code = [chunk]

    og_imports = file_imports


    # clean chunks here
    cleaned_chunks = []
    removed_exports = []

    for i in file_code:
        if i.strip().startswith("module.exports") == False:
            cleaned_chunks.append(i)

            # get chunk name here
            chunk_var_name = get_variable_name_and_type(i)
            if chunk_var_name is not None:
                deps_in_file.add(chunk_var_name[1])
        else:
            removed_exports.append(i)

    with open(full_path,"w") as file:
        code = ""
        file_imports = "\n".join(file_imports)

        if len(file_imports) > 0:
            code += f"{file_imports}\n\n"

        # get file export

        exports = await getModuleExport(entry_file_fullpath,deps_in_file)

        # TODO : this is not standard and it will fail
        # find a better solution.
        """
        so incase we removed an original export from file,
        and after running getModuleExport we were not able to detect any export,
        we just add the original export back.

        this is relevant for database schema where the schema name is defined when exported
        
        e.g : module.exports = mongoose.model("Contact",contactSchema)
        remeber this function is removing every module.exports
        """

        if exports:
            for export in exports:
                if export not in cleaned_chunks:
                    cleaned_chunks.append(export)

        elif removed_exports:
            for entry in removed_exports:
                cleaned_chunks.append(entry)

        file_code = "\n\n".join(cleaned_chunks) # TODO : remove duplicates from chunks

        code += file_code
        file.write(code)
    
        feature_file_path = os.path.join(
            output_path,
            "feature.json"
        )

        code_info = {
            "code":chunk,
            "name":feature if is_feature_name else "name_less",
            "file_name":os.path.basename(full_path),#full_path.replace(project_root,"").lstrip("/output/"),
            "imports":og_imports,
            "dependencies":list(chunk_deps),
            "doc":""
        }

        writeCodeToFeatureFile(feature_file_path,code_info)

    return packages, processed


def createPackageJsonFile(packages,entry_file,dependencies,dev_dependencies,project_root):
    template_dependencies = {}
    template_dev_dependencies = {}
    data = {}

    for package in packages:
        if package in dependencies.keys():
            template_dependencies[package] = dependencies[package]
        elif package in dependencies.keys():
            template_dev_dependencies[package] = dev_dependencies[package]

    # print("dependencies ", template_dependencies)
    # print("dev dependencies ", template_dev_dependencies)

    # name, main, scripts, description, devDependencies, 
    # data['name'] = "feature_name"
    data['main'] = entry_file
    data['scripts'] = {"dev":f"node {entry_file}"}

    if len(template_dependencies) > 0:
        data['dependencies'] = template_dependencies

    if len(template_dev_dependencies) > 0:
        data['devDependencies'] = template_dev_dependencies

    with open(os.path.join(project_root,"package.json"),"w") as file:
        json.dump(data, file, indent=4)


async def handleExtraction(root_path, feature, file_path,output_path):
    packages,files_processed = await extractFeatureCode(feature,file_path,root_path,output_path,False)

    package_json = os.path.join(root_path,"package.json") #f"{root_path}/package.json"

    if not os.path.exists(package_json):#(f"{root_path}/package.json"):
        raise ValueError("Cannot find package.json in root project folder ",root_path)
    
    with open(package_json,"r") as file:
        data = json.loads(file.read())

        dependencies = data['dependencies'] if "dependencies" in data.keys() else None
        dev_dependencies = data['dev_dependencies'] if "dev_dependencies" in data.keys() else None
        main = os.path.join(root_path,data['main']) if 'main' in data.keys() else None #f"{root_path}/{data['main']}" if 'main' in data.keys() else None

        while main == None:
            main_file_path = input("Please Enter the full Path to your project entry file : ")
            if os.path.exists(main_file_path):
                main = main_file_path
            else:
                print("The file whose path you specified does not exists")

        # print("Dependencies are ", dependencies)
        # print("Dev Dependencies are ", dev_dependencies)

        # print("packages ", packages)
        # print("files ", files_processed)

        if main not in files_processed:
            # process main file
            packages = await processEntryFile(main,files_processed,root_path,packages,output_path)

        
        # print("Final Packages are ", packages, " type is ", type(packages))

        main_path = main.replace(root_path,"").strip().lstrip("/")
        # if main_path.startswith("/"):
        #     main_path = main_path[1:]
        
    createPackageJsonFile(packages,main_path,dependencies,dev_dependencies,output_path)
    return main_path #entry file
        