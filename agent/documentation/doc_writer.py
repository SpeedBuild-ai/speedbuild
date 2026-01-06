import asyncio
from pydantic import BaseModel
from typing import List, Optional


class Chunk(BaseModel):
    name: str
    code: str
    dependencies: Optional[List[str]]


BATCH_SIZE = 5
MAX_CONCURRENCY = 8

semaphore = asyncio.Semaphore(MAX_CONCURRENCY)


async def call_llm_batch(chunks: List[Chunk],doc_generator):
    prompt_parts = []

    for c in chunks:
        prompt_parts.append(f"### CHUNK NAME : {c['name']}\nCODE ```{c['code']}```\n")

    prompt = (
        "Document EACH code chunk. Return JSON with fields: id, has_documentation, documentation.\n\n"
        + "\n".join(prompt_parts)
    )

    async with semaphore:
        docs = await doc_generator.generateDocs(prompt,[])

    results = {}
    for obj in docs:
        results[obj.chunk_name] = obj.documentation if obj.has_documentation else None #{

    return results


async def process_chunks_in_batches(sorted_chunks: List[Chunk],doc_generator):
    batches = [
        sorted_chunks[i:i + BATCH_SIZE]
        for i in range(0, len(sorted_chunks), BATCH_SIZE)
    ]

    tasks = [call_llm_batch(b,doc_generator) for b in batches]

    results = await asyncio.gather(*tasks)

    final = {}
    for r in results:
        final.update(r)

    return final