from typing import Any, Dict, Optional

from .features import delete_feature
from .main import get_connection, init_db

    
def create_project(
    *,
    name: str,
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO project (
                name
            )
            VALUES (?)
            """,
            (name,)
        )
        return cur.lastrowid
    
def get_project(id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT * FROM project WHERE id = ? LIMIT 1",
            (id,)
        )
        row = cur.fetchone()

        if not row:
            return None
        
        return row
    
def delete_project(project_id: int) -> None:
    project = get_project(project_id)
    
    if project is not None:
        # get all project features
        print("we dey here")
        with get_connection() as conn:
            curr = conn.execute("SELECT * from feature WHERE project_id = ?",(project_id,))
            features = curr.fetchall()

            for i in features:
                # delete individual feature
                print("deleteing",i['name'])
                delete_feature(i['id'])

        with get_connection() as conn:
            conn.execute(
                "DELETE FROM project WHERE id = ?",
                (project_id,)
            )

def get_all_projects():
    with get_connection() as conn:
        curr = conn.execute("SELECT * from project")
        projects = curr.fetchall()

        return projects


if __name__ == "__main__":
    init_db()
    # d = get_project(7)
    # print(dict(**d))
    # delete_project(4)
    projects = get_all_projects()
    for i in projects:
        print(dict(**i))