# doc_cache.py
import os
import json
import asyncio

class DocCache:
    def __init__(self, cache_path: str):
        self.cache_path = cache_path
        self.lock = asyncio.Lock()
        self.cache = {}
        self.in_flight = {}  # code_hash -> Future

        if os.path.exists(cache_path):
            with open(cache_path, "r") as f:
                self.cache = json.loads(f.read())

    async def get_or_reserve(self, code_hash: str):
        async with self.lock:
            if code_hash in self.cache:
                return self.cache[code_hash], False

            if code_hash in self.in_flight:
                future = self.in_flight[code_hash]
            else:
                future = asyncio.get_running_loop().create_future()
                self.in_flight[code_hash] = future
                return None, True

        # wait outside lock
        return await future, False

    async def set(self, code_hash: str, doc):
        async with self.lock:
            self.cache[code_hash] = doc  # doc CAN be None
            future = self.in_flight.pop(code_hash, None)

            if future and not future.done():
                future.set_result(doc)

    async def fail(self, code_hash: str, exc: Exception):
        async with self.lock:
            future = self.in_flight.pop(code_hash, None)
            if future and not future.done():
                future.set_exception(exc)
                future.add_done_callback(lambda f: f.exception())


    async def flush(self):
        async with self.lock:
            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
            with open(self.cache_path, "w") as f:
                json.dump(self.cache, f, indent=4)

