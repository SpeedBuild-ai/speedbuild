def mergeImportDict(dict1,dict2):
    for item in dict2:
        if item in dict1.keys():
            for entry in dict2[item]:
                if entry not in dict1[item]:
                    dict1[item].append(entry)
        else:
            dict1[item] = dict2[item]
            
    return dict1

def formES6Import(nameImport,others,dep):
    import_str = "import "
    if len(nameImport) > 0:
        import_str += "{" + ','.join(nameImport) + "} "

    if len(others) > 0:
        if import_str.lstrip().endswith("}"):
            import_str += ","
        import_str += f"{','.join(others)} "

    import_str += f'from "{dep}"'
    return import_str


def formRequireStyleImport(namedImport,others,dep):
    import_str = ""
    if len(namedImport) > 0:
        import_str += "{" + ','.join(namedImport) + "} "

    if len(others) > 0:
        if import_str.lstrip().endswith("}"):
            import_str += ","
        import_str += f"{','.join(others)} "

    import_str = f'const {import_str} = require("{dep}")'
    return import_str


def convertToImportStatements(data):
    # TODO we've not added alias or accounted for import with aliases
    imports = []

    for i in data:
        element = data[i]
        nameInport = []
        others = []
        use_require = element[0]["use-require"]


        for item in element:
            newImport = f"{item['dep']} as {item['alias']}" if item['alias'] is not None else item['dep']

            if "standalone" not in item.keys():
                others.append(newImport)
                continue

            if item['standalone'] == False:
                nameInport.append(newImport)
            else:
                others.append(newImport)

        if use_require:
            import_str = formRequireStyleImport(nameInport,others,i)
        else:
            import_str = formES6Import(nameInport,others,i)

        imports.append(import_str)

    return imports

def getDepFromImportDict(data,dep_names):
    deps = []

    for entry in data:
        if entry['dep'].strip() in dep_names:
            deps.append(entry)

    if len(deps) > 0:
        return deps
    
    return None