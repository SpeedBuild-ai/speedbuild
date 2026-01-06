import json
import sqlite3
from typing import Any, Dict, List, Optional
from .main import get_connection, init_db


def create_python_package(
    name: str,
    paths: str
) -> int:
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO python_package (name, paths)
                VALUES (?, ?)
                """,
                (name, json.dumps(paths))
            )
            return cur.lastrowid
        
    except sqlite3.IntegrityError as error:
        print(f"Error : {error}")
        return None
    

def get_python_package(name: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT * FROM python_package WHERE name = ?",
            (name,)
        )
        row = cur.fetchone()

        if not row:
            return None

        return {
            **dict(row),
            "paths": json.loads(row["paths"])
        }
    

def delete_python_package(name: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM python_package WHERE name = ?",
            (name,)
        )

def batch_save_packages(packages: Dict) -> None:
    for pkg in packages:
        if get_python_package(pkg) is not None:
            continue

        paths = packages[pkg]
        create_python_package(**{"name":pkg,"paths":paths})

def get_batch_packages(names:List[str]) -> Optional[Dict[str, Any]]:
    result = {}
    for name in names:
        pkg = get_python_package(name)
        if pkg:
            result[name] = pkg['paths']

    return {"packages":result}

if __name__ == "__main__":
    init_db()
    # data = create_python_package("sympy==1.14.0",{"pkg": ["mpmath", "sympy", "__pycache__", "pip"], "version": "1.14.0"})
    data = get_python_package("sympy==1.14.0")