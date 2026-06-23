# rum/migrate.py
"""
Migration runner for RUM tenant databases.

Applies every .sql file in rum/migrations/ (ordered by filename) to a target
database. Because of database-per-tenant isolation, the same migrations are run
against EACH tenant/region database — there is no shared schema to migrate once.

Usage:
    python -m rum.migrate                 # migrate every configured tenant DSN
    python -m rum.migrate <dsn>           # migrate a single DSN
"""
from __future__ import annotations

import os
import sys

from . import db
from .config import all_configured_dsns

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


def migration_files() -> list[str]:
    return sorted(
        os.path.join(MIGRATIONS_DIR, f)
        for f in os.listdir(MIGRATIONS_DIR)
        if f.endswith(".sql")
    )


def migrate_dsn(dsn: str | None) -> None:
    label = dsn.split("@")[-1] if dsn else "in-memory store"
    if not db.pg_available() or not dsn:
        print(f"[migrate] psycopg/DSN unavailable — skipping DDL for {label} "
              f"(in-memory dev store needs no migration).")
        return
    conn = db.connect(dsn)
    try:
        for path in migration_files():
            with open(path, "r", encoding="utf-8") as fh:
                sql = fh.read()
            conn.execute(sql)
            print(f"[migrate] applied {os.path.basename(path)} -> {label}")
    finally:
        conn.close()


def main(argv: list[str]) -> int:
    targets = argv[1:] if len(argv) > 1 else all_configured_dsns()
    if not targets:
        print("[migrate] no DSNs configured; nothing to do (set RUM_TENANT_DB__* "
              "or RUM_DATABASE_URL/DATABASE_URL).")
        return 0
    for dsn in targets:
        migrate_dsn(dsn)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
