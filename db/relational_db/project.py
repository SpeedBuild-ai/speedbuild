from typing import Any, Dict, Optional
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
    
def get_project(id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT 1 FROM project WHERE name = ? LIMIT 1",
            (id,)
        )
        row = cur.fetchone()

        if not row:
            return None
        
        return row
    
def delete_project(project_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM project WHERE id = ?",
            (project_id,)
        )


if __name__ == "__main__":
    init_db()