import os
import yaml
import json
import shutil
from pathlib import Path 

# from speedbuild.utils.cli.output import StatusManager

from .feature_dependencies import arrangeChunks 
from .extract import extract_feature_code_and_dependencies, getTemplateFileNames, getURLForFeature

from ....utils.cleanup.clear_folder import clear_folder 
from ....utils.django.venv_utils import get_activated_venv 
from ....utils.django.django_utils import ManageDjangoSettings 
from ....utils.file import findFilePath, get_template_output_path 
from ....utils.template.write_feature_file import writeCodeToFeatureFile 
from ....utils.template.template_update import checkTemplateForVersionUpdate 

# remove comments from code before splitting blocks
async def create_temp_from_feature(
        project_path,
        project_name,
        feature_name,
        feature_file_path,
        template_django_apps,
        installedPackages,
        skip_debug
    ):

    venv = get_activated_venv()
    
    # get settings conf from django.conf.settings TODO
    app_name = os.path.dirname(feature_file_path)

    if app_name == os.path.abspath(app_name): #incase app_name holds an abs path just get the base name
        app_name = os.path.basename(app_name)


    findFilePath(project_path, "urls.py")

    # use conditional statement to check if file is found
    project_name = findFilePath(project_path, "asgi.py")

    if len(project_name) == 0:
        raise(ValueError("Cannot find django project settings file"))
    
    template_dep = set()
    installed_apps = set()
    project_name = project_name[0].split("/")[0]
    settings_path = os.path.join(project_path, project_name,"settings.py")

    project_dir = [folder for folder in os.listdir(project_path) if os.path.isdir(os.path.join(project_path,folder))]

    settings = ManageDjangoSettings(settings_path,venv)

    processed = set()


    # start; make recursive

    output_folder_name = "sb_output_"+feature_name

    template_settings_import,template_confs,template_dep = extract_feature_code_and_dependencies(
        feature_file_path,
        feature_name,
        project_path,
        project_dir,
        app_name,
        template_django_apps,
        settings,
        project_name,
        installed_apps,
        template_dep,
        processed,
        [],
        None,
        output_folder_name,
        installedPackages
    )

    # end recursion
    output_dir = os.path.join(".","output",output_folder_name)

    # Create template yaml file
    template_confs = arrangeChunks(template_confs,[],[])

    template_path = get_template_output_path(feature_name)
    template_name = os.path.basename(template_path)

    django_package_cache_path = os.path.join(str(Path.home()),".sb",template_name,"django_package_cache.json") #TODO Check here

    if os.path.exists(django_package_cache_path):
        with open(django_package_cache_path) as package_cache:
            package_cache = json.loads(package_cache.read())
            template_dep = template_dep.union(set(package_cache['packages']))

        # remove cache packages
        os.remove(django_package_cache_path)
    
    data = {
        "feature" : feature_name,
        "feature_file_path" : feature_file_path.replace(project_path,""),
        "source_project":project_name,
        "dependencies" : list(template_dep),
        "settings" : {
            "imports" : list(sorted(set(template_settings_import))),
            "installed_apps" : list(installed_apps),
            "middlewares" : settings.getTemplateMiddleWare(list(installed_apps)),
            "configurations" : template_confs#list(set(template_confs))
        }
    }

    code_info = {
        "code":data,
        "name":"feature_settings",
        "file_name":"settings.py",
        "imports":list(sorted(set(template_settings_import))),
        "dependencies":list(template_dep),
        "doc":None
    }
    
    writeCodeToFeatureFile(os.path.join(output_dir,"feature.json"),code_info)

    yaml_file_path = os.path.join(output_dir,f"sb_{feature_name}.yaml")

    with open(yaml_file_path, 'w') as file:
        yaml.dump(data, file, default_flow_style=False,sort_keys=False)


    # TODO : find a way to detect 
    try:
        # if views.py in models, generate url for feature
        getURLForFeature(feature_name,feature_file_path,app_name,project_path,output_folder_name)
    except Exception as e:
        print(f"Error processing URL : {e}")

    # create template documentations here
    tem_files = getTemplateFileNames(output_dir)
    tem_files = sorted(tem_files, key=lambda x: not x.startswith('.sb_utils')) #process dependencies first
    # Exclude the yaml file

    # Save template to user main dir in the .sb_zip folder
    user_dir = str(Path.home())
    user_dir = os.path.join(user_dir,".sb_zip")

    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    feature_file_path = os.path.join(output_dir,"feature.json")

    # print("feature file path : ",feature_file_path)
    feature_template_file = os.path.join(user_dir,f"{feature_name}.json")
    
    # structure templates to include versions
    if skip_debug:
        checkTemplateForVersionUpdate(template_path)
        # generate Documentations
        # await generateFeatureDocs(feature_file_path)

        shutil.move(feature_file_path,os.path.join(user_dir,f"{feature_name}.json")) #TODO

    is_multi_extract = os.environ.get("multi_extract",'False') == "True"
    if not is_multi_extract:
        # delete output folder
        clear_folder(output_dir)

    return template_path,feature_template_file


async def createTemplate(
        file_path, 
        feature,
        project_name,
        packageToNameMapping,
        project_root,
        append_root=False,
        installedPackages={},
        run_debug=True,
    ):

    # logger = StatusManager()

    if append_root:
        file_path = os.path.join(project_root,file_path)
    else:
        file_path = file_path.replace(project_root,"").lstrip("/")

    # file_path = file_path.lstrip("/")

    # if run_debug:
    #     logger.start_status("Extracting Feature")
    # else:
    #     logger.start_status("Re-extracting debugged feature")

    # print("\n##### Extracting Feature : ",feature," ##### from ",file_path)

    if not os.path.exists(file_path):
        print("invalid feature",file_path)
        return

    template_path, extracted_file_name = await create_temp_from_feature(
        project_root,
        project_name,
        feature,
        file_path,
        packageToNameMapping,
        installedPackages,
        run_debug
    )

    # logger.stop_status("Feature Extracted")


    # debug template to catch error our algorithm missed
    if run_debug:
        os.environ['run_documentation'] = "True"

    if not run_debug:
        os.environ['run_documentation'] = "False"
        # logger.print_message(f"Template `{template_path}` Created")

    return extracted_file_name
