import os
import sys
import django
import inspect
from django.urls import get_resolver


# NOTE : INSTRUCTION : the environment of the project needs to be activated for this to properly work !!!
# NOTE : This only crawl and find urls path, it does not capture websockets path


def get_real_view_object(callback):
    """
    Extract the true view object behind Django/DRF callables.
    Works for:
      - function based views
      - class based views
      - DRF ViewSets + @action routes
    """

    # DRF ViewSet route => callback.cls
    if hasattr(callback, "cls"):
        return callback.cls

    # Class-based view => view_class attribute exists
    if hasattr(callback, "view_class"):
        return callback.view_class

    # Function-based view
    return callback


def parse_django_project(project_path, settings_module):
    """
    project_path: directory containing manage.py
    settings_module: e.g. 'mybookshop.settings'
    """

    project_path = os.path.abspath(project_path)

    # Ensure project path is importable
    if project_path not in sys.path:
        sys.path.insert(0, project_path)

    # Set Django settings
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

    # Boot Django
    django.setup()

    resolver = get_resolver()
    url_patterns = resolver.url_patterns

    results = []

    def walk(patterns, prefix=""):
        for p in patterns:

            # include()
            if hasattr(p, "url_patterns"):
                walk(p.url_patterns, prefix + str(p.pattern))
                continue

            # Build URL path
            full_path = prefix + str(p.pattern)

            # ❌ skip ALL admin URLs
            if full_path.startswith("admin/"):
                continue

            callback = getattr(p, "callback", None)
            if callback is None:
                continue

            # Get the real underlying class/function
            view_obj = get_real_view_object(callback)

            # Extract actual class/function name
            view_name = (
                view_obj.__name__
                if hasattr(view_obj, "__name__")
                else str(view_obj)
            )

            # Find file where defined
            try:
                view_file = inspect.getsourcefile(view_obj) \
                    or inspect.getfile(view_obj)
                if view_file:
                    view_file = os.path.abspath(view_file)
            except Exception:
                view_file = None

            if view_file.startswith(project_path):
                route = {
                    "view_name": view_name,
                    "view_file": view_file,
                }
                if route not in results:
                    results.append(route)

    walk(url_patterns)
    return results

def get_django_feature_views(project_path,settings_path):    
    # settings_path = "jannis_health.settings"
    return parse_django_project(project_path,settings_path)


