import os
import sys
import json
import shutil
import asyncio

from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

from .db.save_feature import batch_save_features_to_db

from .agent.documentation.document_feature import process_feature_file

from .agent.documentation.doc_cache_manager import DocCache
from .agent.documentation.get_feature_code import generateFeatureDocs

from .utils.paths import getProjectRootPath
from .utils.cli.cli_output import StatusManager
from .utils.cleanup.clear_folder import clear_folder
from .utils.package_utils import getPackageNameMapping
from .utils.mcp_config.mcp_conf import mcp_conf_selector
from .utils.config.llm_config_editor.config_editor import ConfigEditor
from .utils.init.init_sb import getSBProjectConfig, initSpeedbuildProject

from .frameworks.django.extraction.extract_features import createTemplate
from .frameworks.express.find.get_paths import getAllExpressProjectRoutes
from .frameworks.express.extraction.extractjs import startExpressExtraction
from .frameworks.django.find.get_django_views import GetAllDjangoExposedFeatures, isFeatureReusable


root_path = getProjectRootPath()
feature_cache_path = os.path.join(root_path,"feature_cache.json")

def getFeatureCache():
    if not os.path.exists(feature_cache_path):
        return {}
    
    with open(feature_cache_path,"r") as f:
        return json.loads(f.read())
    
def saveFeatureCache(data):
    with open(feature_cache_path,"w") as f:
        json.dump(data,f,indent=4)

async def process_feature(feature,semaphore,framework,cache_manager,repo_id=None):
    async with semaphore:
        try:
            await generateFeatureDocs(feature,cache_manager)
        except Exception as e:
            print(
                f"[docs] failed for {feature}: {e}"
            )

async def run_docs_and_upload(features,framework,repo_id):
    # Tune this:
    # 3–5 for OpenAI
    # 8–10 if docs are cached / light
    semaphore = asyncio.Semaphore(5)

    project_root = os.path.abspath(".")
    cache_path = os.path.join(project_root, ".sb", "doc_cache.json")

    doc_cache = DocCache(cache_path)

    tasks = [
        process_feature(feature, semaphore,framework,doc_cache,repo_id)
        for feature in features
        if feature is not None
    ]

    await asyncio.gather(*tasks)

    await doc_cache.flush()

def extractFeature(project_root,args,append_root=False,package_info=None,repo_id=None,framework=None):
    try:
        target = args[2]
        extract_from = args[3]

        if repo_id == None: # Clear output folder before performing single extract
            # clear extraction output folder here
            output_folder = os.path.join(project_root,"output")
            if os.path.exists(output_folder) and package_info == None: #if package_info == None it means this is a single extract. For multiple extracts we will clear the output folder after all extractions ends
                clear_folder(output_folder)
                shutil.rmtree(output_folder)

        # set run_documentation env to its default
        os.environ['run_documentation'] = "False"

        if framework == "django":
            # Extract django feature
            # logger.start_status("Extracting django feature")
            try:
                project_name = os.path.basename(project_root)
                if package_info:
                    packageToNameMapping,installedPackages = package_info
                else:
                    os.environ['speed_build_verbose'] = "True"
                    packageToNameMapping,installedPackages = getPackageNameMapping(project_root)
                feature_file_path = asyncio.run(createTemplate(extract_from,target,project_name,packageToNameMapping,project_root,append_root,installedPackages,True))
            except ValueError as e:
                print(e)
            
        elif framework == "express":
            #Extract Express feature
            feature_file_path = asyncio.run(startExpressExtraction(target,extract_from,project_root))

        if repo_id == None: # single extract
            asyncio.run(process_feature_file([feature_file_path],framework))
            batch_save_features_to_db([feature_file_path])

        return feature_file_path

    except IndexError:
        print("Usage : python speedbuild extract <what_to_extract> <extraction_entry_point>")
        return None

def listExtractedFeature(args):
    print("Listing All Extracted Templates")
    user_home = str(Path.home())
    templates_dir = f"{user_home}/.sb_zip"

    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)

    count = 1
    templates = os.listdir(templates_dir)

    for template in templates:
        if template.endswith(".json"):
            print(f"    {count}) {template}")
            count += 1
        
    print("\n")

def init_worker(pkg_map, installed):
    global PACKAGE_MAP, INSTALLED_PACKAGES
    PACKAGE_MAP = pkg_map
    INSTALLED_PACKAGES = installed

def extractFeature_worker(project_path, args, dry_run,repo_id=None,framework=None):
    """
    Thin worker wrapper.
    Uses globals initialized per process.
    """
    return extractFeature(
        project_path,
        args,
        dry_run,
        [PACKAGE_MAP, INSTALLED_PACKAGES],
        repo_id,
        framework
    )

def extract_all(data, framework, project_path,repo_id=None):
    # One-time setup in main process
    package_map, installed_packages = None,None
    if framework == "django":
        package_map, installed_packages = getPackageNameMapping(project_path)

    extract_logger = StatusManager()
    extract_logger.start_status("Extracting Features")

    max_workers = os.cpu_count() or 4
    futures = []
    final = {}
    extracted = []

    with ProcessPoolExecutor(
        max_workers=max_workers,
        initializer=init_worker,
        initargs=(package_map, installed_packages),
    ) as executor:

        # Submit jobs
        for item in data:
            args = [
                "speedbuild",
                "extract",
                item["feature"],
                item["source_file"],
            ]

            futures.append(
                executor.submit(
                    extractFeature_worker,
                    project_path,
                    args,
                    False,   # dry_run
                    repo_id,
                    framework
                )
            )

        # Collect results as they finish
        for future in as_completed(futures):
            res = future.result()
            if res is not None:
                extracted.append(res)
            if isinstance(res, dict):
                final.update(res)
            # try:
            #     res = future.result()
            #     if res is not None:
            #         extracted.append(res)
            #     if isinstance(res, dict):
            #         final.update(res)
            # except Exception as e:
            #     # IMPORTANT: don't let one failure kill everything
            #     print(f"[extract] worker failed: {e}")

    # ---------- Cleanup (ONLY after workers are done) ----------
    output_folder = os.path.join(project_path, "output")
    if os.path.exists(output_folder):
        try:
            clear_folder(output_folder)
            shutil.rmtree(output_folder)
        except Exception as e:
            print(f"[cleanup] failed: {e}")

    extract_logger.stop_status()

    return extracted

async def GetReusableFeatures(project_path,framework="django"):

    repo_id = 1 #getOrSetRepoId(project_path) # Work here to remove this
    feature_cache = getFeatureCache()

    reusable_features = []

    if framework == "django":
        features = GetAllDjangoExposedFeatures(project_path)
    
    elif framework == "express":
        features,routes_mapping = await getAllExpressProjectRoutes(project_path) #([{'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/controllers/contact_controller.js', 'path': 'createContact'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/contact_routes.js', 'path': 'router'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/controllers/contact_controller.js', 'path': 'getContacts'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/controllers/contact_controller.js', 'path': 'updateContact'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/contact_routes.js', 'path': 'router'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/controllers/contact_controller.js', 'path': 'deleteContact'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/contact_routes.js', 'path': 'sayHello'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/contact_routes.js', 'path': 'router'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/contact_routes.js', 'path': 'router'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/contact_routes.js', 'path': 'sendWelcomeEmail'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/user_routes.js', 'path': 'router'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/controllers/userController.js', 'path': 'loginUser'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/controllers/userController.js', 'path': 'registerUser'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/user_routes.js', 'path': 'router'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/middleware/auth_middleware.js', 'path': 'validateToken'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/user_routes.js', 'path': 'router'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/controllers/userController.js', 'path': 'currentUserInformation'}] ,  {'/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/contact_routes.js:::/': [{'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/controllers/contact_controller.js', 'path': 'createContact'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/contact_routes.js', 'path': 'router'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/controllers/contact_controller.js', 'path': 'getContacts'}], '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/contact_routes.js:::/:id': [{'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/controllers/contact_controller.js', 'path': 'updateContact'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/contact_routes.js', 'path': 'router'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/controllers/contact_controller.js', 'path': 'deleteContact'}], '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/contact_routes.js:::/hello': [{'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/contact_routes.js', 'path': 'sayHello'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/contact_routes.js', 'path': 'router'}], '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/contact_routes.js:::/register': [{'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/contact_routes.js', 'path': 'router'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/contact_routes.js', 'path': 'sendWelcomeEmail'}], '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/user_routes.js:::/login': [{'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/user_routes.js', 'path': 'router'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/controllers/userController.js', 'path': 'loginUser'}], '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/user_routes.js:::/register': [{'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/controllers/userController.js', 'path': 'registerUser'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/user_routes.js', 'path': 'router'}], '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/user_routes.js:::/user-info': [{'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/middleware/auth_middleware.js', 'path': 'validateToken'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/routes/user_routes.js', 'path': 'router'}, {'source': '/home/attah/Documents/work/speedbuildjs/express.js_contact_app/controllers/userController.js', 'path': 'currentUserInformation'}]} )

    logger = StatusManager()

    logger.start_status("Finding Reusable Features, This might take a few minutes")

    tasks = [isFeatureReusable(feature,framework,feature_cache) for feature in features]
    results = await asyncio.gather(*tasks)

    logger.stop_status(f"{len(results)} Reusable Features Found")
    
    reuse_list = []

    for r in results:
        reusable, feature, feature_hash = r

        reuse_list.append((reusable,feature))

        if feature_hash:
            feature_cache[feature_hash] = "REUSABLE" if reusable else "NOT_REUSABLE"

        if reusable and framework == "django":
            reusable_features.append({
                "feature":feature['view_name'],
                "source_file":feature['view_file']
            })

    if framework == "express":
        for route in routes_mapping:
            source,path = route.split(":::")
            
            add_route = True
            views = []
            for entry in routes_mapping[route]:
                views.append({
                    "feature":entry['path'],
                    "source_file":entry['source']
                })

                # TODO : check here; retrieve hash from here
                if (False,entry) in reuse_list:
                    add_route = False

            if add_route:
                reusable_features.append({
                    "feature":path,
                    "source_file":source
                })
            else:
                reusable_features.extend(views)

    saveFeatureCache(feature_cache)

    # clear output folder
    output_folder = os.path.join(project_path,"output")
    if os.path.exists(output_folder): #if package_info == None it means this is a single extract. For multiple extracts we will clear the output folder after all extractions ends
        clear_folder(output_folder)
        shutil.rmtree(output_folder)

    # Extract features here
    extract_logger = StatusManager()
   
    extracted = extract_all(reusable_features,framework,project_path,repo_id)

    extract_logger.print_message(f"{len(reusable_features)} Features Extracted")

    # REMOVE THIS
    extracted = extracted[:10] # NOTE : this is purely for testing, remove this
    # REMOVE THIS

    await process_feature_file(extracted,framework)

    await asyncio.sleep(1)
    
    batch_save_features_to_db(extracted)


def getProjectFramework(project_path):
    # get framework here
    config = getSBProjectConfig(project_path)
    if "framework" not in config:
        print("You need to initialize a speedbuild project first\nrun `speedbuild init` ")
        return None
        
    return config['framework']

def start():
    args = sys.argv
    current_path = os.path.abspath(".")

    try:
        command = args[1]

        if command == "extract":
            # sb.py extract / views.py --express
            framework = getProjectFramework(current_path)

            if framework is not None:
                os.environ['multi_extract'] = "False" #specify we are doing single extract
                extractFeature(project_root=current_path,args=args,framework=framework)

        elif command == "list":
            listExtractedFeature(args)
        
        elif command == "find":
            # get framework here
            framework = getProjectFramework(current_path)
            if framework is not None:
                os.environ['multi_extract'] = "True" # Specify we are doing multi extract
                os.environ['speed_build_verbose'] = "False"

                asyncio.run(GetReusableFeatures(project_path=os.path.abspath("."),framework=framework))

        elif command == "init":
            "Initialize a new speedbuild project"
            initSpeedbuildProject(os.path.abspath("."))

        elif command == "validate":
            "Validate Project code against speedbuild patterns"
            pass

        elif command == "config":
            config_editor = ConfigEditor()
            config_editor.run()
        
        elif command == "mcp-config":
            mcp_conf_selector()

    except IndexError as e:
        print("Available commands :\n- init\n- extract\n- find\n- list\n- validate\n- config\n- mcp-config")

# if __name__ == "__main__":
#     # start()