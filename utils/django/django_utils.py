import os
import re
import sys
import ast
import site
import importlib

import django 
from django.conf import settings 

from speedbuild.utils.file import findFilePath
from speedbuild.utils.parsers.python.parser import PythonBlockParser
from speedbuild.frameworks.django.extraction.feature_dependencies import get_if_blocks, getCodeBlockNameAndType, remove_multiline_comments


django_defaults = [
    "BASE_DIR",
    "SECRET_KEY",
    "DEBUG",
    "ALLOWED_HOSTS",
    "INSTALLED_APPS",
    "MIDDLEWARE",
    "ROOT_URLCONF",
    "TEMPLATES",
    "WSGI_APPLICATION",
    "DATABASES",
    "AUTH_PASSWORD_VALIDATORS",
    "LANGUAGE_CODE",
    "TIME_ZONE",
    "USE_I18N",
    "USE_TZ",
    "STATIC_URL",
    "DEFAULT_AUTO_FIELD"
]

default_django_apps = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

class ManageDjangoSettings():
    def __init__(self,settings_path, venv_path):
        self.venv_path = venv_path
        self.settings_path = settings_path
        self.parser = PythonBlockParser()
        self.blocks = []
        self.blocks_without_comments = []
        self.code_mappings = {}

    def load_django_settings(self):
        """Loads Django settings dynamically from a given settings.py path."""
        settings_dir = os.path.dirname(self.settings_path)
        settings_module_name = "custom_settings"

        sys.path.insert(0, settings_dir)  # Add settings directory to Python path

        spec = importlib.util.spec_from_file_location(settings_module_name, self.settings_path)
        settings_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings_module)

        installed_packages = []

        if not settings.configured:  # Only configure if settings aren't already set
            settings.configure(
                INSTALLED_APPS=installed_packages,
                **{
                    key: getattr(settings_module, key)
                    for key in dir(settings_module) if key.isupper() and key != "INSTALLED_APPS"
                }
            )

        django.setup()  # Initialize Django

        return settings_module
    
    def getAllSourceProjectApps(self,source_apps):
        self.allSourceProjectApps = ast.literal_eval(source_apps.split("=", 1)[1].strip())

    def getTemplateMiddleWare(self,apps):

        try:
            MIDDLEWARE = self.code_mappings["MIDDLEWARE"]
        except KeyError:
            self.getSettingsVariablesName()
            MIDDLEWARE = self.code_mappings["MIDDLEWARE"]
            
        MIDDLEWARE = ast.literal_eval(MIDDLEWARE.split("=", 1)[1].strip())

        template_middleware = []

        for middleware in MIDDLEWARE:
            start = middleware.split(".")[0]
            if start in apps:
                template_middleware.append(middleware)

        return [template_middleware,MIDDLEWARE]


    def getSettingsVariablesName(self,get_code=False):
        with open(self.settings_path,"r") as file:
            data = file.read()
            data_without_multiline_comment = remove_multiline_comments(data)
            chunks = self.parser.parse_code(data)
            self.blocks = chunks

            setting_imports = []

            self.blocks_without_comments = self.parser.parse_code(data_without_multiline_comment)

            var_names = []
            var_name_to_code = {}
            all_variables = {}

            
            for chunk in chunks:
                if not (chunk.startswith("import ") or chunk.startswith("from ")) and not chunk.startswith("#") and not chunk.startswith('"'):
                    try:
                        var_name, var_type = getCodeBlockNameAndType(chunk)


                        if var_name == "MIDDLEWARE" or var_name not in django_defaults:
                            var_names.append(var_name)
                            var_name_to_code[var_name] = chunk

                        elif var_name == "INSTALLED_APPS":
                            self.getAllSourceProjectApps(chunk)

                            # print(var_name ,"is of type ",var_type)

                        if var_type == "if_statement":
                            # pass
                            condtional_statements = get_if_blocks(chunk)
                            for condition in condtional_statements:
                                body = condition['body']
                                if body:
                                    body = body.split("\n")
                                    for line in body:
                                        new_var_name, _ = getCodeBlockNameAndType(line)
                                        all_variables[new_var_name] = chunk
                                        # print("line ",new_var_name)

                                        if new_var_name not in django_defaults:
                                            var_names.append(new_var_name)
                                            var_name_to_code[new_var_name] = chunk

                                # print(body)
                        else:
                            all_variables[var_name] = chunk
                    except:
                        pass

                elif chunk.startswith("import ") or chunk.startswith("from "):
                    setting_imports.append(chunk)

            self.custom_conf = var_names
            self.code_mappings = var_name_to_code
            self.all_variables = all_variables

            self.setting_imports = setting_imports
            return var_names

    def use_venv(self):
        """Modifies sys.path to use the site-packages from the specified virtual environment."""
        python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
        
        if os.name == "nt":  # Windows
            site_packages = os.path.join(self.venv_path, "Lib", "site-packages")
        else:  # Linux/macOS
            site_packages = os.path.join(self.venv_path, "lib", python_version, "site-packages")

        if not os.path.exists(site_packages):
            raise FileNotFoundError(f"Site-packages directory not found in {self.venv_path}")

        sys.path.insert(0, site_packages)  # Prioritize this venv


    def get_app_paths(self,external_apps):
        """Returns the filesystem paths of third-party installed Django apps (excluding custom apps)."""

        # Ensure imports come from the specified virtual environment
        self.use_venv()

        app_paths = {} #get_venv_site_packages("/home/attah/jannis/venv")#
        site_packages = site.getsitepackages()  # Get site-packages directories

        def get_module_path(module_name):
            spec = importlib.util.find_spec(module_name)
            if spec and spec.origin:
                return os.path.dirname(spec.origin)
            return None
        
        for app in external_apps:
            try:
                module = importlib.import_module(app)
                app_path = os.path.dirname(module.__file__)

                app_paths[app] = app_path
            except ImportError:
                print(f"Warning: Could not import {app}")
            except TypeError:
                site_packages_path = os.path.join(self.venv_path, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages")
                if os.path.exists(site_packages_path):
                    module_path = os.path.join(site_packages_path, app)
                    if os.path.exists(module_path):
                        app_paths[app] = module_path

        return app_paths

    def extract_words_from_code(self,code):
        # Extract words using regex (identifiers, keywords, function names, variable names)
        words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', code)
        
        return set(words)

    def find_settings_import(self,app_path,var_names):
        """Checks if 'from django.conf import settings' is in any file in the app."""
        use_settings = False
        configuration = set()

        for root, _, files in os.walk(app_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if "from django.conf import settings" in line:
                                # print(app_path, " ", file)
                                words = self.extract_words_from_code(f.read())
                                app_configuration = words.intersection(set(var_names))
                                configuration = configuration.union(app_configuration)
                                use_settings = True

        return [use_settings, list(configuration)]
    

    def getDjangoAppsConfigurations(self,apps):
        var_names = self.getSettingsVariablesName(self.settings_path)

        # print("here with apps ",var_names)

        # print("here with variable names ",var_names)
        conf_list = []

        self.load_django_settings()

        # apps.append("zoho_zeptomail")


        app_paths = self.get_app_paths(apps)

        # print("\nChecking for 'from django.conf import settings' in installed third-party apps...\n")
        for app, path in app_paths.items():
            use_setting, conf = self.find_settings_import(path,var_names) 
            if use_setting and len(conf) > 0:
                conf_list.extend(conf)
                # print(app," ",conf, " new conf")

        return conf_list
    

def get_project_settings(project_path):
    path = findFilePath(project_path,"asgi.py")
    if len(path) == 0:
        raise ValueError("not a django project, ensure you specified the right path")
    
    path = path[0]
    path = os.path.join(os.path.dirname(path),"settings.py") #path.split("/")
    # path.pop()
    # path.append("settings.py")
    # path = "/".join(path)

    settings_path = os.path.join(project_path,path)
    chunks = []

    with open(settings_path,"r") as file:
        data = file.read()
        chunks = PythonBlockParser().parse_code(data)

    # print(settings_path," path ")
    
    return [settings_path,chunks]

def updateMiddleware(temp_middleware,source,proj_middleware):
    if len(temp_middleware) > 0:
        for i in temp_middleware:
            index_in_source = source.index(i)
            insert_index = None
            if i not in proj_middleware:
                for x in range(index_in_source+1,len(source)):
                    if source[x] in proj_middleware:
                        insert_index = proj_middleware.index(source[x])
                        break
            
            if insert_index:
                proj_middleware.insert(insert_index, i)
            else:
                proj_middleware.append(i)
                
    return proj_middleware