from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import Role, Tier, User


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    role TEXT NOT NULL CHECK (role IN ('utilisateur', 'admin', 'super_admin')),
    tier TEXT NOT NULL DEFAULT 'free' CHECK (tier IN ('free', 'premium')),
    subscription_id TEXT,
    device_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_payment_date TIMESTAMP
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
        INSERT INTO users (username, role, tier, subscription_id, device_count)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(username) DO UPDATE SET 
            role = excluded.role,
            tier = excluded.tier,
            subscription_id = excluded.subscription_id,
            device_count = excluded.device_count
        """,
        (
            user.username,
            user.role.value,
            user.tier.value,
            user.subscription_id,
            user.device_count,
        ),
    )
    conn.commit()


def get_user(conn: sqlite3.Connection, username: str) -> User | None:
    row = conn.execute(
        "SELECT username, role, tier, subscription_id, device_count FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if row is None:
        return None
    return User(
        username=row["username"],
        role=Role(row["role"]),
        tier=Tier(row["tier"]),
        subscription_id=row["subscription_id"],
        device_count=row["device_count"],
    )


def list_users(conn: sqlite3.Connection) -> list[User]:
    rows = conn.execute(
        "SELECT username, role, tier, subscription_id, device_count FROM users ORDER BY username"
    ).fetchall()
    return [
        User(
            username=row["username"],
            role=Role(row["role"]),
            tier=Tier(row["tier"]),
            subscription_id=row["subscription_id"],
            device_count=row["device_count"],
        )
        for row in rows
    ]


def bootstrap_default_users(conn: sqlite3.Connection) -> None:
    for user in (
        User(username="prof", role=Role.USER, tier=Tier.FREE, device_count=0),
        User(username="direction", role=Role.ADMIN, tier=Tier.PREMIUM, device_count=999),
        User(username="owner", role=Role.SUPER_ADMIN, tier=Tier.PREMIUM, device_count=999),
    ):
        upsert_user(conn, user)
