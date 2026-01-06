import json
import hashlib
import os

from .doc_cache_manager import DocCache
from .doc_writer import process_chunks_in_batches
from .documentation import DocumentationGenerator


PROMPT_VERSION = "v1"  # bump this if you change prompting

# file_path = "/home/attah/Documents/jannis/api/jannis_api/output/sb_output_markConsultationAsPaid/feature.json"
def hash_code(code: str) -> str:
    h = hashlib.sha256()
    h.update((code + PROMPT_VERSION).encode("utf-8"))
    return h.hexdigest()

def saveDocsToFile(feature_path,docs):
    with open(feature_path,"r") as file:
        data = json.loads(file.read())
    
    for i in docs:
        if docs[i]:
            file, feature_name = i.split(":::")
            data[file][feature_name]['doc'] = docs[i]

    with open(feature_path,"w") as w_file:
        json.dump(data,w_file,indent=4)


# def saveDocsToFile(feature_path, docs):
#     with open(feature_path, "r") as file:
#         data = json.loads(file.read())

#     for chunk_id, doc in docs.items():
#         if not doc:
#             continue

#         file_name, feature_name = chunk_id.split(":::")
#         code = data[file_name][feature_name]["code"]

#         data[file_name][feature_name]["doc_cache"] = {
#             "hash": hash_code(code),
#             "doc": doc
#         }

#     with open(feature_path, "w") as w_file:
#         json.dump(data, w_file, indent=4)



def getCacheDoc():
    project_root = os.path.abspath(".")
    cache_path = os.path.join(project_root,".sb","doc_cache.json")

    if not os.path.exists(cache_path):
        return {}
    
    with open(cache_path,"r") as file:
        return json.loads(file.read())
    
def addToCacheDoc(data):
    project_root = os.path.abspath(".")
    cache_path = os.path.join(project_root,".sb","doc_cache.json")
    dir_name = os.path.dirname(cache_path)

    cache_data = {}

    if os.path.exists(cache_path):
        with open(cache_path,"r") as f:
            cache_data = json.loads(f.read())
    else:
        os.makedirs(dir_name,exist_ok=True)

    new_cache_data = {**cache_data,**data}

    with open(cache_path,"w") as file:
        json.dump(new_cache_data,file,indent=4)


# async def generateFeatureDocs(feature_file_path):
#     with open(feature_file_path,"r") as file:
#         data = json.loads(file.read())
#         merged_code = []

#         for i in data:
#             features = data[i]
#             for feature in features:
#                 if "code" in features[feature].keys():
#                     merged_code.append({
#                         "code" : features[feature]['code'],
#                         "name":f"{i}:::{feature}",
#                         "file":i
#                     })
                    
#     doc_generator = DocumentationGenerator()
#     result = await process_chunks_in_batches(merged_code,doc_generator)

#     saveDocsToFile(feature_file_path,result)

#     print("Documentation has been added")

# async def generateFeatureDocs(feature_file_path,cache_manager=None):

#     with open(feature_file_path, "r") as file:
#         data = json.loads(file.read())

#     merged_code = []
#     cached_docs = {}
#     sb_doc_cache = getCacheDoc()
#     new_docs_hash_mapping = {}

#     for file_name, features in data.items():
#         for feature_name, feature_data in features.items():
#             if "code" not in feature_data:
#                 continue

#             code = feature_data["code"]
#             code_hash = hash_code(code)

#             if code_hash in sb_doc_cache:
#                 doc = sb_doc_cache.get(code_hash)
#                 # cache hit
#                 cached_docs[f"{file_name}:::{feature_name}"] = doc
#                 continue

#             # cache miss → send to LLM
#             merged_code.append({
#                 "code": code,
#                 "name": f"{file_name}:::{feature_name}",
#                 "file": file_name,
#             })

#             new_docs_hash_mapping[f"{file_name}:::{feature_name}"] = code_hash

#     doc_generator = DocumentationGenerator()

#     new_docs = {}
#     cache_update = {}

#     if merged_code:
#         new_docs = await process_chunks_in_batches(merged_code, doc_generator)
#         for i in new_docs:
#             cache_update[new_docs_hash_mapping[i]] = new_docs[i]

#     # merge cached + new
#     final_docs = {**cached_docs, **new_docs}

#     saveDocsToFile(feature_file_path, final_docs)

#     addToCacheDoc(cache_update)

#     print(
#         f"Docs reused: {len(cached_docs)}, generated: {len(new_docs)}"
#     )


async def generateFeatureDocs(feature_file_path, doc_cache: DocCache = None):

    single_run = False

    if doc_cache is None:
        project_root = os.path.abspath(".")
        cache_path = os.path.join(project_root, ".sb", "doc_cache.json")

        doc_cache = DocCache(cache_path)
        single_run = True

    with open(feature_file_path, "r") as file:
        data = json.loads(file.read())

    merged_code = []
    chunk_hash_map = {}     # chunk_id -> code_hash
    final_docs = {}

    # ---------- PHASE 1: cache lookup / reservation ----------
    for file_name, features in data.items():
        for feature_name, feature_data in features.items():
            if "code" not in feature_data or (feature_name == "feature_settings" and file_name == "settings.py"):
                continue

            code = feature_data["code"]
            code_hash = hash_code(code)
            chunk_id = f"{file_name}:::{feature_name}"

            doc, should_generate = await doc_cache.get_or_reserve(code_hash)

            if doc is not None:
                final_docs[chunk_id] = doc
                continue

            if should_generate:
                merged_code.append({
                    "code": code,
                    "name": chunk_id,
                    "file": file_name,
                })
                chunk_hash_map[chunk_id] = code_hash

    # ---------- PHASE 2: generate missing docs ----------
    # if merged_code:
    #     doc_generator = DocumentationGenerator()
    #     new_docs = await process_chunks_in_batches(
    #         merged_code, doc_generator
    #     )

    #     for chunk_id, doc in new_docs.items():
    #         if not doc:
    #             continue

    #         code_hash = chunk_hash_map[chunk_id]
    #         final_docs[chunk_id] = doc
    #         await doc_cache.set(code_hash, doc)

    # if merged_code:
    #     doc_generator = DocumentationGenerator()
    #     try:
    #         new_docs = await process_chunks_in_batches(
    #             merged_code, doc_generator
    #         )

    #         for chunk_id, doc in new_docs.items():
    #             if not doc:
    #                 continue

    #             code_hash = chunk_hash_map[chunk_id]
    #             final_docs[chunk_id] = doc
    #             await doc_cache.set(code_hash, doc)

    #     except Exception as e:
    #         # fail all reserved hashes
    #         for code_hash in chunk_hash_map.values():
    #             await doc_cache.fail(code_hash, e)
    #         raise

    if merged_code:
        doc_generator = DocumentationGenerator()
        try:
            new_docs = await process_chunks_in_batches(merged_code, doc_generator)

            for chunk_id, doc in new_docs.items():
                code_hash = chunk_hash_map.get(chunk_id)
                if code_hash is None:
                    print(f"Chunk {chunk_id} missing in hash map, skipping.")
                    continue

                final_docs[chunk_id] = doc
                await doc_cache.set(code_hash, doc)  # always set, even if doc is None

        except Exception as e:
            for code_hash in chunk_hash_map.values():
                await doc_cache.fail(code_hash, e)
            # raise


    # ---------- PHASE 3: persist results ----------
    saveDocsToFile(feature_file_path, final_docs)

    print(
        f"Docs reused: {len(final_docs) - len(merged_code)}, "
        f"generated: {len(merged_code)}"
    )

    if single_run:
        await doc_cache.flush()

