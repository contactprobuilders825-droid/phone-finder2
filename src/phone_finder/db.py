from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import Role, User


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    role TEXT NOT NULL CHECK (role IN ('utilisateur', 'admin', 'super_admin'))
);
"""


def connect(db_path: str = "phone_finder.db") -> sqlite3.Connection:
    path = Path(db_path)
    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def upsert_user(conn: sqlite3.Connection, user: User) -> None:
    conn.execute(
        """
        INSERT INTO users (username, role)
        VALUES (?, ?)
        ON CONFLICT(username) DO UPDATE SET role = excluded.role
        """,
        (user.username, user.role.value),
    )
    conn.commit()


def get_user(conn: sqlite3.Connection, username: str) -> User | None:
    row = conn.execute(
        "SELECT username, role FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if row is None:
        return None
    return User(username=row["username"], role=Role(row["role"]))


def list_users(conn: sqlite3.Connection) -> list[User]:
    rows = conn.execute("SELECT username, role FROM users ORDER BY username").fetchall()
    return [User(username=row["username"], role=Role(row["role"])) for row in rows]


def bootstrap_default_users(conn: sqlite3.Connection) -> None:
    for user in (
        User(username="prof", role=Role.USER),
        User(username="direction", role=Role.ADMIN),
        User(username="owner", role=Role.SUPER_ADMIN),
    ):
        upsert_user(conn, user)
