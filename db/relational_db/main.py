import os
import sqlite3
from speedbuild.utils.paths import get_user_root


root_path = get_user_root()

DB_PATH = os.path.join(root_path,"sqlite3.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS project (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS python_package (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                paths TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS feature (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc TEXT,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                code_import TEXT NOT NULL DEFAULT '[]',
                dependencies TEXT NOT NULL DEFAULT '[]',
                root_feature INTEGER NOT NULL DEFAULT 0,
                feature_filename TEXT NOT NULL,
                framework TEXT NOT NULL DEFAULT '',
                vector_db_id TEXT,
                project_id INTEGER NOT NULL,
                FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_feature_project_id
                ON feature(project_id);

            CREATE INDEX IF NOT EXISTS idx_feature_name
                ON feature(name);

            CREATE INDEX IF NOT EXISTS idx_feature_root_feature
                ON feature(root_feature);

            """
        )