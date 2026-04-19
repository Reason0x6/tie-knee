from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ShareRecord:
    slug: str
    title: str
    markdown: str
    created_at: str


class ShareAlreadyExistsError(Exception):
    pass


def init_share_db(db_path: str) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS shares (
                slug TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                markdown TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def create_share(db_path: str, slug: str, title: str, markdown: str) -> ShareRecord:
    try:
        with sqlite3.connect(db_path) as connection:
            connection.execute(
                """
                INSERT INTO shares (slug, title, markdown)
                VALUES (?, ?, ?)
                """,
                (slug, title, markdown),
            )
            connection.commit()
    except sqlite3.IntegrityError as exc:
        raise ShareAlreadyExistsError(slug) from exc

    return get_share(db_path, slug)


def overwrite_share(db_path: str, slug: str, title: str, markdown: str) -> ShareRecord | None:
    with sqlite3.connect(db_path) as connection:
        cursor = connection.execute(
            """
            UPDATE shares
            SET title = ?, markdown = ?
            WHERE slug = ?
            """,
            (title, markdown, slug),
        )
        connection.commit()

    if cursor.rowcount == 0:
        return None

    return get_share(db_path, slug)


def get_share(db_path: str, slug: str) -> ShareRecord | None:
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT slug, title, markdown, created_at
            FROM shares
            WHERE slug = ?
            """,
            (slug,),
        ).fetchone()

    if row is None:
        return None

    return ShareRecord(
        slug=row["slug"],
        title=row["title"],
        markdown=row["markdown"],
        created_at=row["created_at"],
    )
