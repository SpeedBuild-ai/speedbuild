import re
import ast
import ast

from ....utils.parsers.python.parser import PythonBlockParser 

from ....utils.django.var_utils import get_assigned_variables, removeDecorator

pattern = r'\b(?:\w+\.)+\w+[,]?\b'


parser = PythonBlockParser()

def get_referenced_variables(block, root=False):
    """Extracts variable names referenced/used within the given block using AST."""
    referenced_vars = set()
    assigned_vars = set()  # Track assignments to exclude them from references
    
    block = removeDecorator(block)  # Assuming you have this function
    
    try:
        tree = ast.parse(block.strip())
        
        # First pass: collect all assigned variables
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assigned_vars.add(target.id)
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    assigned_vars.add(node.target.id)
            elif isinstance(node, ast.FunctionDef):
                assigned_vars.add(node.name)
                # Add function parameters as assigned
                for arg in node.args.args:
                    assigned_vars.add(arg.arg)
            elif isinstance(node, ast.ClassDef):
                assigned_vars.add(node.name)
        
        # Second pass: collect all referenced variables
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                # Only include variables that are being loaded/referenced
                # and are not built-ins or assigned within this block
                var_name = node.id
                if (var_name not in assigned_vars and 
                    var_name not in dir(__builtins__) and
                    not var_name.startswith('__')):
                    referenced_vars.add(var_name)
            
            elif isinstance(node, ast.Attribute):
                # Handle attribute access (e.g., obj.method, module.function)
                if isinstance(node.value, ast.Name):
                    var_name = node.value.id
                    if (var_name not in assigned_vars and 
                        var_name not in dir(__builtins__) and
                        not var_name.startswith('__')):
                        referenced_vars.add(var_name)
            
            elif isinstance(node, ast.Call):
                # Handle function calls
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if (func_name not in assigned_vars and 
                        func_name not in dir(__builtins__) and
                        not func_name.startswith('__')):
                        referenced_vars.add(func_name)
        
        if root and len(referenced_vars) > 0:
            return list(referenced_vars)[0]
            
    except:
        pass  # Silently handle parsing errors like the original
    
    return referenced_vars


def get_all_variables_and_parameters(block):
    """
    Comprehensive function that extracts both assigned and referenced variables,
    including function parameters and their usage.
    """
    all_vars = {
        'assigned': set(),
        'referenced': set(), 
        'parameters': set(),
        'function_calls': set(),
        'attributes': set()
    }
    
    block = removeDecorator(block)
    
    try:
        tree = ast.parse(block.strip())
        
        for node in ast.walk(tree):
            # Assignments
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        all_vars['assigned'].add(target.id)
                        
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    all_vars['assigned'].add(node.target.id)
                    
            # Function definitions and parameters
            elif isinstance(node, ast.FunctionDef):
                all_vars['assigned'].add(node.name)
                for arg in node.args.args:
                    all_vars['parameters'].add(arg.arg)
                    
            elif isinstance(node, ast.ClassDef):
                all_vars['assigned'].add(node.name)
                
            # Variable references
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                var_name = node.id
                if (not var_name.startswith('__') and 
                    var_name not in dir(__builtins__)):
                    all_vars['referenced'].add(var_name)
                    
            # Function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    all_vars['function_calls'].add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        all_vars['referenced'].add(node.func.value.id)
                        
            # Attribute access
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    all_vars['attributes'].add(f"{node.value.id}.{node.attr}")
                    all_vars['referenced'].add(node.value.id)
    
    except:
        pass
    
    return all_vars

def get_refrenced_variables_from_file(feature, blocks_name):
    refrences = get_referenced_variables(feature)

    ref_list = []
    for i in refrences:
        if i in blocks_name:
            ref_list.append({"packagePath":".","imports":i})   
    return ref_list



def reformatLine(line, project_name):
    line = line.split(".")
    feature = line.pop()
    file = line.pop()

    if file == project_name:
        return ["/".join(line) + "/" + file + "/" + feature + ".py", "__all__"]
    else:
        file += ".py"

    return ["/".join(line) + "/" + file, feature]

def getFileDependencies(code,project_name):
    matches = re.findall(pattern, code)
    dependencies = []

    for i in matches:
        dependencies.append(reformatLine(i,project_name))

    return dependencies

def extract_words_from_code(code):
    if code == None:
        return set()
    # Remove strings and comments
    code = re.sub(r'(".*?"|".*?")', '', code)  # Remove strings
    code = re.sub(r'#.*', '', code)  # Remove comments
    
    # Extract words using regex (identifiers, keywords, function names, variable names)
    words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', code)
    
    return set(words)

def strip_decorators(code_chunk):
    lines = code_chunk.splitlines()
    cleaned_lines = []
    
    for line in lines:
        # 1. Strip leading whitespace to check the content
        stripped = line.lstrip()
        
        # 2. Check if the line starts with '@'
        # This ignores decorators but keeps function/class bodies
        if stripped.startswith('@'):
            continue
            
        cleaned_lines.append(line)
        
    return "\n".join(cleaned_lines)

def getBlockDependencies(block, all_blocks):
    """
    Analyzes a code block and identifies all its dependencies from other blocks.
    This function extracts all variables, imports, and references that a given code block
    depends on, including imported packages, locally defined variables, classes, and functions.
    Args:
        block (str): The code block to analyze for dependencies.
        all_blocks (list): A list of all code blocks in the file to search for dependencies.
    Returns:
        list: A list of dictionaries, each containing:
            - "packagePath" (str): The package/module path (e.g., "os", ".", or relative import path).
            - "imports" (str): The name of the imported/referenced item, optionally with alias (e.g., "numpy as np").
    Raises:
        None
    Example:
        >>> blocks = ["import os", "x = 5", "print(x)"]
        >>> getBlockDependencies("print(x)", blocks)
        [{"packagePath": ".", "imports": "x"}]
    """
    
    importLine = []
    block_words = extract_words_from_code(block)

    # Get assigned variables in the current block
    assigned_vars = get_assigned_variables(block)

    # Remove assigned variables from the dependencies list
    filtered_words = [word for word in block_words if word not in assigned_vars]
    
    filtered_chunks = []
    other_chunks = [] # for class and functions

    # Exclude class and function definitions from all_blocks
    for chunk in all_blocks:
        stripped_chunk = chunk.strip()
        stripped_decorator_code = strip_decorators(stripped_chunk).strip()

        if not (stripped_decorator_code.startswith("class ") or stripped_decorator_code.startswith("def ")):
            filtered_chunks.append(chunk)
        else:
            if block != chunk:
                other_chunks.append(chunk)

    all_words = set()

    # Manage imports
    for line in filtered_chunks:
        if line.startswith("import ") or line.startswith("from "):
            if "from " in line:
                package_name = line.split("import")[0].split("from")[1].strip()
            else:
                package_name = line.split("import")[1].strip()
                
            if len(package_name) > 0:
                # if package_name not start with .
                # go to our root folder and try and find the file
                # if package_name.startswith(".") or isFileInRoot(package_name) == True:
                char = extract_words_from_code(line.split("import")[1])
                for word in char:
                    if word in filtered_words:
                        # check import for alias
                        if " as " in line:
                            original_name = line.split(" as ")[0].split(" ")[-1]
                            # print("Found an alias import ",line,"original name ",original_name)
                            word = f"{original_name} as {word}"
                        all_words.add(word)
                        importLine.append({"packagePath":package_name,"imports":word})
        else:
            # variables line declaration
            # print("here with line ", line)
            varNames = get_assigned_variables(line)
            for word in varNames:
                if word in filtered_words:
                    all_words.add(word)
                    
                    importLine.append({"packagePath":".","imports":word})

    # manage class and functions
    for chunk in other_chunks:
        # print("other : ",chunk)
        name = get_assigned_variables(chunk,True)
   
        if isinstance(name,str) and name in filtered_words:
            importLine.append({"packagePath":".","imports":name})

    # check for in file dependencies here
    words = set()
    for chunk in all_blocks:
        var_name = get_assigned_variables(chunk,True)
        if isinstance(var_name,str):
            # print(get_assigned_variables(chunk,True))
            words.add(var_name)

    
    ref = get_refrenced_variables_from_file(block,words)

    # print("here with ",ref)

    importLine.extend(ref)

    # print(importLine)

    return importLine

def get_code_block_names(code,block_name):
    # print(f"code {block_name} ",code, " \n\n\n")
    try:
        tree = ast.parse(code.strip())

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):  # Function names
                return node.name == block_name
            elif isinstance(node, ast.ClassDef):  # Class names
                return node.name == block_name
            elif isinstance(node, ast.Assign):  # Direct assignments (x = 5, x, y = 10, 20)
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id == block_name: return True
    except:
        # pass
        # print(code," error jumbo ",block_name)

        return False

# def getCodeBlockFromFile(blockName, file_dependencies):
#     for chunk in file_dependencies:
#         if get_code_block_names(chunk,blockName):
#             return chunk
#     return None

def getCodeBlockFromFile(blockName, file_dependencies):
    for chunk in file_dependencies:
        if get_assigned_variables(chunk,True)  == blockName:
            return chunk

    return None

def removeDuplicates(code):
    """
    Removes duplicate code chunks from the given list, preserving the original order.

    Args:
        code (list): A list of strings, each representing a code chunk (can be multiline).

    Returns:
        list: A new list containing the unique code chunks from the input, in their original order.
    """
    cleaned_code = []
    for line in code:
        if line not in cleaned_code:
            cleaned_code.append(line)

    return cleaned_code

def get_if_blocks(code):
    tree = ast.parse(code.strip())
    if_blocks = []

    for node in ast.walk(tree):
        if isinstance(node, ast.If):  # Capture if statements
            if_block = {
                "type": "if",
                "condition": ast.unparse(node.test) if hasattr(ast, "unparse") else "<condition>",
                "body": ast.unparse(node.body) if hasattr(ast, "unparse") else "<body>",
            }
            if_blocks.append(if_block)

            # Process the `orelse` part which may contain elif or else blocks
            else_body = []
            for elif_node in node.orelse:
                if isinstance(elif_node, ast.If):  # Elif case
                    elif_block = {
                        "type": "elif",
                        "condition": ast.unparse(elif_node.test) if hasattr(ast, "unparse") else "<condition>",
                        "body": ast.unparse(elif_node.body) if hasattr(ast, "unparse") else "<body>",
                    }
                    if_blocks.append(elif_block)
                else:  # Else block (contains multiple statements)
                    else_body.append(ast.unparse(elif_node) if hasattr(ast, "unparse") else "<body>")

            if else_body:  # Capture the entire else block as a single entity
                else_block = {
                    "type": "else",
                    "body": "\n".join(else_body)
                }
                if_blocks.append(else_block)

    return if_blocks

def getCodeBlockNameAndType(code, returnVal=False):
    # print(code)
    tree = ast.parse(code.strip())

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):  # Direct assignments (x = 5, x, y = 10, 20)
            for target in node.targets:
    
                if isinstance(target, ast.Name):
                    var_name =  target.id
                
                     # Get the assigned value
                    value = node.value
                    var_type = None  # Default type

                    if isinstance(value, ast.Constant):  # Handles literals (Python 3.8+)
                        var_type = type(value.value).__name__
                    elif isinstance(value, ast.List):
                        var_type = "list"
                    elif isinstance(value, ast.Dict):
                        var_type = "dict"
                    elif isinstance(value, ast.Tuple):
                        var_type = "tuple"
                    elif isinstance(value, ast.Set):
                        var_type = "set"
                    elif isinstance(value, ast.Call):  # Function call
                        var_type = "function_call"
                    elif isinstance(value, ast.BinOp):  # Binary operations (e.g., x + y)
                        var_type = "expression"

                    # print("data ", var_name," ",var_type, " ", val_value)
                    if returnVal:
                        return [var_name,var_type,value]
                    
                    return [var_name,var_type]
                
        elif isinstance(node, ast.If):  # Capture if statements
            condition = ast.unparse(node.test) if hasattr(ast, "unparse") else "<condition>"
            # print(condition, " is this")
            return ["if_"+condition,"if_statement"]

    return None

def remove_multiline_comments(code: str) -> str:
    """
    Removes all multi-line comments (triple-quoted strings that are not docstrings) from Python code.
    """
    pattern = re.compile(r'(""".*?"""|\'\'\'.*?\'\'\')', re.DOTALL)
    
    def replacer(match):
        # Keep docstrings in functions and classes
        before = code[:match.start()].strip().split('\n')
        if before and (before[-1].startswith("def ") or before[-1].startswith("class ")):
            return match.group(0)
        return ""
    
    return pattern.sub(replacer, code)

def removeMethodsFromChunk(chunk):
    """
        Remove methods from class definitions
    """
    if not chunk.strip().startswith("class"):
        return chunk
    
    lines = chunk.split("\n")
    classWithoutMethod = [lines.pop(0)]

    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith("def ") or stripped_line.startswith("@"):
            break
        classWithoutMethod.append(line)
    
    return "\n".join(classWithoutMethod)

def arrangeChunks(data,arranged_chunks,processed):
    code_to_name = {}
    sorted_chunks = []

    for chunk in data:
        name = get_assigned_variables(chunk,True)
        # print("name is ",name," with type ",type(name))
        if isinstance(name, str):
            # print("chunk name is ",name)
            code_to_name[name] = chunk

    chunk_order = getArrangeChunksOrder(data,arranged_chunks,processed)
    # print("chunk order is ", chunk_order)

    for i in chunk_order:
        sorted_chunks.append(code_to_name[i])

    return sorted_chunks

def getArrangeChunksOrder(data,arranged_chunks,processed):
    stack = []

    data = [removeMethodsFromChunk(i) for i in data]
    # print(data, "\n\ncleaned\n\n")

    for chunk in data:
        name = get_assigned_variables(chunk,True)
        # chunk_without_method = removeMethodsFromChunk(chunk)
        # print("name of chunk is ", chunk)
        dep = getBlockDependencies(chunk,data)
        dep = [i['imports'] for i in dep if i['packagePath'] == "."]

        if len(dep) == 0:
            arranged_chunks.append(chunk)
            processed.append(name)
        else:
            addToList = True
            for c in dep:
                if c not in processed:
                    addToList = False
                    stack.append(chunk)
                    break

            if addToList:
                arranged_chunks.append(chunk)
                processed.append(name)

    if len(stack) > 0:
        # print(stack)
        # print("\n\nprocessed\n",processed)
        arranged_chunks = getArrangeChunksOrder(stack,arranged_chunks,processed)

    return [name for name in processed if isinstance(name,str)] #arranged_chunks
