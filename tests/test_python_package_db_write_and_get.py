from db.relational_db.main import init_db
from utils.django.django_app_dependencies import get_django_app_from_packages_parallel

packages = [
    "annotated-types",
    "anyio",
    "asgiref",
    "certifi",
    "charset-normalizer",
    "Django",
    "esprima",
    "h11",
    "httpcore",
    "httpx",
    "idna",
    "jsonpatch", 
    "jsonpointer",
    "langchain",
    "langchain-core",
    "langgraph",
    "langgraph-checkpoint",
    "langgraph-prebuilt",
    "langgraph-sdk",
    "langsmith",
    "markdown-it-py",
    "mdurl",
    "orjson",
    "ormsgpack",
    "packaging",
    "pip",
    "pydantic",
    "pydantic_core",
    "Pygments",
    "PyYAML",
    "requests",
    "requests-toolbelt",
    "rich",
    "sqlparse",
    "tenacity",
    "typing_extensions",
    "typing-inspection",
    "urllib3",
    "uuid_utils",
    "xxhash",
    "zstandard"
]


if __name__ == "__main__":
    init_db()
    get_django_app_from_packages_parallel(packages)