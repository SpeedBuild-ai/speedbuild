import os
import esprima
from rich.prompt import Prompt
from rich.console import Console

from ..parsers.javascript_typescript.jsParser import JsTxParser 
from ...frameworks.express.extraction.jsDep import getChunkDependencies 
from ...frameworks.express.extraction.move_file import getNewImportPath 
from ...frameworks.express.extraction.handle_js_route import getRoutePathAndMethodsOrReturnNone 

parser = JsTxParser()

def get_express_instance_variable(js_code: str):
    tree = esprima.parseScript(js_code)

    express_var = None
    for node in tree.body:
        # Look for: const app = express();
        if node.type == "VariableDeclaration":
            for decl in node.declarations:
                if (
                    decl.init
                    and decl.init.type == "CallExpression"
                    and decl.init.callee.type == "Identifier"
                    and decl.init.callee.name == "express"
                ):
                    express_var = decl.id.name  # e.g., "app"
    return express_var

def getFileContent(filename):
    with open(filename,"r") as file:
        return file.read()
    return None

def cleanupChunk(chunk,template_express_var,destination_express_var):

    if chunk.strip().startswith(template_express_var):
        chunk = chunk.split(template_express_var)[1:]
        chunk.insert(0,destination_express_var)
        return "".join(chunk)
    return chunk

def findImportStatement(dependency,import_deps):
    for import_path in import_deps:
        dependcies = import_deps[import_path]

        # TODO : get actual import path by crawling project folders

        for i in dependcies:
            if i['dep'] == dependency:
                return [import_path,dependcies]
            
    return None

def processDependencies(
        entry_file_path,
        template_files,
        chunk,
        chunks,
        chunks_name,
        target_listener,
        template_express_var,
        destination_express_var,
        target_chunks,
        import_deps,
        target_import_deps
    ):

    deps = getChunkDependencies(chunk,chunks_name,False)
    for dep in deps:
        
        dep_chunk = chunks_name[dep]

        dep_import = findImportStatement(dep,import_deps)
        if  dep_import is not None:
            path,dep_mapping = dep_import

            cleaned_path = path

            while cleaned_path.startswith("."):
                cleaned_path = cleaned_path[1:]
                if len(cleaned_path) == 1 and cleaned_path == ".":
                    raise ValueError("Invalid path")
                
            for filename in template_files:

                if filename.endswith(cleaned_path):
                    import_path = getNewImportPath(entry_file_path,filename)
                    
                    if not import_path.startswith("."):
                        import_path = f"./{import_path}"

                    target_import_deps[import_path] = dep_mapping
                    break
    
        if dep_chunk not in target_chunks and dep_chunk in chunks:
            insert_index = target_chunks.index(target_listener)
            insert_chunk = cleanupChunk(dep_chunk,template_express_var,destination_express_var)

            if insert_chunk not in target_chunks:
                target_chunks.insert(insert_index,insert_chunk)
            
            # recursive with dep_chunk
            target_chunks,import_deps = processDependencies(entry_file_path,template_files,dep_chunk,chunks,chunks_name,target_listener,template_express_var,destination_express_var,target_chunks,import_deps,target_import_deps)

    insert_index = target_chunks.index(target_listener)
    insert_chunk = cleanupChunk(chunk,template_express_var,destination_express_var)
    
    if insert_chunk not in target_chunks:
        target_chunks.insert(insert_index,insert_chunk)
    
    return target_chunks,target_import_deps

# what are you doing?
async def mergeEntryFiles(project_entry, template_entry,template_files=None,logger=None):

    logger.start_status("Processing project entry file")

    entry_file = os.path.dirname(project_entry)

    first = getFileContent(project_entry)
    template = getFileContent(template_entry)

    express_var_name_first = get_express_instance_variable(first)
    express_var_name_second = get_express_instance_variable(template)

    template = template.replace(f"{express_var_name_second}",express_var_name_first)

    _,chunks,chunks_name,import_deps = await parser.parse_code(template_entry)
    

    _,target_chunks,_,target_import_deps = await parser.parse_code(project_entry)
    target_listener = None

    for i in target_chunks:
        if i.strip().startswith(f"{express_var_name_first}.listen"):
            target_listener = i

    try:
        chunks.remove(chunks_name[express_var_name_second])
    except:
        pass

    selected_chunks = []
    for chunk in chunks:
        if chunk.strip().startswith(f"{express_var_name_second}.listen"):
            deps = getChunkDependencies(chunk,chunks_name,raw_code=False)
            for dep in deps:
                if dep in chunks_name.keys():
                    if chunks_name[dep] in selected_chunks:
                        selected_chunks.remove(chunks_name[dep])
        else:
            if chunk.startswith("/") == False:
                selected_chunks.append(chunk)

    logger.stop_status()

    console = Console()

    console.print("\n[bold cyan]Merge Entry File[/bold cyan]")
    console.print("[dim]How would you like to merge dependencies?[/dim]\n")

    console.print("[bold]1.[/bold] Merge all  template entry file dependencies (default)")
    console.print("[bold]2.[/bold] Select dependencies manually\n")

    merge_all = True

    choice = Prompt.ask(
        "[bold green]Choice[/bold green]",
        choices=["1", "2"],
        default="1"
    )

    if choice == "2":
        merge_all = False
    

    for chunk in selected_chunks:
        info = getRoutePathAndMethodsOrReturnNone(chunk,None)
        if info is not None:
           target_chunks,target_import_deps = processDependencies(
                entry_file,
                template_files,
                chunk,
                chunks,
                chunks_name,
                target_listener,
                express_var_name_second,
                express_var_name_first,
                target_chunks,
                import_deps,
                target_import_deps
            )
        else:
            if not merge_all:
                res = Prompt.ask(f"[cyan]Should I add \n{chunk} to entry file (yes/no) [/cyan]")
                while res.lower() not in ["yes","no"]:
                    res = Prompt.ask(f"[cyan]Please enter a valid response (yes/no) [/cyan]")

                if res.lower() == "no":
                    continue

            target_chunks,target_import_deps = processDependencies(
                entry_file,
                template_files,
                chunk,
                chunks,
                chunks_name,
                target_listener,
                express_var_name_second,
                express_var_name_first,
                target_chunks,
                import_deps,
                target_import_deps
            )

    return target_import_deps, target_chunks


