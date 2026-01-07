import math
import os
import shutil
import tempfile
import subprocess
import importlib.util
import concurrent.futures
from importlib import metadata

from speedbuild.db.relational_db.main import init_db
from speedbuild.db.relational_db.pkg_prepopulate_data import pre_compiled
from speedbuild.db.relational_db.python_packages import batch_save_packages, db_has_python_packages, get_batch_packages, prepopulate_python_packages

from speedbuild.utils.cli.cli_output import StatusManager

MAX_WORKERS = 5  # Reduced from 5 to avoid resource exhaustion
TIMEOUT = 120  # Seconds to wait before considering a package installation hung

def load_django_settings(settings_path):
    """Loads the Django settings module dynamically."""
    spec = importlib.util.spec_from_file_location("settings", settings_path)
    settings_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(settings_module)
    return settings_module

def create_temp_env():
    """Creates a temporary virtual environment and returns its path."""
    temp_dir = tempfile.mkdtemp()
    venv_path = os.path.join(temp_dir, "venv")
    try:
        # Add timeout to avoid hanging
        result = subprocess.run(
            ["python", "-m", "venv", venv_path], 
            check=True, 
            timeout=30  # 30 seconds should be enough for venv creation
        )
        return temp_dir, venv_path
    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        # print(f"Error creating virtual environment: {str(e)}")
        shutil.rmtree(temp_dir)
        raise

def get_site_packages_path(venv_path):
    """Returns the site-packages path for the virtual environment."""
    python_bin = os.path.join(venv_path, "Scripts" if os.name == "nt" else "bin", "python")
    try:
        output = subprocess.run(
            [python_bin, "-c", "import site; print(site.getsitepackages()[0])"],
            capture_output=True,
            text=True,
            timeout=10  # 10 seconds timeout
        )
        return output.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"Timeout getting site-packages path for environment: {venv_path}")
        raise

def install_package(venv_path, package_name):
    """Installs a package in the temporary virtual environment."""
    pip_bin = os.path.join(venv_path, "Scripts" if os.name == "nt" else "bin", "pip")
    try:
        # print(f"Starting installation of {package_name}...")
        process = subprocess.run(
            [pip_bin, "install", package_name], 
            check=True, 
            timeout=TIMEOUT,  # Timeout to prevent hanging
            capture_output=True,
            text=True
        )
        # print(f"Detected {package_name}")
        return True
    except subprocess.TimeoutExpired:
        # print(f"Installation of {package_name} timed out after {TIMEOUT} seconds")
        return False
    except subprocess.SubprocessError as e:
        # print(f"Error installing {package_name}: {str(e)}")
        return False

def detect_installed_apps(site_packages_path):
    """Detect likely Django apps in site-packages."""
    try:
        apps = []
        for item in os.listdir(site_packages_path):
            full_path = os.path.join(site_packages_path, item)

            # Ignore metadata folders
            if item.endswith(".dist-info") or item.endswith(".egg-info"):
                continue

            # Include real directories
            if os.path.isdir(full_path):
                # Check for __init__.py to confirm it's a module
                # if os.path.isfile(os.path.join(full_path, "__init__.py")):
                #     apps.append(item)
                apps.append(item)
        return apps
    except Exception as e:
        print(f"Error detecting installed apps: {str(e)}")
        return []

def process_single_package(package_name):
    """Process a single package in its own virtual environment."""
    
    temp_dir = None
    try:
        temp_dir, venv_path = create_temp_env()
        site_packages = get_site_packages_path(venv_path)
        
        success = install_package(venv_path, package_name)
        if not success:
            # print(f"Installation failed for {package_name}")
            return package_name, []
            
        installed_apps = detect_installed_apps(site_packages)
            
        return package_name, installed_apps
    except Exception as e:
        print(f"Error processing {package_name}: {str(e)}")
        return package_name, []
    finally:
        # Cleanup temp environment
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                # print(f"Cleaned up environment for {package_name}")
            except Exception as e:
                pass
                # print(f"Failed to clean up {temp_dir}: {str(e)}")


def get_package_version(package_name):
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        return "unknown"

def get_django_app_from_packages_parallel(package_names, max_batch_size=10):
    """
    TODO : here we dance

    Process multiple package names in parallel to retrieve Django applications.
    This function processes a list of package names to identify Django applications within them,
    utilizing parallel processing for efficiency. It implements caching to avoid reprocessing
    previously analyzed packages.
    Args:
        package_names (list): A list of package names to process.
        max_batch_size (int, optional): Maximum number of packages to process in parallel. 
            Defaults to 10.
    Returns:
        dict: A dictionary mapping package names to lists of discovered Django applications.
            For packages that fail processing or timeout, an empty list is returned.
    Example:
        >>> packages = ['django-allauth', 'django-rest-framework']
        >>> results = get_django_app_from_packages_parallel(packages)
        >>> print(results)
        {'django-allauth': ['allauth', 'allauth.account'], 'django-rest-framework': ['rest_framework']}
    Note:
        - Uses threading for parallel processing
        - Implements timeout handling to prevent hanging
        - Caches results for future lookups
        - Processes packages in batches to manage resource usage
    """

    init_db() # initialize sqlite3 database connection
    
    results = {}
    packages_to_process = list(package_names)  
    
    progress_max_value = math.ceil(len(packages_to_process) / max_batch_size)
    logger = StatusManager(show_percentage=True,max_value=progress_max_value,step=1)
    logger.start_status("Getting Installed packages")

    # Here
    if not db_has_python_packages():
        pre_compiled_pkgs = pre_compiled
        prepopulate_python_packages(pre_compiled_pkgs)

    # Process in smaller batches to prevent resource exhaustion
    for i in range(0, len(packages_to_process), max_batch_size):
        batch = packages_to_process[i:i+max_batch_size]
        # print(f"Processing batch of {len(batch)} packages")

        batch_with_version = [
            f"{i}=={get_package_version(i)}"
            for i in batch
        ]

        res = get_batch_packages(batch_with_version) #from database
        # print("response ", res)

        if len(res) > 0:
            recieved_packages = res['packages']
            recieved_packages_names = [name.split("==")[0].strip() for name in recieved_packages.keys()]
            batch = [name for name in batch if name not in recieved_packages_names ]

            for pkg in recieved_packages:
                results[pkg.split("==")[0]] = recieved_packages[pkg] #remove version from recieved_packages before adding to results
        
        new_packages = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_package = {
                executor.submit(process_single_package, pkg): pkg 
                for pkg in batch
            }
            
            for future in concurrent.futures.as_completed(future_to_package):
                try:
                    package_name, installed_apps = future.result(timeout=TIMEOUT + 30)
                    package_version = get_package_version(package_name)
                    new_packages[f"{package_name}=={package_version}"] = {"pkg":installed_apps,"version":package_version}#installed_apps

                    logger.update_status("Installed Package Detected : "+package_name)
                    # add to reults
                    results[package_name] = {"pkg":installed_apps,"version":package_version}
                    
                except concurrent.futures.TimeoutError:
                    package = future_to_package[future]
                    print(f"Processing timed out for package: {package}")
                    # results[package] = {"pkg":[],"version":None}
                except Exception as e:
                    package = future_to_package[future]
                    # print(f"Exception for package {package}: {str(e)}")
                    # results[package] = {"pkg":[],"version":None}

        # push by batch to the server
        if len(new_packages.keys()) > 0:
            batch_save_packages(new_packages) #write new packages to database
        
        logger.update_progress()

    logger.stop_status("Installed Packages Collected")
    return results

def get_installed_packages(venv_path):
    """Get list of installed packages in the given virtual environment."""
    pip_path = os.path.join(venv_path, "bin", "pip")  # Linux/macOS

    if os.name == "nt":
        pip_path = os.path.join(venv_path, "Scripts", "pip.exe")  # Windows

    try:
        result = subprocess.run(
            [pip_path, "list"], 
            capture_output=True, 
            text=True,
            timeout=30  # 30 seconds timeout
        )
        lines = result.stdout.splitlines()[2:]  # Skip headers
        packages = {line.split()[0] for line in lines}  # Extract package names
        return packages
    except subprocess.TimeoutExpired:
        print("Timeout getting installed packages")
        return set()
    except Exception as e:
        print(f"Error getting installed packages: {str(e)}")
        return set()

def getDjangoAppsPackage(settings_path, venv):
    """
    Maps Django installed apps to their corresponding Python packages.
    This function analyzes the Django settings file to find installed apps and determines
    which Python packages provide those apps. It handles both direct app imports and
    regular Python package imports.
    Args:
        settings_path (str): Path to the Django settings.py file
        venv (str): Path to the Python virtual environment to analyze
    Returns:
        dict: A mapping of Django app names to lists of package names that provide them.
              Returns empty dict if settings file is not found or cannot be loaded.
              Format: {'app_name': ['package1', 'package2']}
    Raises:
        No exceptions are raised - errors are handled internally and logged to stdout
    Example:
        >>> getDjangoAppsPackage('/path/to/settings.py', '/path/to/venv')
        {'django.contrib.admin': ['django'],
         'django.contrib.auth': ['django'],
         'myapp': ['my-package']}
    """
    if not os.path.exists(settings_path):
        print(f"Error: Settings file '{settings_path}' not found!")
        return {}

    # Load Django settings
    try:
        settings_module = load_django_settings(settings_path)
        installed_apps = getattr(settings_module, "INSTALLED_APPS", [])
    except Exception as e:
        print(f"Error loading Django settings: {str(e)}")
        return {}

    # Get all installed packages
    packages = get_installed_packages(venv)
    
    # Process packages in parallel
    package_app_mapping = get_django_app_from_packages_parallel(packages)
    
    # Map Django apps to their packages
    app_mapping = {}
    for package, django_apps in package_app_mapping.items():

        for app in django_apps['pkg']:
            if app in installed_apps:  # or is a regular import
                if app in app_mapping:
                    app_mapping[app]['pkg'].append(package)
                else:
                    app_mapping[app] = {"pkg":[package]}

                    # check if version is not None or Unkmown
                    pkg_version = django_apps['version'] 
                    if pkg_version != None or pkg_version != "unknown":
                        app_mapping[app]['version'] = pkg_version 

    return [app_mapping,package_app_mapping]
