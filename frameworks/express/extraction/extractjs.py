import os
import shutil
from pathlib import Path

# from speedbuild.utils.cli.output import StatusManager 
from ....agent.documentation.get_feature_code import generateFeatureDocs

from ....utils.cleanup.clear_folder import clear_folder 
from ....utils.parsers.javascript_typescript.jsParser import JsTxParser 
from ....utils.template.template_update import checkTemplateForVersionUpdate 

from .extractCodeJs import handleExtraction
from .handle_js_route import getRoutePathAndMethodsOrReturnNone

async def startExpressExtraction(path,file_name,project_root):
    """
    Extracts and processes Express.js route handlers from JavaScript files.
    This function parses JavaScript code, extracts route handlers matching a specified path,
    processes dependencies, and organizes extracted files into appropriate folders.
    Args:
        path (str): The route path to extract (e.g., "/api/users")
        file_name (str): Path to the JavaScript source file
        project_root (str): Root directory of the project
    Returns:
        None
    Raises:
        ValueError: If the specified route path is not found in the source file
    The function performs the following steps:
    1. Parses JavaScript code to extract chunks and dependencies
    2. Processes and maps dependencies
    3. Locates and extracts the route handler matching the specified path
    4. Indexes and categorizes extracted files
    5. Moves files to appropriate folders based on categorization
    6. Creates a zip archive of the extracted template
    """
    parser = JsTxParser()
    # logger = StatusManager()

    # logger.print_message("Extracting Feature Code")
    # logger.start_status("Starting Extraction")

    extracted = False
    extra_dependencies = []
    dep_to_path_mappings = {}

    template_name = f"{os.path.basename(project_root)}::{file_name}::{path}".replace("/","_")

    _,chunks,chunk_names,import_deps = await parser.parse_code(file_name)

    output_path = os.path.join("output",template_name)

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

    if path in chunk_names.keys():
        await handleExtraction(project_root,chunk_names[path],file_name,output_path)
        extracted = True
    else:
        for chunk in chunks:
            words = chunk.split(".")
            if len(words) > 1:
                route_info = getRoutePathAndMethodsOrReturnNone(chunk,chunks)
                if route_info is not None:
                    if route_info[0] == path:
                        await handleExtraction(project_root,chunk,file_name,output_path)
                        extracted = True
                        break
    
    # TODO get template name here
    # print("Template output path is ",template_name)
    
    if not extracted:
        # Not found
        raise ValueError("Route specified was not found in ",file_name)

    extraction_root = os.path.join("output",template_name)

    # package into zip
    home = str(Path.home())
    template_path = os.path.join(home,".sb_zip")#f"{home}/.sb_zip"
    output_dir = os.path.join(project_root,extraction_root)#os.path.join(project_root,"output") #f"{project_root}/output"

    if not os.path.exists(template_path):
        os.makedirs(template_path,exist_ok=True)

    
    # logger.stop_status()

    template_path = os.path.join(template_path,template_name)#f"{template_path}/{template_name}"
    
    # shutil.make_archive(template_path, 'zip', output_dir) # We dont need this now

    feature_file_path = f"{template_path}.json"

    # move template feature file to output folder
    shutil.move(os.path.join(os.path.abspath("."),output_path,"feature.json"),feature_file_path)

    is_multi_extract = os.environ.get("multi_extract",'False') == "True"

    if not is_multi_extract:
        clear_folder(output_dir) # for multi extract 

    # TODO handle this 
    # print("oh boy",feature_file_path)
    # try:
    #     await generateFeatureDocs(feature_file_path)
    # except Exception as e:
    #     print("Documentation error ", e)

    checkTemplateForVersionUpdate(template_path)

    # logger.print_message(f"Extraction Complete : template saved with name `{template_name}`")
    return feature_file_path