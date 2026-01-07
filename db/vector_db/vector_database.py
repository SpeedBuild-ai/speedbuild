import os
import uuid
import json
import chromadb
from speedbuild.utils.paths import get_user_root

root_path = get_user_root()
default_collection = "default_collection"
vector_db_path = os.path.join(root_path,"speedbuild_vectordb")

def get_db_collection(collection_name=None):
    if collection_name is None:
        collection_name = default_collection

    client = chromadb.PersistentClient(path=vector_db_path)
    collection = client.get_or_create_collection(name=collection_name)

    return collection


def saveToVectorDB(doc,meta_data,collection_name=default_collection):

    collection = get_db_collection(collection_name)
    doc_id = str(uuid.uuid4())

    collection.add(
        ids = [doc_id],
        documents = [doc],
        metadatas = [meta_data]
    )

    return doc_id

def removeFeatureEmbedding(project_id : int,feature_id:int,framework:str):
    collection = get_db_collection()

    results = collection.get(
        where={
            "$and": [
                {"framework": framework},
                {"project_id": project_id},
                {"id": feature_id}
            ]
        },
        include=["metadatas"]
    )

    if results["ids"]:
        collection.delete(where={
            "$and": [
                {"framework": framework},
                {"project_id": project_id},
                {"id": feature_id}
            ]
        })


def query_collection(collection_name,query,framework=None,n=5):
    collection = get_db_collection(collection_name)

    if framework:
        # filter collection meta data to match framework here
        response = collection.query(
            query_texts=query,
            n_results=n,
            where={"framework":framework}
        )
    else:
        response = collection.query(query_texts=query,n_results=n)

    context = []

    for i in range(0,len(response['documents'][0]),1):
        doc = response['documents'][0][i]
        meta_data = response['metadatas'][0][i]

        context.append({
            "name":meta_data['name'],
            "feature_id":meta_data['id'],
            "code":doc
        })

    return json.dumps(context)

def peek_collection(collection_name=default_collection):
    collection = get_db_collection(collection_name)

    response = collection.peek()

    print(response)


def getCodeContext(query:str,framework:str):
    """
    Get Extra context on code base

    Args:
        query (str) : question you want to ask
        framework (str) : could be express or django

    Returns:
        code context
    """
    context = query_collection(default_collection,query,framework)
    return context


if __name__ == "__main__":
    # context = getCodeContext("Pay fast payment processing and validation","django")
    print(peek_collection())
    # removeFeatureEmbedding(6,11,"express")