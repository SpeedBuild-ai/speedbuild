from .jsParser import JsTxParser

def parse_object_exports(exports_str):
    """Parse object exports respecting nested braces"""
    result = []
    current = ""
    depth = 0
    
    for char in exports_str:
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
        elif char == ',' and depth == 0:
            if current.strip():
                result.append(current.strip())
            current = ""
            continue
        current += char
    
    if current.strip():
        result.append(current.strip())
    
    return result

async def getModuleExport(filename,deps_set):
    """
        Get export statements of dependencies in a CommonJS/ES6 module.

        Args:
            filename : Path to JS module file
            deps_set : set of dependency names to get export statements for

        Returns:
            list of export statement strings
    """

    parser = JsTxParser() # js parser
    _, chunks, _, _ = await parser.parse_code(filename) #parse file code

    module_export = []

    for chunk in chunks:
        if chunk.strip().startswith("module.exports") or chunk.strip().startswith("export default "):

            if "=" not in chunk:  # Skip if no assignment
                default_es6_export = chunk.replace("export default ","").strip()
                if default_es6_export in deps_set:
                    module_export.append(chunk)

                continue

            declaration,exports = chunk.split("=",1)
            declaration = declaration.strip()

            if declaration == "export default":
                continue

            # process declaration
            if declaration != "module.exports":
                declaration = declaration.replace("module.exports.","").strip()
                if declaration in deps_set:
                    module_export.append(chunk)
                    continue

            # process exports
            exports = exports.strip().rstrip(";")
            if exports.startswith("{") and exports.endswith("}"):
                exports = exports.lstrip("{").rstrip("}")

                # Use smart parser that respects nesting
                export_items = parse_object_exports(exports)

                # module.exports = {foo, bar: {name: "james"}, baz}
                export_lists = []
                for item in export_items:
                    if ":" in item: # meaning we are exporting an object
                        key = item.split(":", 1)[0].strip() # get the key, value pair
                        if key in deps_set:
                            export_lists.append(item)
                    elif item.strip() in deps_set: # we are exporting named exports
                        export_lists.append(item.strip()) # get the named export

                if export_lists:
                    export_data = f"{declaration} = {{ {', '.join(export_lists)} }}"
                    module_export.append(export_data)

            elif exports in deps_set:
                # e.g module.exports = number;
                module_export.append(chunk)

    return module_export