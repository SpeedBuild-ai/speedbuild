import esprima

# Define visitor functions
def visit_node(node, parent=None):
    if node is None:
        return
        
    node_type = node.type
    

    # Handle export declarations
    if node_type == 'ExportNamedDeclaration' or node_type == 'ExportDefaultDeclaration':
        # The actual declaration is nested inside the export
        if hasattr(node, 'declaration') and node.declaration:
            return visit_node(node.declaration, node)
        return None

    if node_type == 'ClassDeclaration':
        class_name = node.id.name if hasattr(node, 'id') and node.id else 'anonymous'
        return ["class", class_name]
    
    elif node_type == 'FunctionDeclaration':
        func_name = node.id.name if hasattr(node, 'id') and node.id else 'anonymous'
        return ["function", func_name]

    elif node_type == 'VariableDeclaration':
        declarations = node.declarations
        if declarations:
            declaration = declarations[0]
            var_name = declaration.id.name if hasattr(declaration, 'id') and declaration.id else 'unknown'
            init_node = declaration.init

            init_type = init_node.type if init_node else ''
            
            return [init_type, var_name]
        
    elif node_type == 'IfStatement':
        return "ifStatement", "ifStatement"
    
    return None

def removeDefaultKeywordFromChunk(chunk):
    """
    Replace the 'export default' keyword with 'const' so a parser can 
    successfully process and extract variable name.
    
    Args:
        chunk (str): code to process

    Returns:
        str: processed chunk

    """

    chunk_stripped = chunk.strip().rstrip(';')

    if not chunk_stripped.startswith("export default "):
        return chunk
    
    # Remove "export default " prefix and add "const " 
    rest = chunk_stripped[len("export default "):]

    return f"const {rest}"


def get_variable_name_and_type(chunk):    
    # Parse the JavaScript code

    if chunk.strip().startswith("/") or "=" not in chunk:
        return None 
    
    if chunk.strip().startswith("export default "):
        chunk = removeDefaultKeywordFromChunk(chunk)
    
    try:
        # Use parseModule for ES6 module syntax (export/import)
        ast = esprima.parseModule(chunk)
        info = visit_node(ast.body[0])
        return info
    except esprima.error_handler.Error as e:
        raise ValueError(f"Parse error: {e} could not parse code : {chunk}")
        # return None
    except IndexError:
        raise ValueError("error processing chunk : ",chunk)