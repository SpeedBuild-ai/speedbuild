import os
from .jsDep import getChunkDependencies
from .extractjs import getRoutePathAndMethodsOrReturnNone
from utils.parsers.javascript_typescript.jsParser import JsTxParser
from .extractCodeJs import extractFeatureCode, getExtraDependencies


parser = JsTxParser()

# TODO : extract external file dependencies

async def processEntryFile(file_name,file_dependencies,project_root):

    _,chunks,chunks_name,import_dict = await parser.parse_code(file_name)
    packages = []

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
                        # print("Full path is ", full_path)

                        # TODO : test this out
                        path_without_dot_or_slash = full_path.replace(project_root,"").lstrip("/")
                        # print("Full path cleaned is ", path_without_dot_or_slash)
                        
                        if path_without_dot_or_slash not in file_dependencies:
                            skip_chunk = True
                            break

        # is_ignore = len([i for i in deps if dep_to_path_mappings[i] in file_dependencies]) > 0
        if not skip_chunk:
            print("Processing \n",chunk, "\n","#"*10)
            packages = await extractFeatureCode(chunk,file_name,False,packages,file_dependencies) # extract code

    # print("Packages are ", packages)