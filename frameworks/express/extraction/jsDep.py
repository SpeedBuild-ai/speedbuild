import re
from ....utils.parsers.javascript_typescript.jsParser import getLineValue

varIdentifies = ["const","let","var"]

# TODO : handle single and multi line comment
def removeCommentFromChunk(chunk):
    return chunk

def getWordsInLine(code, removeStrings=True):
    if code == None:
        return set()
    # Remove strings and comments
    if removeStrings:
        code = re.sub(r'(".*?"|".*?")', '', code)  # Remove strings
        
    code = re.sub(r'#.*', '', code)  # Remove comments
    
    # Extract words using regex (identifiers, keywords, function names, variable names)
    words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', code)
    
    return set(words)

def getChunkDependencies(chunk,chunks_name,chunk_name=True,extra_deps=None):

    if chunk_name:
        if chunk not in chunks_name.keys():
            raise ValueError("The code you want to parse is not in the file")
        
        chunk = chunks_name[chunk]

    deps = set(chunks_name)
    
    if extra_deps is not None:
        deps = deps.union(set(extra_deps))

    all_deps = set()
    exclude_deps = set()

    # remove comments from chunks
    chunk = removeCommentFromChunk(chunk)
    
    lines = chunk.split("\n")
    for line in lines:
        line = line.strip()
        line_word = line.split(" ")

        if line_word[0] in varIdentifies:

            line_diff = getLineValue(line)

            if line_diff is not None:
                # print(line_diff)
                beforeEqualSign,afterEqualSign = line_diff

                words_in_line = getWordsInLine(afterEqualSign)
                exclude_word = getWordsInLine(beforeEqualSign)

                chunk_dep = deps.intersection(words_in_line)
                
                exclude_deps= exclude_deps.union(exclude_word)
                # print(chunk_dep)
                all_deps = all_deps.union(chunk_dep)
        else:
            words_in_line = getWordsInLine(line)
            chunk_dep = deps.intersection(words_in_line)
            all_deps = all_deps.union(chunk_dep)


    if len(all_deps) > 0:
        # print(all_deps, " ", exclude_deps, " ", all_deps.difference(exclude_deps))
        return all_deps.difference(exclude_deps)
        
    return []
