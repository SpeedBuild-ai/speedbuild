import os
from pathlib import Path

from .js_var_names import get_variable_name_and_type


output_marker = "### PARSER OUTPUT ###"
varIdentifies = ["const ","let ","var "]
special_case = [".",",","else","||","&&"]

def getLineValue(line):
    """
    Split a string at the first '=' and return the two parts.
    Searches the given string for the first occurrence of the '=' character.
    If found, returns a two-element list [left, right] where `left` contains
    the substring up to and including that first '=', and `right` contains
    the remainder of the string after the '='. If no '=' is present, returns
    None.
    Parameters
    ----------
    line : str
        The input string to examine. The function expects a string; passing
        other types may raise a TypeError.
    Returns
    -------
    list[str, str] | None
        A list with two strings [left_including_equals, right_after_equals]
        when '=' is found; otherwise None.
    Examples
    --------
    getLineValue("key=value")  -> ["key=", "value"]
    getLineValue("a=b=c")      -> ["a=", "b=c"] TODO : implement multi = sign
    getLineValue("novalue")    -> None
    """
    if "=" in line:
        pos = line.index("=") + 1
        return [line[:pos],line[pos:]]
    
    return None

class JsTxParser:
    def __init__(self):
        self.opening = [ "[","(","{","/*"]
        self.closing = ["]",")","}","*/"]
        self.cache = None

    def checkIfChunkIsContinuation(self,chunk):
        chunk = chunk.strip()
        for item in special_case:
            if chunk.startswith(item):
                return True
        return False

    def get_and_set_variable_name(self,chunk):
        return get_variable_name_and_type(chunk)
    
    def getFileInfoFromCache(self,filename):
        if self.cache is not None and filename in self.cache.keys():
            return self.cache[filename]
        return None

    def storeFileInfoInCache(self,filename, fileData):
        # TODO : find out; is this optimized
        cache = self.cache if self.cache is not None else {}
        cache[filename] = fileData

        self.cache = cache

    def clearCache(self):
        self.cache = None

    async def parse_code(self,filename, ignore_import=False, ignore_chunk_name=False,raw_code=False):

        # check cache if file have been processed before
        cache_file_data = self.getFileInfoFromCache(filename)

        if cache_file_data is not None:
            return cache_file_data

        stack = []
        chunks = []
        memory = []
        imports = []

        variableToChunkMapping = {}

        if raw_code:
            code = filename
        else:
            with open(filename,"r") as file:
                code = file.read()

        lines = code.split("\n")
        for line in lines:
            is_import = False
            memory.append(line)

            # handle multi line comments
            if line.startswith("/*") and line.endswith("*/"):
                pass # skip edge case where multi line comment are on 1 line. E.g : - /*Hello my Guy We land shjgsgs shgshgs*/ -

            elif line.startswith("/*"):
                # print("multi line comment opening found")
                stack.append("/*")

            elif line.endswith("*/"):
                # print("multi line comment closing found")
                if len(stack) > 0:
                    last = stack[-1]
                    index = self.opening.index(last)

                    if index == self.closing.index("*/"):
                        stack.pop(-1)

                else:
                    raise ValueError("Your code has an error and its not syntactic correct")
                
            else:
                for char in line:
                    if char in self.opening:
                        stack.append(char)
                    elif char in self.closing:
                        if len(stack) > 0:
                            last = stack[-1]
                            index = self.opening.index(last)

                            if index == self.closing.index(char):
                                stack.pop(-1)

                        else:
                            raise ValueError("Your code has an error and its not syntactic correct")

            if len(stack) == 0:
                newCode = "\n".join(memory)
                if len(newCode.strip()) > 0:
                    # TODO check if newCode start with special characters like ||, else, else if ....
                    if (newCode.strip()[0] in self.opening or self.checkIfChunkIsContinuation(newCode)) and len(chunks) > 0:
                        last_chunk = chunks.pop(-1)
                        newCode = f"{last_chunk}\n{newCode}"

                    if not ignore_import and newCode.strip().startswith("import "):
                        imports.append(newCode)
                    else:
                        chunks.append(newCode)

                        if not newCode.startswith("/") and not ignore_chunk_name:

                            if newCode.strip().startswith("exports."):
                                chunk_to_process = "const "+newCode.strip()[8:]
                            else:
                                chunk_to_process = newCode

                            # print(chunk_to_process,"\n\n")
                            try:
                                chunk_info = self.get_and_set_variable_name(chunk_to_process)
                                # print(chunk_info, " - chunk info")
                                if chunk_info is not None:
                                    if isinstance(chunk_info,list):
                                        # print("info ",chunk_info[1])
                                        variableToChunkMapping[chunk_info[1]] = newCode
                                        # print("mapping ", variableToChunkMapping)
                                else:
                                    # print("chunk evaluated to none ",chunk_to_process)
                                    pass
                            except ValueError as e:
                                pass
                                # print(e)

                memory = []

        if len(stack) > 0:
            raise ValueError("Your code has an error and its not syntactic correct")
            
        import_deps = {}
        require_synthax_import = []
        new_chunks = []

        for chunk in chunks:
            require_check = "require(" in chunk

            # convert require to import syntax
            if require_check:
                chunk = convertRequireToImport(chunk)
                imports.append(chunk)
                require_synthax_import.append(chunk)

                # TODO: remove chunk from chunks
                # chunks.remove(chunk)
            else:
                new_chunks.append(chunk)

        chunks = new_chunks

        for chunk in imports:

            if " from " in chunk:
                deps, src = chunk.split(" from ")

                namedImports = []

                if "{" in deps and "}" in deps:
                    namedImports = deps.split("}")[0].split("{")[-1].split(",")


                deps = deps.replace("{","").replace("}",'').replace("import","").strip().split(",")
                src = src.replace("'","").replace('"',"")

                if src.endswith(";"):
                    src = src[:len(src)-1]

                src_deps = []

                if src in import_deps.keys():
                    src_deps = import_deps[src]

                
                for word in deps:
                    if " as " in word:
                        word, alias = word.split(" as ")
                        src_deps.append({"dep":word.strip(),"alias":alias.strip(),"standalone": word not in namedImports, "use-require":chunk in require_synthax_import})
                    
                    elif word.strip() == "*":

                        # Example paths
                        path1 = Path(os.path.dirname(filename))
                        path2 = Path(f"{src}.js")

                        merged = path1 / path2

                        _, chunks, varMappings = self.parse_code(merged,True)
        
                        src_deps[-1]['ext_deps'] = list(varMappings.keys())

                        for ext_dep in list(varMappings.keys()):
                            src_deps.append({"dep":ext_dep.strip(),"alias":None,"standalone":True,"use-require":chunk in require_synthax_import})

                    else:
                        src_deps.append({"dep":word.strip(),"alias":None,"standalone": word not in namedImports, "use-require":chunk in require_synthax_import})

                    import_deps[src] = src_deps
            else:
                pass
        
        returnObject = [imports,chunks,variableToChunkMapping,import_deps]

        # Store file data in cache
        self.storeFileInfoInCache(filename,returnObject)

        return returnObject 

def removeJsIndentifier(line):
    for indentify in varIdentifies:
        if line.startswith(indentify):
            return line.replace(indentify,"").strip()
    
    return None


def convertRequireToImport(line):
    lineData = getLineValue(line)
    if lineData is not None:
        beforeEqualSign, AfterEqualSign = lineData

        # get path
        end = -1
        start = 0

        while AfterEqualSign[start] != "(":
            start += 1

        while AfterEqualSign[end] != ")":
            end -= 1

        path = AfterEqualSign[start+1:end]
        path = path.replace("'","").replace('"',"")

        # get dependencies
        deps = removeJsIndentifier(beforeEqualSign[:-1])

        if " :" in deps:
            deps = deps.replace(" :","as")
        elif ":" in deps:
            deps = deps.replace(":"," as")

        return f'import {deps} from "{path}"'

