"""
Add
Remove
Replace
"""

"""
Tasks
-----

1) group and process actions by layer                        -- done
2) breakCode output format should be the same as read_file   -- done
3) rework breakcode to handle list of expressions
4) validate if file operation was successful
5) validate if command execution was succesful
"""

"Process Layer by Layer"

from .read_file import read_file
from .break_chunk import breakChunk, getLayerBreakDown, getChunk, getLayerCode

from typing import List, Optional, TypedDict
from pydantic import Field

"""
    actions = [
        {
            "action":"add",
            "chunk":None,
            "code":<New code>
        },
        {
            "action":"remove",
            "chunk":<layer_chunk_name>,
            "code":None
        },
        {
            "action":"replace",
            "chunk":<layer_chunk_name>,
            "code":<New code>
        }
    ]
"""

class SingleUpdateAction(TypedDict):
    action : str = Field(description="action to carry out (add | remove | replace )")
    chunk : Optional[str] = Field(description = "name of chunk to use as anchor for update operation")
    code : Optional[str] = Field(description="New code to write to file")


def addLeadingWhiteSpaces(code,count):
    cleaned = []

    if count == 0:
        return code
    
    lines = code['code'].split("\n")
    for line in lines:
        cleaned.append(" "*count+line)

    cleaned = "\n".join(cleaned)

    return {"name":code['name'],"code":cleaned}

def processLayer(layers,layer_chunks,items,file_type="python",root_operation=False):

    if root_operation or len(layers) == 0: 

        # we are at the final layer
        for item in items:  # TODO : process layer actions once
            action = item['action']

            code = item['code']

            if action == "add":
                if item['chunk'] != None:
                    add_after = getChunk(item['chunk'],layer_chunks)
                    
                    if add_after == None:
                        raise ValueError(f"Chunk with name {item['chunk']} not found in file")
                    
                    position = layer_chunks.index(add_after)

                    layer_chunks.insert(position,{"code":code,"name":"new"}) #insert at specified position
                else:
                    layer_chunks.append({"code":code,"name":"new"}) #add code to ending of file

            elif action == "remove" or action == "replace":

                chunk_to_remove = getChunk(item['chunk'],layer_chunks)

                if chunk_to_remove == None:
                    raise ValueError(f"Chunk with name {item['chunk']} not found in {layer_chunks}")
                position = layer_chunks.index(chunk_to_remove)
                if action == "remove":
                    layer_chunks.pop(position)
                else:
                    layer_chunks[position] = {"code":code,"name":layer_chunks[position]['name']}

            else:
                raise ValueError(f"action {action} not recognised")
            
        return layer_chunks 
    else:

        layers = list(layers)
        current = layers.pop(0)

        chunk = getChunk(current,layer_chunks)

        if chunk == None:
            raise ValueError("Could not find code in file") #could not find layer in chunks
        
        inner_layer,whitespaces = breakChunk(chunk['code'],current,file_type) #TODO Start here

        result = processLayer(layers,inner_layer,items,file_type)

        prev = result
        if isinstance(result,list):
            prev = result[0]
        else:
            result = [result]

        prev = prev['name'].split("_sub_")
        prev = "_sub_".join(prev[:len(prev)-1]) # get previous layer name

        result_with_identation = [addLeadingWhiteSpaces(i,whitespaces)['code'] for i in result]
        
        chunk_index = layer_chunks.index(getChunk(current,layer_chunks))

        result = {"code":"\n".join(result_with_identation),"name":current}

        layer_chunks[chunk_index] = result

        # remove and add
        return layer_chunks
   
def sortAndGroupByLayer(data):
    # Group by identical chunk_layer array
    groups = {}
    for d in data:
        key = tuple(d.get("chunk_layer", []))  # tuples are hashable, lists aren't
        groups.setdefault(key, []).append(d)


    # Sort each group by number of chunk_layer (descending)
    for k in groups:
        # groups[k] = sorted(groups[k], key=lambda d: len(d.get("chunk_layer", [])), reverse=True)
        actions = sorted(groups[k], key=lambda d: len(d.get("chunk_layer", [])), reverse=True)
        groups[k] = {"actions":actions,"root_chunk":actions[0]['root_chunk']}


    # Sort the groups themselves from largest to smallest chunk_layer count
    sorted_groups = dict(sorted(groups.items(), key=lambda item: len(item[0]), reverse=True))

    # print(sorted_groups, "here with\n")

    return sorted_groups


def addChunkLayersBreakdown(layer_data):
    """
    actions = [
        {
            "action":"add",
            "chunk_layer":[],
            "chunk":None,
            "code":<New code>
        },
        {
            "action":"remove",
            "chunk_layer":[],
            "chunk":<layer_chunk_name>,
            "code":None
        },
        {
            "action":"replace",
            "chunk_layer":[],
            "chunk":<layer_chunk_name>,
            "code":<New code>
        }
    ]
    """

    for i in range(0,len(layer_data)):
        current = layer_data[i]
        layers = getLayerBreakDown(current['chunk'])
        current['chunk_layer'] = layers
        current["root_chunk"] = False

        if len(layers) == 1 and current['chunk'] == layers[0]:
            current["root_chunk"] = True

    return layer_data


def updateFile(filename : str,actions : List[SingleUpdateAction] = []) -> str:

    """
    Update File; write, remove or replace code in file

    Args:
        filename (str) : absolute path to file we are updating
        actions (List[SingleUpdateAction]) : a list of update action to perform on file

    Returns:
        Confirmation if update was successful or not
    """

    file_type = "js"

    if filename.endswith(".py"):
        file_type = "python"
   
    actions = addChunkLayersBreakdown(actions)

    chunks = read_file(filename)

    if chunks == None:
        "TODO : create new file in the specified path"
        file_code = ""
        for step in actions:
            # print(step['action'])
            if step['action'] != "add":
                return "Error : This is a new file : you cannot replace or remove code because its new"
            
            if len(file_code) == 0:
                file_code += step['code']
            else:
                file_code += f"\n\n{step['code']}"

    else:
        sorted_data = sortAndGroupByLayer(actions) #sort by layer, max to min

        layer_chunks = chunks

        for layer in sorted_data:

            layer_actions = sorted_data[layer]['actions']
            is_root = sorted_data[layer]['root_chunk']


            # if is_root:
            #     print("Found root chunk ", layer)
                        
            # check for root operations
            try:
                layer_chunks = processLayer(layer,layer_chunks,layer_actions,file_type,is_root)
                # if root_chunk: # is root operation
                #     layer_chunks = processLayer(layer,layer_chunks,layer_actions,True)
                # else:
                #     # current = getChunk(layer[0],chunks)
                #     # update = getChunk(layer[0],layer_chunks)
                #     # # TODO : verify update here
                #     # print("current ",current,"\n\n")
                #     # print("update ",update,"\n\n")
                #     layer_chunks = processLayer(layer,layer_chunks,layer_actions)  
            except ValueError as err:
                return f"Error : {err}"
           

        file_code = "\n\n".join([i['code'] for i in layer_chunks])

    # write update
    with open(filename,"w") as file:
        file.write(file_code)

    return "Update Successful" # If Successful



# if __name__ == "__main__":
#     # print(getLayerBreakDown("chunk_1"))
#     filename = "/home/attah/.sb/environment/express/controllers/contact_controller.js"
#     chunks = read_file(filename)
#     # layers = getLayerCode(getLayerBreakDown("chunk_1_sub_5_sub_3"),chunks,"js")

#     # for item in layers:
#     #     print("name",item['name'])
#     #     print(item['code'])
#     #     print("\n","-"*30)

#     actions = [
#         {
#             "action":"remove",
#             "chunk":"chunk_1_sub_2",
#             "code":"console.log('Lolo')"
#         },
#         # {
#         #     "action":"add",
#         #     "chunk":"chunk_2", # add before chunk
#         #     "code":"# 'step':'I am the Batman',"
#         # },
#         # {
#         #     "action":"add",
#         #     "chunk":"chunk_3_sub_2_sub_2_sub_2", # replace chunk
#         #     "code":"'step':'Jesus Baby',"
#         # },
#         # {
#         #     "action":"add",
#         #     "chunk":"chunk_3_sub_2_sub_2_sub_3", # replace chunk
#         #     "code":"'step':'Jesus Baby',"
#         # },
#         # {
#         #     "action":"add",
#         #     "chunk":None, # replace chunk
#         #     "code":"New code"
#         # },
#     ]

#     res = updateFile(filename,actions)
#     print(res)

