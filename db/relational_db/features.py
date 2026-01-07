import json

from .main import get_connection, init_db
from typing import Any, Dict, List, Optional

from speedbuild.db.vector_db.vector_database import removeFeatureEmbedding

# add speedbuild project id to features
# we need project db schema

def feature_exist(name: str, filename: str, code: str, project_id : str) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT *
            FROM feature
            WHERE name = ?
              AND feature_filename = ?
              AND code = ?
              AND project_id = ?
            LIMIT 1
            """,
            (name, filename, code, project_id)
        )
        return cur.fetchone() is not None
    
def get_all() -> Dict:
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT *
            FROM feature
            """,
        )

        return cur.fetchall()

def create_feature(
    *,
    name: str,
    code: str,
    feature_filename: str,
    doc: Optional[str] = None,
    code_import: List[str] = None,
    dependencies: List[str] = None,
    root_feature: bool = False,
    framework: str = "",
    vector_db_id: Optional[str] = None,
    project_id : str
) -> int:
    
    # # Verify project exists
    # project_exists = conn.execute(
    #     "SELECT 1 FROM project WHERE id = ?", (project_id,)
    # ).fetchone()
    
    # if not project_exists:
    #     raise ValueError(f"Project with id '{project_id}' does not exist")
    
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO feature (
                doc, code, name, code_import, dependencies,
                root_feature, feature_filename, framework,
                vector_db_id,project_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,?)
            """,
            (
                doc,
                code,
                name,
                json.dumps(code_import or []),
                json.dumps(dependencies or []),
                int(root_feature),
                feature_filename,
                framework,
                vector_db_id,
                project_id
            )
        )
        return cur.lastrowid
    
def get_project_feature_by_name(name: str, project_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT id, name FROM feature WHERE name = ? AND project_id = ? LIMIT 1",
            (name, project_id)
        )
        row = cur.fetchone()

        if not row:
            return None
        
        print("name", name, dict(row))
        return {"name": row['name'], "id": row['id']}


def get_feature(feature_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT * FROM feature WHERE id = ?",
            (feature_id,)
        )
        row = cur.fetchone()

        if not row:
            return None
        
        deps = json.loads(row['dependencies'])
        dependencies = []

        if isinstance(deps,str):
            deps = list(set(deps.split(",")))

        for i in deps:
            res = get_project_feature_by_name(i,row['project_id'])
            if res:
                dependencies.append(res)

        return {
            **dict(row),
            "code_import": json.loads(row["code_import"]),
            "dependencies": dependencies,
            "root_feature": bool(row["root_feature"]),
        }


def update_feature(
    feature_id: int,
    **updates
) -> None:
    if not updates:
        return

    allowed = {
        "doc", "code", "name", "code_import", "dependencies",
        "root_feature", "feature_filename", "framework",
        "vector_db_id"
    }

    fields = []
    values = []

    for key, value in updates.items():
        if key not in allowed:
            continue

        if key in {"code_import", "dependencies"}:
            value = json.dumps(value)
        elif key == "root_feature":
            value = int(value)

        fields.append(f"{key} = ?")
        values.append(value)

    if not fields:
        return

    values.append(feature_id)

    with get_connection() as conn:
        conn.execute(
            f"UPDATE feature SET {', '.join(fields)} WHERE id = ?",
            values
        )

def delete_feature(feature_id: int) -> None:
    data = get_feature(feature_id)

    if data is not None:
        project_id = data['project_id']
        framework = data['framework']

        with get_connection() as conn:
            conn.execute(
                "DELETE FROM feature WHERE id = ?",
                (feature_id,)
            )
        
        # remove embedding from vector database
        removeFeatureEmbedding(project_id,feature_id,framework)


if __name__ == "__main__":
    init_db()
    # d = get_all()
    # for i in d:
    #     print(dict(**i),"\n\n")
    
    data = get_feature(186)
    print(data)