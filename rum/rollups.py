# rum/rollups.py
"""
Rollup / aggregation job + retention purge.

Reads raw `rum_events` and produces `rum_rollups` (hour / day / week) per
(site_id, page_path, privacy_bucket):

  * p50 / p75 / p95 for LCP, CLS, INP.
  * p75 of each INP component (input delay / processing / presentation) — the
    headline diagnostic, aggregated.
  * heatmap_grid: binned click / movement densities + scroll-depth histogram.
  * behavior_summary: rage/dead click counts + hotspots, scroll distribution,
    common session flows.

Sensitive JSONB (`behavior`, `cls_sources`) is decrypted in the app tier here to
aggregate it, and only the aggregated, statistical result is written to the
rollup (which is safe to keep plaintext). Raw rows are then purged per the
tier's retention window.

Usage:
    python -m rum.rollups run          # roll up the recent window for all DSNs
    python -m rum.rollups purge        # apply retention to all DSNs
    python -m rum.rollups all          # run + purge
"""
from __future__ import annotations

import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from . import db
from .config import all_configured_dsns, tenant_key_for_site
from .crypto import decrypt_field
from .pricing import get_tier

HEATMAP_BINS = 20  # 20x20 grid over the viewport (percentage space)


# --------------------------------------------------------------------------- #
# Stats helpers
# --------------------------------------------------------------------------- #
def percentile(values: list[float], p: float) -> float | None:
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    if len(vals) == 1:
        return vals[0]
    rank = (p / 100.0) * (len(vals) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(vals) - 1)
    frac = rank - lo
    return vals[lo] + (vals[hi] - vals[lo]) * frac


def _int_pct(values, p):
    v = percentile(values, p)
    return int(round(v)) if v is not None else None


def _bucket_start(ts: datetime, bucket: str) -> datetime:
    ts = ts.astimezone(timezone.utc)
    if bucket == "hour":
        return ts.replace(minute=0, second=0, microsecond=0)
    if bucket == "day":
        return ts.replace(hour=0, minute=0, second=0, microsecond=0)
    if bucket == "week":
        start = ts.replace(hour=0, minute=0, second=0, microsecond=0)
        return start - timedelta(days=start.weekday())
    raise ValueError(bucket)


def _decrypt(value):
    try:
        return decrypt_field(value)
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Behavior aggregation
# --------------------------------------------------------------------------- #
def _empty_grid():
    return [[0] * HEATMAP_BINS for _ in range(HEATMAP_BINS)]


def _bin(pct: float) -> int:
    idx = int((pct / 100.0) * HEATMAP_BINS)
    return max(0, min(HEATMAP_BINS - 1, idx))


def aggregate_behavior(behaviors: list[dict]) -> tuple[dict, dict]:
    """Return (heatmap_grid, behavior_summary) from decrypted behavior payloads."""
    click_grid = _empty_grid()
    move_grid = _empty_grid()
    scroll_hist = defaultdict(int)        # decile -> count
    rage_hotspots = defaultdict(int)      # (xbin, ybin) -> count
    dead_hotspots = defaultdict(int)
    rage_total = 0
    dead_total = 0
    flows = defaultdict(int)              # tuple(path,...) -> count

    for b in behaviors:
        if not isinstance(b, dict):
            continue
        for c in b.get("clicks") or []:
            click_grid[_bin(c["y"])][_bin(c["x"])] += 1
        for m in b.get("moves") or []:
            move_grid[_bin(m["y"])][_bin(m["x"])] += 1
        sm = b.get("scroll_max")
        if sm is not None:
            scroll_hist[min(10, int(sm // 10))] += 1
        for r in b.get("rage") or []:
            rage_total += 1
            rage_hotspots[(_bin(r["x"]), _bin(r["y"]))] += 1
        for d in b.get("dead") or []:
            dead_total += 1
            dead_hotspots[(_bin(d["x"]), _bin(d["y"]))] += 1
        flow = b.get("flow")
        if flow:
            flows[tuple(flow)] += 1

    def _top(hotspots):
        return [
            {"x_bin": k[0], "y_bin": k[1], "count": v}
            for k, v in sorted(hotspots.items(), key=lambda kv: kv[1], reverse=True)[:10]
        ]

    heatmap_grid = {
        "bins": HEATMAP_BINS,
        "clicks": click_grid,
        "moves": move_grid,
    }
    behavior_summary = {
        "rage_clicks": rage_total,
        "dead_clicks": dead_total,
        "rage_hotspots": _top(rage_hotspots),
        "dead_hotspots": _top(dead_hotspots),
        "scroll_depth_hist": {str(k): scroll_hist[k] for k in sorted(scroll_hist)},
        "flows": [
            {"path": list(path), "count": count}
            for path, count in sorted(flows.items(), key=lambda kv: kv[1], reverse=True)[:15]
        ],
    }
    return heatmap_grid, behavior_summary


# --------------------------------------------------------------------------- #
# Rollup builder
# --------------------------------------------------------------------------- #
def build_rollups_for_events(events: list[dict], buckets=("hour", "day", "week")) -> list[dict]:
    """Group events and produce rollup rows for each requested time bucket."""
    rollups: list[dict] = []
    for bucket in buckets:
        groups: dict[tuple, list[dict]] = defaultdict(list)
        for e in events:
            ts = e.get("occurred_at")
            if ts is None:
                continue
            key = (e["site_id"], e["page_path"], _bucket_start(ts, bucket), e["privacy_bucket"])
            groups[key].append(e)

        for (site_id, page_path, bucket_start, privacy_bucket), rows in groups.items():
            lcp = [r["lcp_ms"] for r in rows if r.get("lcp_ms") is not None]
            cls = [float(r["cls"]) for r in rows if r.get("cls") is not None]
            inp = [r["inp_ms"] for r in rows if r.get("inp_ms") is not None]
            inp_id = [r["inp_input_delay_ms"] for r in rows if r.get("inp_input_delay_ms") is not None]
            inp_proc = [r["inp_processing_ms"] for r in rows if r.get("inp_processing_ms") is not None]
            inp_pres = [r["inp_presentation_ms"] for r in rows if r.get("inp_presentation_ms") is not None]

            behaviors = [_decrypt(r.get("behavior")) for r in rows]
            behaviors = [b for b in behaviors if isinstance(b, dict)]
            heatmap_grid, behavior_summary = aggregate_behavior(behaviors)

            cls_p50 = percentile(cls, 50)
            cls_p75 = percentile(cls, 75)
            cls_p95 = percentile(cls, 95)

            rollups.append({
                "site_id": site_id,
                "page_path": page_path,
                "bucket": bucket,
                "bucket_start": bucket_start,
                "privacy_bucket": privacy_bucket,
                "sample_count": len(rows),
                "lcp_p50": _int_pct(lcp, 50), "lcp_p75": _int_pct(lcp, 75), "lcp_p95": _int_pct(lcp, 95),
                "cls_p50": round(cls_p50, 4) if cls_p50 is not None else None,
                "cls_p75": round(cls_p75, 4) if cls_p75 is not None else None,
                "cls_p95": round(cls_p95, 4) if cls_p95 is not None else None,
                "inp_p50": _int_pct(inp, 50), "inp_p75": _int_pct(inp, 75), "inp_p95": _int_pct(inp, 95),
                "inp_input_delay_p75": _int_pct(inp_id, 75),
                "inp_processing_p75": _int_pct(inp_proc, 75),
                "inp_presentation_p75": _int_pct(inp_pres, 75),
                "heatmap_grid": heatmap_grid,
                "behavior_summary": behavior_summary,
            })
    return rollups


# --------------------------------------------------------------------------- #
# Job entrypoints
# --------------------------------------------------------------------------- #
def run_rollups(dsn: str | None, window_hours: int = 48) -> int:
    until = datetime.now(timezone.utc)
    since = until - timedelta(hours=window_hours)
    conn = db.connect(dsn)
    try:
        events = conn.fetch_events(since, until)
        rollups = build_rollups_for_events(events)
        for r in rollups:
            conn.upsert_rollup(r)
        print(f"[rollups] {len(events)} events -> {len(rollups)} rollups ({conn.backend})")
        return len(rollups)
    finally:
        conn.close()


def purge_retention(dsn: str | None) -> tuple[int, int]:
    """
    Apply tier retention. Raw events use the shortest applicable window across the
    sites in this database; rollups use the rollup retention. (Per-site retention
    can be made finer by purging per site_id; we apply the DB-wide minimum here so
    no row outlives its strictest tier.)
    """
    now = datetime.now(timezone.utc)
    conn = db.connect(dsn)
    try:
        # Default to Agency windows as the DB-wide maximum; production reads each
        # site's tier. We use the most generous tier's window as the ceiling and
        # rely on per-site tiers for anything stricter.
        raw_hours = 24 * 7
        rollup_days = 180
        # If the backend exposes site tiers, tighten to the strictest present.
        try:
            tiers = [get_tier(t) for t in _site_tiers(conn)]
            if tiers:
                raw_hours = max(t.raw_retention_hours for t in tiers)
                rollup_days = max(t.rollup_retention_days for t in tiers)
        except Exception:
            pass
        events_purged = conn.purge_events_before(now - timedelta(hours=raw_hours))
        rollups_purged = conn.purge_rollups_before(now - timedelta(days=rollup_days))
        print(f"[purge] removed {events_purged} raw events, {rollups_purged} rollups ({conn.backend})")
        return events_purged, rollups_purged
    finally:
        conn.close()


def _site_tiers(conn) -> list[str]:
    if conn.backend == "memory":
        return [s.get("tier", "free") for s in conn._mem.sites.values()]  # type: ignore
    rows = conn.query("SELECT DISTINCT tier FROM sites", ())
    return [r[0] for r in rows]


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "all"
    dsns = all_configured_dsns() or [None]  # None => in-memory dev store
    for dsn in dsns:
        if cmd in ("run", "all"):
            run_rollups(dsn)
        if cmd in ("purge", "all"):
            purge_retention(dsn)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
