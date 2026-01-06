import os
import asyncio

from ...utils.parsers.python.parser import PythonBlockParser
from ...utils.parsers.javascript_typescript.jsParser import JsTxParser
from ...frameworks.express.extraction.jsDep import getChunkDependencies
from ...frameworks.django.extraction.feature_dependencies import getBlockDependencies


def formatPythonOutput(chunks):
    read_data = []
    import_data = []

    for chunk in chunks:
        if chunk.startswith("from ") or chunk.startswith("import "):
            import_data.append(chunk)
        else:
            dependencies_data = []
            dependencies = getBlockDependencies(chunk,chunks)
            for dep in dependencies:
                if not dep['packagePath'].startswith("django."):
                    data = {
                        "name":dep['imports'],
                        "source":dep['packagePath']
                    }
                    if data not in dependencies_data:
                        dependencies_data.append(data)
                        
            read_data.append({
                "name":f"chunk_{len(read_data)+1}",
                "code":chunk,
                "dependencies":dependencies_data
            })

    if len(import_data) > 0:
        read_data.insert(0,{
            "name":"import_chunk",
            "code":"\n".join(import_data)
        })

    return read_data

def getDepSource(import_data,dep):
    for i in import_data:
        elememt = import_data[i]
        for entry in elememt:
            if entry['dep'] == dep:
                return i
    return None

def formatJavascripttOutput(imports,chunks,chunk_names,import_deps):
    read_data = []

    for chunk in chunks:
        dependencies_data = []
        dependencies = getChunkDependencies(chunk,chunk_names,False)

        for dep in dependencies:
            source = getDepSource(import_deps,dep)
            if source == None:
                source = "."

            data = {
                "name":dep,
                "source":source
            }
            dependencies_data.append(data)

        read_data.append({
            "name":f"chunk_{len(read_data)+1}",
            "code":chunk,
            "dependencies":dependencies_data
        })

    read_data.insert(0,{
        "name":"import_chunk",
        "code":"\n".join(imports)
    })

    return read_data


def formatOutput(chunks,file_type):
    if file_type == "python":
        return formatPythonOutput(chunks)

    return formatJavascripttOutput(chunks)    

def read_file(file_name : str):
    """
    Get File content.

    Args:
        file_name (str) : absolute path of file

    Returns:
        List of chunks of file content
    """
    if not os.path.exists(file_name):
        return None
    
    
    if file_name.endswith(".py"):
        with open(file_name,"r") as file:
            chunks = PythonBlockParser().parse_code(file.read())
            return formatPythonOutput(chunks)
    else:
        imports,chunks,variableToChunkMapping,import_deps = asyncio.run(JsTxParser().parse_code(file_name))
        return formatJavascripttOutput(imports,chunks,variableToChunkMapping,import_deps)

    # print(chunks)
    


# if __name__ == "__main__":
#     file_name = "/home/attah/.sb/environment/express/controllers/contact_controller.js"
#     data = read_file(file_name,"js")

#     print(data)

#     # for chunk in data:
#     #     print(chunk['name'])
#     #     print(chunk['code'])
#     #     if chunk['name'] != "import_chunk":
#     #         print("\n",chunk['dependencies'])
#     #     print("\n","-"*30,"\n")