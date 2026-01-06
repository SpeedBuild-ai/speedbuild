import asyncio
from .read_file import read_file
from ...utils.parsers.javascript_typescript.jsParser import JsTxParser
from ...utils.parsers.python.parser import PythonBlockParser, indentCode


def unindentCode(code):
    """
    Split and partially unindent a block of code into separate "blocks" based on top-level lines.
    This function processes a multiline string `code` and returns a list of text blocks. Each returned
    block is a contiguous group of input lines (joined with newline characters) accumulated until a
    top-level (no-leading-space) line is encountered, at which point the current accumulated block is
    closed and a new block starts. Blank lines in the input are preserved as single newline entries
    within blocks.
    Behavior details:
    - Input is split by newline characters into individual lines.
    - Purely blank lines (lines for which line.strip() == "") are preserved as a single newline and
        appended to the current block (or used to separate blocks).
    - For lines processed before any top-level (indent_count == 0) line has been seen:
            - Lines with an indentation less than 4 spaces have their surrounding whitespace stripped
                (equivalent to line.strip()).
            - Lines with an indentation of 4 or more spaces have the first four spaces removed (only one
                indentation level is removed).
        This "pre-top-level" unindent behavior stops once a top-level line is seen.
    - When a top-level line (no leading spaces) is encountered:
            - If any lines have been accumulated since the last block boundary, that accumulated chunk is
                finalized and appended to the result list.
            - A flag is set so subsequent lines are not unindented by the special rules above.
    - After processing all lines, any remaining accumulated lines form the final block appended to the
        result.
    Parameters:
    - code (str): Multiline string containing the code to split and partially unindent.
    Returns:
    - List[str]: A list of string blocks. Each element is a block constructed by joining the cleaned
        lines for that block with newline characters.
    Notes and caveats:
    - The function treats indentation as spaces only. Tab characters are not specially handled and may
        produce unexpected results.
    - The function removes at most four leading spaces from lines in the initial (pre-top-level)
        region; it does not normalize arbitrary indentation levels beyond that.
    - Blank lines are represented as "\n" within blocks; consecutive blank lines will be preserved as
        separate entries in the accumulated text for that block.
    - The implementation assumes non-empty lines that contain only spaces are handled by the early
        blank-line check (so they are not iterated character-by-character).
    Example:
    >>> code = "    def foo():\\n        pass\\n\\nclass Bar:\\n    pass"
    >>> unindentCode(code)
    ["def foo():\\n    pass\\n\\n", "class Bar:\\n    pass"]
    """

    blocks = []
    cleaned = []
    has_sub_chunk = False
    lines = code.split("\n")

    for line in lines:

        if len(line.strip()) == 0:
            cleaned.append("\n")
            continue

        indent_count = 0
        while line[indent_count] == " ":
            indent_count += 1

        if indent_count == 0:
            if len(cleaned) > 0:
                blocks.append("\n".join(cleaned))
                cleaned = []
                has_sub_chunk = True

        elif indent_count < 4:
            if not has_sub_chunk:
                line = line.strip()
        else:
            if not has_sub_chunk:
                _,line = line.split("    ",1)
        
        cleaned.append(line)

    if len(cleaned) > 0:
        blocks.append("\n".join(cleaned))

    return blocks


# Source of my problem
def processJsChunk(code):
    lines = code.split("\n")

    if len(lines) < 2:
        return code
    
    first_line = lines[0]
    last_line = lines[-1]

    code = lines[1:len(lines)-1]

    # whitespace = 0
    # while code[0][whitespace] == " ":
    #     whitespace += 1

    # if whitespace > 0:
    #     for i in range(0,len(code)):
    #         line = code[i]
    #         # print("line info",line.split(" "*whitespace,1))
    #         chunks = line.split(" "*whitespace,1)
    #         if len(chunks)  > 1:
    #             code[i] = chunks[1]

    code = "\n".join(code)

    _,chunks,_,_ = asyncio.run(JsTxParser().parse_code(code,False,False,True))

    chunks.insert(0,first_line)
    chunks.append(last_line)

    return chunks

def processChunk(code):
    """
    Breaks down Python code into logical chunks while preserving data structure definitions.
    This function splits code into chunks based on logical breaks and handles special cases
    for data structures (lists, dictionaries, tuples). It maintains proper indentation and
    structure of the original code.
    Args:
        code (str): A string containing Python code to be broken into chunks.
    Returns:
        list or str: If the code can be broken down, returns a list of code chunks.
                    If the code is a single line, returns the original code string.
    Examples:
        >>> code = "def example():\\n    x = [1,\\n    2,\\n    3]"
        >>> breakChunk(code)
        ['def example():', '    x = [', '    1,', '    2,', '    3', ']']
        >>> code = "single_line = 42"
        >>> breakChunk(code)
        'single_line = 42'
    """

    if len(code.split("\n")) < 2:
        return code
    
    first_line, code = code.split("\n",1)

    chunk_symbol = None
    is_data_structure = False
    data_structure_closing = ["]","}",")"]
    data_structure_starting = ["[","{","("]

    possible_opening = set(first_line).intersection(set(data_structure_starting))
    chunk_start = first_line.split(" ",1)[0]

    index = None
    
    if chunk_start not in ["def","class"] and len(list(possible_opening)) > 0:
        for char in possible_opening:
            if index == None:
                index = first_line.index(char)
                continue
            pos = first_line.index(char)
            if pos < index:
                index = pos
        
        chunk_symbol = first_line[index]
        code = f"{first_line[index+1:]}{code}"

        first_line = first_line[:index + 1]
        is_data_structure = True

    chunks = unindentCode(code)

    if len(chunks) > 1 and not is_data_structure:
        chunks[0] = first_line + "\n" + indentCode(chunks[0])
        return chunks
    
    splits = PythonBlockParser().parse_code(chunks[0])
    chunks = []
    for chunk in splits:
        chunks.append(indentCode(chunk))

    chunks.insert(0,first_line)

    if is_data_structure:
        close_symbol = data_structure_closing[data_structure_starting.index(chunk_symbol)]
        
        if chunks[-1].endswith(","):
            chunks[-1] = chunks[-1][:len(chunks[-1])-1]

        if chunks[-1].endswith(close_symbol):
            chunks[-1] = chunks[-1][:len(chunks[-1])-1]

        chunks.append(close_symbol)
    
    return chunks

def removeLeadingSpaces(code):
    count = 0
    cleaned = []
    while code[count] == " ":
        count += 1

    if count > 0:
        lines = code.split("\n")
        for line in lines:
            cleaned.append(line[count:])
        
        code = "\n".join(cleaned)

    return code,count

def addLeadingWhiteSpaces(code,count):
    if count == 0:
        return code

    return {"name":code['name'],"code":" "*count + code['code']}

def breakChunk(code,name,code_type="python"):

    if "\t" in code:
        code = code.replace("\t"," "*4)

    # TODO : make dynamic, add leading spaces in some cases
    endWithComa = False

    if code.endswith(","):
        endWithComa = True
        code = code[:len(code)-1]

    formatted = []
    code, whiteSpaceCount = removeLeadingSpaces(code)

    if code_type == "python":
        result = processChunk(code)

        if endWithComa and len(result) > 0:
            result[-1] = result[-1] + ","

    else:
        result = processJsChunk(code)

    if isinstance(result,str):
        formatted.append({
            "name":f"{name}",
            "code":result
        })

    else:
        for i in result:
            formatted.append({
                "name":f"{name}_sub_{len(formatted)+1}",
                "code":i 
            })

    return formatted,whiteSpaceCount


def getLayerBreakDown(name):
    if name == None:
        return []
    
    names = name.split("_sub_")
    layers = [names[0]]

    for i in range(1,len(names)-1):
        prev = layers[i-1]
        layers.append(f"{prev}_sub_{names[i]}")
    
    return layers
    
def getChunk(name,chunks):
    for chunk in chunks:
        if chunk['name'] == name:
            return chunk
    return None
    
def getLayerCode(layers,layer_chunks,file_type):

    # print(layers)

    while len(layers) > 0:
        layer = layers.pop(0)
        chunk = getChunk(layer,layer_chunks)
        layer_chunks,_ = breakChunk(chunk['code'],layer,file_type)

    return layer_chunks


def break_chunk(file_name: str, chunk_name : str):
    """
    Break code chunks into sub chunks

    Args:
        file_name (str) : absolute path of the file holding the chunk
        chunk_name (str) : name of chunk we want to break into sub chunks

    Returns:
        Successful : a list os sub chunks
        Failure : Error message. 
    """

    file_type = "js"
    if file_name.endswith(".py"):
        file_type = "python"
    
    file_content = read_file(file_name)
    layers = getLayerBreakDown(chunk_name)

    if file_content is None:
        return f"Could not read file {file_name}, because it does not exist"
    
    chunks = getLayerCode(layers,file_content,file_type)

    if chunks is not None:
        return chunks
    
    return f"Could find chunk with name {chunk_name} in file"


# if __name__ == "__main__":
#     code = "urlpatterns = [\n\tpath('admin/', admin.site.urls),\n\tpath('shop/',include('shop.urls')),\n]"
#     print(code)
#     chunks = breakChunk(code,"testoro")#break_chunk('/home/attah/.sb/environment/express/controllers/contact_controller.js',"chunk_1","js")
#     print(chunks)

    # for chunk in chunks[0]:
    #     print(chunk,"\n","#"*20)
# if __name__ == "__main__":
#     chunks = break_chunk('/home/attah/.sb/environment/express/controllers/contact_controller.js',"chunk_1","js")
#     print(chunks)


# if __name__ == "__main__":
#     code = """
#         {
#             "step": "Basic Info",
#             "completed": True,
#         },
#         {
#             "step": "Health Goals",
#             "completed": False,
#         },
#         {
#             "step": "LifeStyle",
#             "completed": False,
#         },
#         {
#             "step": "Medical History",
#             "completed": False,
#         },
#         {
#             "step": "Digestive History",
#             "completed": False,
#         },
#         {
#             "step": "Diet History",
#             "completed": False,
#         },
#         {
#             "step": "Reproductive Health",
#             "completed": False,
#         },
#         {
#             "step": "Emergency Contact",
#             "completed": False,
#         },
#     """.strip()

#     result = breakChunk(code,"hello")
#     if isinstance(result,str):
#         print(result)
#     else:
#         for i in result:
#             print(i,"\n","-"*30)