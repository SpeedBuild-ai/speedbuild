import os
import json
import asyncio
from pathlib import Path

from ....agent.tools.read_file import read_file
from ....agent.tools.break_chunk import breakChunk

from ..extraction.jsDep import getChunkDependencies
from ..extraction.handle_js_route import getRoutePathAndMethodsOrReturnNone
from ..extraction.extractCodeJs import getExtraDependencies, getFileNameFromDir

from ....utils.parsers.javascript_typescript.jsParser import JsTxParser
from ....utils.express.merge_js_entry import findImportStatement, get_express_instance_variable


# start from root route
# follow to all sub routes
# process sub routes of sub route

"""
    Find all project routes
"""

async def extractJSRoutes(file_name,root_path,routes=[]):
    _,chunks,variableToChunkMapping,import_deps = await JsTxParser().parse_code(file_name)

    with open(file_name,"r") as file:
        express_instance_name = get_express_instance_variable(file.read())

    for code in chunks:
        result = getRoutePathAndMethodsOrReturnNone(code,[])

        if result is not None:
            path,chunk_routes = result
            if "use" in chunk_routes:
                deps = getChunkDependencies(code,variableToChunkMapping,False)
                deps.remove(express_instance_name)

                route_path,_ = findImportStatement(list(deps)[0],import_deps)

                # get new dependency file path
                file_path = str(Path(root_path) / Path(route_path))
                file_name = os.path.basename(file_path)
                full_file_path = os.path.dirname(file_path)
                full_file_path = getFileNameFromDir(full_file_path,file_name)

                routes = await extractJSRoutes(full_file_path,root_path,routes)
            else:
                routes.append({
                    "path":path,
                    "source":file_name
                })

    return routes

def extractDjangoRoutes(file_name,project_root,routes=[]):

    chunks = read_file(file_name)

    # TODO : ignore router for now and focus on just urlPatterns
    for chunk in chunks:
        if chunk['code'].startswith("urlpatterns"):
            code = chunk['code']
            chunk_lines,_ = breakChunk(code,chunk['name'])
            chunk_lines = chunk_lines[1:-1] #ignore first and last entry i.e urlpatterns = [\n]
            
            for line in chunk_lines:
                print(line['code'],"\n","#"*30)
            break

    # print(chunks)
    return "Processing"

async def getAllExpressProjectRoutes(project_path):
    package_json_path = os.path.join(project_path,"package.json")
    if not os.path.exists(package_json_path):
        raise ValueError("Cannot find project package.json file")
    
    with open(package_json_path,"r") as file:
        conf = json.loads(file.read())
    
    if "main" not in conf.keys():
        entry_file = input("Could not find entry file. What is your project entry file (e.g index.js) : \n")
    else:
        entry_file = conf['main']

    entry_full_path = os.path.join(project_path,entry_file)

    if not os.path.exists(entry_full_path):
        raise ValueError("Could not find project entry file. file does not exist",entry_full_path)
    
    all_routes =  await extractJSRoutes(entry_full_path,project_path)


    # Extract all functions / views attached to routes

    parser = JsTxParser()

    files_dict = {}
    for entry in all_routes:
        source = entry['source']
        path = entry['path']
        file_entry = []

        if source in files_dict.keys():
            file_entry = files_dict[source]
    
        file_entry.append(path)
        files_dict[source] = file_entry


    features = {}

    for file in files_dict:
        _,chunks,chunk_names,import_deps = await parser.parse_code(file)

        for chunk in chunks:
            words = chunk.split(".")
            if len(words) > 1:
                route_info = getRoutePathAndMethodsOrReturnNone(chunk,chunks)
                if route_info is not None:
                    file_tag = f"{file}:::{route_info[0]}"
                    if route_info[0] in files_dict[file]:
                        extra_dependencies, dep_to_path_mappings = getExtraDependencies(import_deps)
                        deps = getChunkDependencies(chunk,chunk_names,False,extra_dependencies)

                        for i in deps:
                            file_path = dep_to_path_mappings[i] if i in dep_to_path_mappings else file

                            if file != file_path:
                                file_name = os.path.basename(file_path)
                                project_root = Path(os.path.dirname(file))
                                relative_path = Path(file_path)

                                file_path = str((project_root / relative_path).resolve())

                                file_path = getFileNameFromDir(os.path.dirname(file_path),file_name)

                                # print("file_path",file_path,"\n\n")

                            data = {
                                "source":file_path,
                                "path" : i,
                            }

                            path_deps = []
                            if file_tag in features:
                                path_deps = features[file_tag]

                            if data not in path_deps: 
                                path_deps.append(data)

                            features[file_tag] = path_deps

    merged_features = []
    route_mapping = {}

    for i in features:
        entry = features[i]
        route_mapping[i] = entry
        merged_features.extend(entry)

    return merged_features,route_mapping


if __name__ == "__main__":
    project_root = "/home/attah/Documents/work/speedbuildjs/express.js_contact_app"
    features,routes_mapping = asyncio.run(getAllExpressProjectRoutes(project_root))
    print(routes_mapping)

"""
If every dependency of a path is reusable extract that path else extract only reusable deps
"""