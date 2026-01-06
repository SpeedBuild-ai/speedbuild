import os

from ....utils.file import findFilePath 
from ....utils.parsers.python.parser import PythonBlockParser 

from ....utils.django.django_utils import django_defaults
from ....utils.django.django_app_dependencies import get_package_version

from .write_dependency import OneStep, writeCodeToFile
from .feature_dependencies import extract_words_from_code, get_code_block_names, getBlockDependencies, getFileDependencies

            
def getUrlPathForViews(feature,path):
    path_import = ["from django.urls import path"]
    urlpatterns = []

    with open(path,"r") as file:
            data = file.read()
            file_dependencies = PythonBlockParser().parse_code(data)
            chunkImport = [i for i in file_dependencies if i.startswith("import ") or i.startswith("from ")]

            file_dependencies = [chunk for chunk in file_dependencies if not (chunk.startswith("import ") or chunk.startswith("from "))]

            urlPaths = None

            for deb in file_dependencies:
                if get_code_block_names(deb,"urlpatterns"):
                    urlPaths = deb
                    break

            if urlPaths != None:
                urlPaths = urlPaths.split("\n")
                if len(urlPaths) > 1:
                    for path in urlPaths:
                        if feature in path:
                            if not path.endswith(","):
                                path += ","

                            urlpatterns.append(path)
                            view = path.split(",")[1].strip()

                            for importLine in chunkImport:
                                imports = importLine.split("import")[1]
                                imports = imports.replace("(","")
                                imports = imports.replace(")","").strip()

                                if "," in imports:
                                    imports = imports.split(",")
                                else:
                                    imports = [imports]

                                for i in imports:
                                    i = i.strip()
                                    if view.startswith(i):
                                        path_import.append(importLine.strip())
    return [urlpatterns, path_import]

def handleRouterURL(view_name,path):
    url_imports = ['from django.urls import path']
    url_content = []

    with open(path,"r") as file:
        data = file.read()
        chunks = PythonBlockParser().parse_code(data)
        feature = None
        initialized_pattern = False

        for chunk in chunks:
            if view_name in chunk and not(chunk.startswith("import ") or chunk.startswith("from ")):
                feature = chunk
                break
            elif "views" in chunk and (chunk.startswith("import ") or chunk.startswith("from ")):
                url_imports.append(chunk)

        if feature is None:
            raise ValueError("Feature Not found in urls.py")
        
        router_var = feature.split(".")[0]
        router_words = [view_name]

        for i in chunks:
            if i.split("=")[0].strip() == router_var:
                var, val = i.split("=")
                if "(" in val:
                    val = val[:val.index("(")]
                router_words.extend([var.strip(),val.strip()])
                break

        for chunk in chunks:
            words_in_chunk = extract_words_from_code(chunk)
            intercept = words_in_chunk.intersection(router_words)
            
            if len(intercept) > 0:
                if chunk.startswith("import ") or chunk.startswith("from "):
                    url_imports.append(chunk)
                else:
                    if "urlpatterns" in chunk:
                        urlpatterns_var = chunk.split("=")[0].strip()

                        if initialized_pattern == False and urlpatterns_var != "urlpatterns":
                            url_content.append("urlpatterns = []")
                        else:
                            initialized_pattern = True
                            

                    url_content.append(chunk)

        # merge import and content
        # url_imports = "\n".join(url_imports)
        url_content = "\n".join(url_content)

        # url_code = f"{url_imports}\n\n{url_content}"

        # print(url_code)
        return [url_content,url_imports]


def getTemplateFileNames(path):
    file_paths = []
    for root, _, files in os.walk(path):
        for file in files:
            # Get the relative path to the base directory
            relative_path = os.path.relpath(os.path.join(root, file), path)
            file_paths.append(relative_path)
    return file_paths


def getURLForFeature(feature,file_path,app_name,project_path,output_dir):
    """
        if pattern not in urlpattern,
        check if pattern is in other chunks
        then get chunk dependencies and imports
    """

    path_folder = os.path.dirname(file_path)
    path = os.path.join(path_folder,"urls.py")

    # path = file_path.split("/")
    # path.pop()  #remove current file in path
    # path.append("urls.py") #add urls.py to path
    # path_list = path
    # path = "/".join(path)
    parser = PythonBlockParser()

    template_file_path = os.path.join("sb_app","urls.py")

    if os.path.exists(path):
        urlpatterns, imports = getUrlPathForViews(feature,path)

        if len(urlpatterns) > 0:
            urlpatterns = "\n".join(urlpatterns)
            urlpatterns = f"urlpatterns = [\n{urlpatterns}\n]"
            # imports = "\n".join(imports)
        else:
            try:
                urlpatterns, imports = handleRouterURL(feature,path)
                if len(urlpatterns.strip()) == 0:
                    return

                # print("url ",template_file_path, " ", output_dir)
                writeCodeToFile(template_file_path,urlpatterns,imports,[],False,output_dir)
            except ValueError as error:
                pass#print(error)

    else:
        # TODO: get and loop through all url files in the project
        project_urls_files = findFilePath(project_path,"urls.py")

        for url in project_urls_files:
            path = os.path.join(project_path,url)

            with open(path,"r") as file:
                data = file.read()
                chunks = parser.parse_code(data)
                for chunk in chunks:
                    if chunk.startswith(f"from {app_name}"):
                        urlpatterns, imports = getUrlPathForViews(feature,path)

                        if len(urlpatterns) > 0:
                            urlpatterns = "\n".join(urlpatterns)
                            urlpatterns = f"urlpatterns = [\n{urlpatterns}\n]"
                            # imports = "\n".join(imports)
                            # print("url ",template_file_path, " ", output_dir)
                            writeCodeToFile(template_file_path,urlpatterns,imports,[],False,output_dir)
                        break

def extract_feature_code_and_dependencies(
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
        template_settings_import=[],
        template_confs = None,
        output_dir = None,
        cache = {}
    ):
    
    # print("feature file path ", feature_file_path)
    # print("output dir is ", output_dir)
    
    # get template conf from OneStep
    packages,use_email,settings_conf = OneStep(
        file_path=feature_file_path,
        feature=feature_name,
        project_root=project_path,
        folders_in_project_root=project_dir,
        writeToFile=True,
        app_name=app_name,
        project_name=project_name,
        use_email=False,
        settings_conf=[],
        output_dir = output_dir
    )

    if template_confs == None:
        template_confs =[]

    if len(packages) > 0:

        for package in packages:
            package = package.split(" ")[0].strip()

            if package in template_django_apps.keys():

                for pack in template_django_apps[package]['pkg']:
                    version = get_package_version(pack)
                    if version == "unknown":
                        version = None

                    if version:
                        template_dep.add(f"{pack}=={version}")
                    else:
                        template_dep.add(f"{pack}")
                installed_apps.add(package)
            else:

                probable_package = []

                if package not in cache.keys():
                    # TODO : work here ask the user for clarification

                    for pkg in cache:
                        if package in cache[pkg]:
                            probable_package.append(pkg) #Investigate here TODO

                    if len(probable_package) == 1:
                        package = probable_package[0]
                    elif len(probable_package) > 1:
                        # Ask user to select package that they used
                        while True:
                            user_input = input(f"Please which of this packages does ur feature depend on \n {probable_package}")
                            if user_input.strip() in probable_package:
                                package = user_input.strip()
                                break

                            print("Please Enter the correct package to proceed")
                    # print("couldnt find package ",package)
                    
                if len(probable_package) > 0:
                    version = get_package_version(package)
                    if version == "unknown":
                        version = None
                    if version:
                        template_dep.add(f"{package}=={version}")
                    else:
                        template_dep.add(package)


        conf_list = settings.getDjangoAppsConfigurations(list(installed_apps))

        conf_list.extend(settings_conf)

        # print("conf list = ",conf_list)

        remaining_conf = set(settings.custom_conf).difference(set(conf_list))

        if use_email and "EMAIL_BACKEND" in remaining_conf:
            conf_list.append("EMAIL_BACKEND")
            if "DEFAULT_FROM_EMAIL" in remaining_conf:
                conf_list.append("DEFAULT_FROM_EMAIL")


        conf_list = [i for i in conf_list if i not in processed][::-1]
        conf_queue = conf_list

        # get internal conf depenencies
        while len(conf_queue) > 0:
            conf = conf_queue.pop(0)

            if conf in processed or conf in django_defaults:
                # processed.add(conf)
                continue

            processed.add(conf)

            conf_code = settings.code_mappings[conf]

            # Here
            if conf_code not in template_confs:
                template_confs.append(conf_code) #add conf to list

            extFileDependencies = getFileDependencies(conf_code,project_name) # get external dependencies
            fileDependencies = getBlockDependencies(conf_code,settings.blocks) # in file dependencies

            # print("external conf dependencies ",extFileDependencies)
            # print("internal conf dependencies ", fileDependencies)

            # manage conf internal dependencies
            for dep in fileDependencies:
                source = dep['packagePath'].strip()
                imports = dep['imports'].strip()

                if source == imports:
                    template_settings_import.append(f"import {imports}")
                elif source != ".":
                    template_settings_import.append(f"from {source} import {imports}")
                else:
                    
                    if imports not in conf_list and imports not in processed:
                        conf_queue.append(imports)

            # manage conf external dependencies
            if len(extFileDependencies) > 0:
                for dep in extFileDependencies:
                    path, feature = dep
                    # print("handling dep ",dep)
                    main_dir = path.split("/")[0].strip()

                    # print(main_dir, " ",project_dir)

                    # if main_dir not in installed_apps:
                    # if main_dir in project_dir:
                    path = os.path.join(project_path,path)
                    if os.path.exists(path):

                        # TODO : sort conf here
                        # pop template_confs
                        # replace path
                        # re add to template_confs
                        code = template_confs.pop()

                        path = path.replace(".py","").replace(project_path,"")
                        if path.startswith("/"):
                            path = path[1:]

                        path_list = path.split("/")
                        start = path_list.pop(0)

                        if start == project_name:
                            path_list.insert(0,"<sb_ext>")
                        elif start == app_name:
                            path_list.insert(0,"<sb_ext_app>")
                        else:
                            path_list.insert(0,"<sb_ext_app>.sb_utils")

                        new_path = ".".join(path_list)

                        path = path.replace("//",".").replace("/",".")
                        

                        code = code.replace(path,new_path)

                        # print("path to get external conf ",path, " feture ",feature)  

                        path = os.path.join(project_path,f"{path}.py")#project_path + "/" + path.replace(".","/") + ".py"

                        # re add template conf
                        if code not in template_confs:
                            template_confs.append(code)


                        # Test environment start
                        _, template_confs, template_dep = extract_feature_code_and_dependencies(
                            path,
                            feature,
                            project_path,
                            project_dir,
                            app_name,
                            template_django_apps,
                            settings,
                            project_name,
                            installed_apps,
                            template_dep,
                            processed,
                            template_settings_import,
                            template_confs,
                            output_dir
                        )

                        # Test environment End
                                
                    else:
                        # print("here ok processinf conf for ",main_dir)
                        for item in cache:
                            if main_dir in cache[item]:
                                version = get_package_version(item)
                                if version == None or version == "unknown":
                                    template_dep.add(item)
                                else:
                                    template_dep.add(f"{item}=={version}")


                                # add main_dir to installed_apps so we can get configurations associated with package
                                installed_apps.add(main_dir)

                                new_conf = settings.getDjangoAppsConfigurations(list(installed_apps))
                                # print("\nfound new ",new_conf,"\n")

                                # check if main_dir is in source project installed apps
                                in_source_project_apps = settings.allSourceProjectApps
                                if main_dir not in in_source_project_apps:
                                    installed_apps.remove(main_dir)

                                # add to queue
                                for _conf in new_conf:
                                    if _conf not in conf_list and _conf not in processed: 
                                        conf_queue.append(_conf)

                                remaining_conf = remaining_conf.difference(conf_list)

                        # with open("sb_app_mapping_cache.json","r") as cacheFile:
                        #     cache = json.loads(cacheFile.read())
                        #     for item in cache:
                        #         if main_dir in cache[item]:
                        #             template_dep.add(item)

                        #             # add main_dir to installed_apps so we can get configurations associated with package
                        #             installed_apps.add(main_dir)

                        #             new_conf = settings.getDjangoAppsConfigurations(list(installed_apps))
                        #             # print("\nfound new ",new_conf,"\n")

                        #             # check if main_dir is in source project installed apps
                        #             in_source_project_apps = settings.allSourceProjectApps
                        #             if main_dir not in in_source_project_apps:
                        #                 installed_apps.remove(main_dir)

                        #             # add to queue
                        #             for _conf in new_conf:
                        #                 if _conf not in conf_list and _conf not in processed: 
                        #                     conf_queue.append(_conf)

                        #             remaining_conf = remaining_conf.difference(conf_list)

    return [template_settings_import, template_confs, template_dep]