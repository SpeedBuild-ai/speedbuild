import re

from speedbuild.agent.tools.break_chunk import break_chunk
from speedbuild.agent.tools.read_file import read_file


# Extract imports
def extract_imports(lines):
    return [line for line in lines if line.startswith("from") or line.startswith("import")]


def strip_comment(line):
    in_single = False
    in_double = False

    for i, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:i].rstrip()  # remove comment part

    return line.rstrip()

# Extract urlpatterns
def extract_urlpatterns(file_name):
    """
    Extracts and returns the individual URL pattern definitions from a Django URL configuration file.
    Args:
        file_name (str): The path to the Django URL configuration file to process.
    Returns:
        List[str]: A list of strings, each representing a single URL pattern definition, indented with a tab.
    Raises:
        ValueError: If no 'urlpatterns' definition is found in the file.
    Side Effects:
        Prints the extracted 'urlpatterns' code to standard output for debugging purposes.
    """
    file_content = read_file(file_name)
    urlpatterns = None
    chunk_name = None

    for chunk in file_content:
        if chunk['code'].strip().startswith("urlpatterns"):
            urlpatterns = chunk['code']
            chunk_name = chunk.get('name')
            break

    if urlpatterns is None:
        return []
        # raise ValueError("Could not find urlpatterns definition in file")
    
    # TODO how do i detect and strip comments in dividual patterns
    
    chunks = break_chunk(file_name, chunk_name)

    # Safely remove opening/closing bracket chunks or the header line without relying on pop indexes.
    filtered = []
    for c in chunks:
        code = c.get('code', '').strip()
        # skip explicit bracket lines or the header line that defines urlpatterns
        if code in ("[", "]"):
            continue
        if code.startswith("urlpatterns"):
            continue

        line = strip_comment(c['code'])
        if not line.endswith(",") and len(line.strip()) > 0:
            line += ","

        filtered.append(line)

    return ["\t" + i.strip() for i in filtered]

# Extract router definitions and rename if necessary
def extract_router(lines, suffix):
    router_defs = {}
    router_lines = []
    router_pattern = re.compile(r"^(\w+)\s*=\s*(\w+Router)\(\)")  # Matches `router = RouterType()`

    for line in lines:
        match = router_pattern.match(line)
        if match:
            router_name, router_type = match.groups()
            new_router_name = f"{router_name}_{suffix}"  # Rename to avoid conflicts
            line = line.replace(router_name, new_router_name)
            router_defs[new_router_name] = router_type
            router_lines.append(line)

    return router_lines, router_defs

# Extract direct `urlpatterns += router.urls` usage and rename routers
def extract_router_urlpatterns(lines, router_dict):

    direct_router_urls = []
    register_url = []

    for line in lines:
        if not(line.startswith("import ") or line.startswith("from ")):
            for old_name, _ in router_dict.items():
                new_name = old_name
                old_name = old_name.split("_")
                old_name.pop()
                old_name = "_".join(old_name)

                if old_name in line:
                    if "urlpatterns" in line:
                        delimeter = "="
                        if "+=" in line:
                            delimeter = "+="

                        code = line.split(delimeter)[1].strip().replace(old_name,new_name)

                        register_url.append(code)
                    else:
                        try:
                            if line.split("=")[1].strip().startswith(_):
                                continue
                        except ValueError:
                            pass

                        direct_router_urls.append(line.replace(old_name,new_name))

    return [direct_router_urls,register_url]


def merge_urls(urls1,urls2,source_url,target_url):

    imports1 = extract_imports(urls1)
    imports2 = extract_imports(urls2)

    # Merge imports without duplicates
    merged_imports = sorted(set(imports1 + imports2))

    urlpatterns1 = extract_urlpatterns(source_url)
    urlpatterns2 = extract_urlpatterns(target_url)

    merge_patterns = sorted(set(urlpatterns1+urlpatterns2))

    # Merge urlpatterns while ensuring all unique paths are included
    patterns = ["urlpatterns = [","\n"]
    patterns.extend(merge_patterns)
    patterns.extend("]")

    router_lines1, router_defs1 = extract_router(urls1, "1")
    router_lines2, router_defs2 = extract_router(urls2, "2")

    # Merge routers while preserving different router names
    merged_router_code = sorted(set(router_lines1 + router_lines2))

    router_urlpatterns1, register_rounter1_urls = extract_router_urlpatterns(urls1, router_defs1)
    router_urlpatterns2, register_rounter2_urls = extract_router_urlpatterns(urls2, router_defs2)

    # Merge router urlpatterns without duplication
    merged_router_urlpatterns = sorted(set(router_urlpatterns1 + router_urlpatterns2))
    merged_router_code += merged_router_urlpatterns

    # merge register_router_urls
    merge_register_router = sorted(set(register_rounter1_urls + register_rounter2_urls))

    # Ensure `include(router.urls)` is only added once
    if any("include(" in line for line in patterns) and merged_router_urlpatterns:
        merged_router_urlpatterns = []  # Avoid duplicate API URL inclusion


    url_code = merged_imports + ["\n"] + merged_router_code + ["\n\n"]

    url_code = [i for i in url_code if len(i.strip()) > 0]

    code = "\n".join(url_code) + "\n\n\n"

    url_code = patterns + [f" + {route}" for route in merge_register_router]
    url_code = [i for i in url_code if len(i.strip()) > 0]
    code += "\n".join(url_code)

    return code