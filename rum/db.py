# rum/db.py
"""
Neon (serverless Postgres) access layer for RUM.

Design notes:
  * TLS is mandatory. Every DSN is normalized to `sslmode=require` before use, so
    the edge -> Neon hop is always encrypted (docs/RUM_SYSTEM.md "In transit").
  * Connections are scoped to ONE tenant/region database (database-per-tenant
    isolation). Callers pass a resolved DSN from rum.config.resolve_target().
  * psycopg is optional. If it (or a DSN) is unavailable, we fall back to an
    in-memory store so the Flask app, the snippet endpoint, and the dashboard all
    run in development without a database. The in-memory store mirrors the two
    tables closely enough for the dashboard and rollup job to function.
"""
from __future__ import annotations

import threading
from typing import Any, Iterable

try:  # psycopg 3 preferred
    import psycopg
    from psycopg.types.json import Json as _Json
    _PG = "psycopg3"
except BaseException:  # pragma: no cover - driver optional / native build may panic
    try:
        import psycopg2 as psycopg  # type: ignore
        from psycopg2.extras import Json as _Json  # type: ignore
        _PG = "psycopg2"
    except BaseException:
        psycopg = None  # type: ignore
        _Json = None  # type: ignore
        _PG = None


def pg_available() -> bool:
    return psycopg is not None


def _ensure_tls(dsn: str) -> str:
    """Force TLS. Never allow a plaintext hop to Neon."""
    if "sslmode=" in dsn:
        return dsn
    sep = "&" if "?" in dsn else "?"
    return f"{dsn}{sep}sslmode=require"


# --------------------------------------------------------------------------- #
# In-memory fallback store (dev / no-DB mode)
# --------------------------------------------------------------------------- #
class _MemoryStore:
    """A tiny stand-in for a tenant database, keyed by DSN (or '__local__')."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.sites: dict[int, dict] = {1: {"id": 1, "domain": "localhost", "tier": "agency"}}
        self.events: list[dict] = []
        self.rollups: dict[tuple, dict] = {}
        self._event_seq = 0

    def insert_event(self, row: dict) -> int:
        with self._lock:
            self._event_seq += 1
            row = dict(row, id=self._event_seq)
            self.events.append(row)
            return self._event_seq

    def site_tier(self, site_id: int) -> str:
        return self.sites.get(site_id, {}).get("tier", "free")


_MEM_STORES: dict[str, _MemoryStore] = {}
_MEM_LOCK = threading.Lock()


def _memory_store(dsn: str | None) -> _MemoryStore:
    key = dsn or "__local__"
    with _MEM_LOCK:
        store = _MEM_STORES.get(key)
        if store is None:
            store = _MemoryStore()
            _MEM_STORES[key] = store
        return store


# --------------------------------------------------------------------------- #
# Connection helper
# --------------------------------------------------------------------------- #
class Connection:
    """
    Thin wrapper over a psycopg connection OR the in-memory store. The ingest and
    rollup code uses the high-level methods below so it doesn't care which backend
    is live.
    """

    def __init__(self, dsn: str | None):
        self.dsn = dsn
        self._use_pg = bool(dsn) and pg_available()
        self._conn = None
        if self._use_pg:
            self._conn = psycopg.connect(_ensure_tls(dsn))  # type: ignore
        else:
            self._mem = _memory_store(dsn)

    # --- lifecycle ---------------------------------------------------------- #
    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "Connection":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    @property
    def backend(self) -> str:
        return _PG if self._use_pg else "memory"

    # --- generic helpers ---------------------------------------------------- #
    def execute(self, sql: str, params: Iterable[Any] | None = None) -> None:
        cur = self._conn.cursor()
        cur.execute(sql, params or ())
        self._conn.commit()
        cur.close()

    def query(self, sql: str, params: Iterable[Any] | None = None) -> list[tuple]:
        cur = self._conn.cursor()
        cur.execute(sql, params or ())
        rows = cur.fetchall()
        cur.close()
        return rows

    # --- high-level operations --------------------------------------------- #
    def site_tier(self, site_id: int) -> str:
        if not self._use_pg:
            return self._mem.site_tier(site_id)
        rows = self.query("SELECT tier FROM sites WHERE id = %s", (site_id,))
        return rows[0][0] if rows else "free"

    def fetch_events(self, since, until) -> list[dict]:
        """Raw events in [since, until) across all sites — for the rollup job."""
        cols = [
            "id", "site_id", "page_path", "occurred_at", "privacy_bucket",
            "lcp_ms", "cls", "inp_ms",
            "inp_input_delay_ms", "inp_processing_ms", "inp_presentation_ms",
            "lcp_element", "cls_sources", "device_class", "connection_type",
            "country", "viewport_w", "viewport_h", "behavior",
        ]
        if not self._use_pg:
            out = []
            for e in self._mem.events:
                ts = e.get("occurred_at")
                if ts is not None and since <= ts < until:
                    out.append(dict(e))
            return out
        rows = self.query(
            f"SELECT {', '.join(cols)} FROM rum_events "
            f"WHERE occurred_at >= %s AND occurred_at < %s",
            (since, until),
        )
        return [dict(zip(cols, r)) for r in rows]

    def upsert_rollup(self, row: dict) -> None:
        """Insert-or-update a rollup keyed by its UNIQUE tuple."""
        if not self._use_pg:
            key = (row["site_id"], row["page_path"], row["bucket"],
                   row["bucket_start"], row["privacy_bucket"])
            self._mem.rollups[key] = dict(row)
            return
        cols = [
            "site_id", "page_path", "bucket", "bucket_start", "privacy_bucket",
            "sample_count",
            "lcp_p50", "lcp_p75", "lcp_p95",
            "cls_p50", "cls_p75", "cls_p95",
            "inp_p50", "inp_p75", "inp_p95",
            "inp_input_delay_p75", "inp_processing_p75", "inp_presentation_p75",
            "heatmap_grid", "behavior_summary",
        ]
        json_cols = {"heatmap_grid", "behavior_summary"}
        values = []
        for c in cols:
            v = row.get(c)
            if c in json_cols and v is not None and _Json is not None:
                v = _Json(v)
            values.append(v)
        placeholders = ", ".join(["%s"] * len(cols))
        updates = ", ".join(
            f"{c} = EXCLUDED.{c}" for c in cols
            if c not in ("site_id", "page_path", "bucket", "bucket_start", "privacy_bucket")
        )
        cur = self._conn.cursor()
        cur.execute(
            f"INSERT INTO rum_rollups ({', '.join(cols)}) VALUES ({placeholders}) "
            f"ON CONFLICT (site_id, page_path, bucket, bucket_start, privacy_bucket) "
            f"DO UPDATE SET {updates}",
            values,
        )
        self._conn.commit()
        cur.close()

    def purge_events_before(self, cutoff) -> int:
        if not self._use_pg:
            before = len(self._mem.events)
            self._mem.events = [e for e in self._mem.events if e.get("occurred_at", cutoff) >= cutoff]
            return before - len(self._mem.events)
        cur = self._conn.cursor()
        cur.execute("DELETE FROM rum_events WHERE occurred_at < %s", (cutoff,))
        n = cur.rowcount
        self._conn.commit()
        cur.close()
        return n

    def purge_rollups_before(self, cutoff) -> int:
        if not self._use_pg:
            before = len(self._mem.rollups)
            self._mem.rollups = {k: v for k, v in self._mem.rollups.items()
                                 if v.get("bucket_start", cutoff) >= cutoff}
            return before - len(self._mem.rollups)
        cur = self._conn.cursor()
        cur.execute("DELETE FROM rum_rollups WHERE bucket_start < %s", (cutoff,))
        n = cur.rowcount
        self._conn.commit()
        cur.close()
        return n

    def fetch_rollups(self, site_id: int, bucket: str, since, page_path: str | None = None) -> list[dict]:
        """Rollups for the dashboard."""
        cols = [
            "site_id", "page_path", "bucket", "bucket_start", "privacy_bucket",
            "sample_count",
            "lcp_p50", "lcp_p75", "lcp_p95",
            "cls_p50", "cls_p75", "cls_p95",
            "inp_p50", "inp_p75", "inp_p95",
            "inp_input_delay_p75", "inp_processing_p75", "inp_presentation_p75",
            "heatmap_grid", "behavior_summary",
        ]
        if not self._use_pg:
            out = []
            for (s_id, p_path, b, b_start, _pb), v in self._mem.rollups.items():
                if s_id == site_id and b == bucket and b_start >= since:
                    if page_path is None or p_path == page_path:
                        out.append(dict(v))
            return sorted(out, key=lambda r: r["bucket_start"])
        params = [site_id, bucket, since]
        extra = ""
        if page_path is not None:
            extra = " AND page_path = %s"
            params.append(page_path)
        rows = self.query(
            f"SELECT {', '.join(cols)} FROM rum_rollups "
            f"WHERE site_id = %s AND bucket = %s AND bucket_start >= %s{extra} "
            f"ORDER BY bucket_start ASC",
            params,
        )
        return [dict(zip(cols, r)) for r in rows]

    def insert_event(self, row: dict) -> int:
        """Insert one sanitized + (selectively) encrypted event row."""
        if not self._use_pg:
            return self._mem.insert_event(row)
        cols = [
            "site_id", "page_path", "occurred_at", "privacy_bucket",
            "lcp_ms", "cls", "inp_ms",
            "inp_input_delay_ms", "inp_processing_ms", "inp_presentation_ms",
            "lcp_element", "cls_sources", "device_class", "connection_type",
            "country", "viewport_w", "viewport_h", "behavior",
        ]
        json_cols = {"cls_sources", "behavior"}
        placeholders = ", ".join(["%s"] * len(cols))
        values = []
        for c in cols:
            v = row.get(c)
            if c in json_cols and v is not None and _Json is not None:
                v = _Json(v)
            values.append(v)
        cur = self._conn.cursor()
        cur.execute(
            f"INSERT INTO rum_events ({', '.join(cols)}) VALUES ({placeholders}) RETURNING id",
            values,
        )
        new_id = cur.fetchone()[0]
        self._conn.commit()
        cur.close()
        return new_id


def connect(dsn: str | None) -> Connection:
    return Connection(dsn)
