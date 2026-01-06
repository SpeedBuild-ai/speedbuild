import os
import json
import asyncio
import hashlib
from typing import List

from speedbuild.utils.paths import getProjectRootPath
from speedbuild.utils.cli.cli_output import StatusManager
from speedbuild.utils.cli.cli_select import displaySelector

# from speedbuild.utils.config.agent_config import setSpeedbuildConfig
from speedbuild.agent.documentation.documentation import DocumentationGenerator

root_path = getProjectRootPath()

BATCH_SIZE = 3
PROMPT_VERSION = "v1"
CACHE_PATH = os.path.join(root_path,"cache_docs.json")

file_semaphor = asyncio.Semaphore(2)

retrieved_from_cache = {}

def hash_code(code: str) -> str:
    h = hashlib.sha256()
    h.update((code + PROMPT_VERSION).encode("utf-8"))
    return h.hexdigest()

def flatten_feature_file(fdata, feature_data,cache_data={}):
    global retrieved_from_cache

    flatten_features = []

    for filename in fdata:
        for codename in fdata[filename]:
            data = fdata[filename][codename]
            code_hash = hash_code(data['code'])
            feature_tag = f"{filename}:::{codename}"
            data['name'] = feature_tag
            data['hash'] = code_hash

            if code_hash not in cache_data:
                if data not in feature_data: #check if code doc is already in cache
                    flatten_features.append(data)
            else:
                # Code in cache_data
                cache_entry = cache_data.get(code_hash,"")

                retrieved_from_cache[feature_tag] = {
                    "documentation":cache_entry,
                    "hash":code_hash
                }

    return flatten_features

async def call_llm_batch(batch,doc_generator,statusManager):
    # Todo : Implement rate limit and TPM (Token per Minute) and Jittering and Pausing
    prompt_parts = []
    chunk_hash_mapping = {}

    for c in batch:
        prompt_parts.append(f"### CHUNK NAME : {c['name']}\nCODE ```{c['code']}```\n")
        chunk_hash_mapping[c['name']] = c['hash']

    prompt = (
        "Document EACH code chunk. Return JSON with fields: id, has_documentation, documentation.\n\n"
        + "\n".join(prompt_parts)
    )

    async with file_semaphor:
        docs = await doc_generator.generateDocs(prompt)

    results = {}
    index = 0

    for obj in docs:

        try:
            doc_hash = chunk_hash_mapping[obj.chunk_name]
        except KeyError:
            current = batch[index]['name']
            doc_hash = chunk_hash_mapping[current]

        results[obj.chunk_name] = {
            "documentation":obj.documentation if obj.has_documentation else "",
            "hash":doc_hash
        }

        index += 1
    
    statusManager.update_progress()

    return results

async def process_batches(batches,framework):
    doc_generator = DocumentationGenerator()

    statusManager = StatusManager(show_percentage=True,max_value=len(batches),step=1)
    statusManager.start_status("Generating Documentation")
    
    tasks = [call_llm_batch(b,doc_generator,statusManager) for b in batches]
    results = await asyncio.gather(*tasks)

    statusManager.stop_status("Documentation Generated.")

    final = {}
    for r in results:
        if r is not None:
            final.update(r)

    return final

def get_features_code(filename,all_data,framework,doc_cache):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Could not find file {filename}")
    
    with open(filename,"r") as f:
        try:
            file_data = json.loads(f.read())
            
            if framework == "django":
                del file_data['settings.py']
        
            return flatten_feature_file(file_data,all_data,doc_cache)

        except json.JSONDecodeError as error:
            print(f"JSON Decode Error : {error}")
            return None
        
def getDocCache():
    if not os.path.exists(CACHE_PATH):
        return {}
    
    with open(CACHE_PATH,"r") as f:
        return json.loads(f.read())
    
def saveDocCache(cache_data):
    with open(CACHE_PATH,"w") as f:
        json.dump(cache_data,f,indent=4)
        
async def process_feature_file(feature_files : List[str], framework : str):

    # Ask if to generate docs
    choice = displaySelector("Would you like to generate doc for extracted code?",["yes", "no"])

    if choice != "yes":
        return

    flattened_data = []
    doc_cache = getDocCache()

    for filename in feature_files:
        data = get_features_code(filename,flattened_data,framework,doc_cache)

        if data is not None:
            flattened_data.extend(data)

    batches = [
        flattened_data[i:i + BATCH_SIZE]
        for i in range(0, len(flattened_data), BATCH_SIZE)
    ]

    result = await process_batches(batches, framework)

    result = {**retrieved_from_cache,**result} # merge both new docs and cache retrieved docs

    if result:
        # TODO : update cache to hold newly generated docs

        for i in result:
            hash = result[i]['hash']
            doc = result[i]['documentation']

            if hash not in doc_cache:
                doc_cache[hash] = doc

        saveDocCache(doc_cache)

        # TODO : write docs to feature json files
        for filename in feature_files:
            if os.path.exists(filename):

                # read file
                with open(filename,"r") as f:
                    data = json.loads(f.read())
                    for file in data:
                        for code in data[file]:
                            tag = f"{file}:::{code}"
                            if tag in result and result[tag]['documentation']:
                                data[file][code]['doc'] = result[tag]['documentation']

                # write file
                with open(filename,"w") as w_file:
                    json.dump(data,w_file,indent=4)



# if __name__ == "__main__":
#     setSpeedbuildConfig()
#     test_file = "/home/attah/.sb_zip/ManageSupplements.json"
#     asyncio.run(process_feature_file([test_file],"django"))