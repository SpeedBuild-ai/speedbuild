import ast

def removeDecorator(code):
    if code == None:
        return ""
    blocks = code.split("\n")
    index = None

    for i in range(len(blocks)):
        if blocks[i].startswith("@"):
            index = i
        else:
            break
    
    if index != None:
        code_without_decorator = blocks[index:]
        return "\n".join(code_without_decorator).strip()
    
    return "\n".join(blocks).strip()


def get_assigned_variables(block,root=False):
    """
    Extracts variable names assigned within the given block of Python code using the Abstract Syntax Tree (AST).
    Args:
        block (str): The block of Python code to analyze.
        root (bool, optional): If True, returns only the first assigned variable found. Defaults to False.
    Returns:
        set or str: A set of assigned variable names if root is False, or a single variable name (str) if root is True.
    Notes:
        - Handles direct assignments, type-annotated assignments, function and class definitions.
        - Ignores decorators by removing them before parsing.
        - Returns an empty set if parsing fails or no assignments are found.
    """
    """Extracts variable names assigned within the given block using AST."""
    assigned_vars = set()
    
    block = removeDecorator(block)
    # print("hee  ", block, "\n\n")
    try:
        tree = ast.parse(block.strip())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):  # Direct assignments (x = 5, x, y = 10, 20)
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assigned_vars.add(target.id)
            if isinstance(node, ast.AnnAssign):  # Type-annotated assignments (x: int = 5)
                if isinstance(node.target, ast.Name):
                    assigned_vars.add(node.target.id)
            elif isinstance(node, ast.FunctionDef):  # Function parameters
                assigned_vars.add(node.name)
                # for arg in node.args.args:
                #     assigned_vars.add(arg.arg)
            elif isinstance(node, ast.ClassDef):  # Exclude class names from assigned vars
                assigned_vars.add(node.name)

            if root and len(assigned_vars) > 0:
                return list(assigned_vars)[0]
    except:
        pass
        # print("error for ",block)

    return assigned_vars