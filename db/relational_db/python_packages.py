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

def get_all_python_packages():
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                SELECT * FROM python_package 
                """
            )
            return cur.fetchall()
        
    except sqlite3.IntegrityError as error:
        print(f"Error : {error}")
        return None

def prepopulate_python_packages(data:Dict):
    for pkg in data:
        if get_python_package(pkg) == None:
            create_python_package(**{"name":pkg,"paths":data[pkg]})
        else:
            print(f"Skipping {pkg} already in db")

def db_has_python_packages():
    pkgs = get_all_python_packages()
    if pkgs == None:
        return False
    
    if len(pkgs) > 0:
        return True
    
    return False
