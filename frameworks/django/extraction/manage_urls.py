import ast
from typing import List, Tuple


def extract_views_from_urls(urls_file_path: str) -> List[Tuple[str, str]]:
    # print(f"Extracting views from {urls_file_path}")
    with open(urls_file_path, "r") as f:
        data = f.read()
        data = data.replace(".as_view()", "")

        tree = ast.parse(data, filename=urls_file_path)

        view_names = []
        import_alias_map = {}

        # Step 1: Capture import statements to trace views
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module
                if module == None:
                    module = ""
                for alias in node.names:
                    import_alias_map[alias.asname or alias.name] = f"{module}.{alias.name}"
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    import_alias_map[alias.asname or alias.name] = alias.name

        # Step 2: Find calls to `path()` or `re_path()`
        for node in ast.walk(tree):
            
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("path", "re_path"):
                
                if len(node.args) >= 2:
                    view = node.args[1]
                    if isinstance(view, ast.Attribute):

                        # Something like views.HomeView
                        value_id = view.value.id if isinstance(view.value, ast.Name) else None

                        attr = view.attr
                        full_path = import_alias_map.get(value_id)
                        if full_path:
                            view_names.append(f"{full_path}.{attr}")
                    elif isinstance(view, ast.Name):
                        # Direct function/class reference
                        view_path = import_alias_map.get(view.id)
                        if view_path:
                            view_names.append(view_path)

    return view_names