# rum/api.py
"""
Flask blueprint wiring the RUM system into the existing SEO analyzer app.

Routes:
  POST /rum/collect?site=<id>      Ingest beacon (returns 204; the snippet's edge).
  GET  /rum/liftlog-rum.js         Serve the open-source snippet (first-party).
  GET  /rum/sites/<id>             Site detail page: "Real Users" + "Heatmaps" tabs.
  GET  /rum/api/sites/<id>/realuser   JSON for the Real Users tab.
  GET  /rum/api/sites/<id>/heatmaps   JSON for the Heatmaps tab.
  GET  /rum/install/<id>           Copy-paste install snippet UI helper (JSON).

The dashboard reads from `rum_rollups` (aggregated, plaintext-safe) so per-row
encrypted payloads never need bulk decryption to render. Tier gates hide features
the plan doesn't include.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify, render_template, send_from_directory, abort

from . import db
from .config import resolve_target, BUCKET_OTHER
from .ingest import ingest
from .pricing import (
    get_tier, CAP_RUM, CAP_MOVEMENT, CAP_SESSION_FLOW, CAP_PAGE_BREAKDOWN,
    CAP_CLICK_HEATMAP, CAP_SCROLL_HEATMAP, CAP_RAGE, CAP_DEAD,
)

bp = Blueprint(
    "rum", __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/rum/static",
)

SNIPPET_DIR = os.path.join(os.path.dirname(__file__), "snippet")

# CWV thresholds (Google): good / needs-improvement boundaries.
THRESHOLDS = {
    "lcp": {"good": 2500, "poor": 4000},
    "cls": {"good": 0.1, "poor": 0.25},
    "inp": {"good": 200, "poor": 500},
}


def _rating(metric: str, value):
    if value is None:
        return "none"
    t = THRESHOLDS[metric]
    if value <= t["good"]:
        return "good"
    if value <= t["poor"]:
        return "needs-improvement"
    return "poor"


def _client_ip() -> str | None:
    # The edge hands us the IP; we pass it ONLY to rum.geo, which discards it.
    fwd = request.headers.get("X-Forwarded-For", "")
    return fwd.split(",")[0].strip() if fwd else request.remote_addr


# --------------------------------------------------------------------------- #
# Ingest + snippet
# --------------------------------------------------------------------------- #
@bp.route("/rum/collect", methods=["POST"])
def collect():
    try:
        site_id = int(request.args.get("site") or 0)
    except (TypeError, ValueError):
        site_id = 0
    if not site_id:
        # Snippet always sends ?site=; missing => bad request but no body echoed.
        return ("", 400)
    payload = request.get_json(silent=True) or {}
    result = ingest(site_id, payload, dict(request.headers), _client_ip())
    # Always 204 on accepted/ignored/dropped so the beacon never blocks or leaks.
    return ("", 204 if result.code in (204, 200) else result.code)


@bp.route("/rum/liftlog-rum.js", methods=["GET"])
def snippet():
    resp = send_from_directory(SNIPPET_DIR, "liftlog-rum.js", mimetype="application/javascript")
    resp.headers["Cache-Control"] = "public, max-age=3600"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


# --------------------------------------------------------------------------- #
# Dashboard data
# --------------------------------------------------------------------------- #
def _conn_for_site(site_id: int):
    # For reads we use the OTHER-bucket region as the primary read DB; a fuller
    # implementation fans out across the tenant's regional DBs and merges.
    target = resolve_target(site_id, BUCKET_OTHER)
    return db.connect(target.dsn)


def _latest_rollups(conn, site_id: int, bucket="day", days=30, page_path=None):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    return conn.fetch_rollups(site_id, bucket, since, page_path=page_path)


def _aggregate_p75(rollups, field):
    """Sample-weighted average of a per-bucket p75 — a stable headline number."""
    num = den = 0
    for r in rollups:
        v = r.get(field)
        n = r.get("sample_count") or 0
        if v is not None and n:
            num += float(v) * n
            den += n
    if not den:
        return None
    val = num / den
    return round(val, 4) if field.startswith("cls") else int(round(val))


@bp.route("/rum/api/sites/<int:site_id>/realuser", methods=["GET"])
def realuser_data(site_id: int):
    conn = _conn_for_site(site_id)
    try:
        tier = get_tier(conn.site_tier(site_id))
        if not tier.has(CAP_RUM):
            return jsonify({"enabled": False, "reason": "RUM requires Pro or Agency."}), 200

        rollups = _latest_rollups(conn, site_id, "day", 30)
        cwv = {
            "lcp": _aggregate_p75(rollups, "lcp_p75"),
            "cls": _aggregate_p75(rollups, "cls_p75"),
            "inp": _aggregate_p75(rollups, "inp_p75"),
        }
        inp_breakdown = {
            "input_delay": _aggregate_p75(rollups, "inp_input_delay_p75"),
            "processing": _aggregate_p75(rollups, "inp_processing_p75"),
            "presentation": _aggregate_p75(rollups, "inp_presentation_p75"),
        }
        ratings = {m: _rating(m, cwv[m]) for m in ("lcp", "cls", "inp")}
        sample_count = sum(r.get("sample_count") or 0 for r in rollups)

        # Per-page performance table (Agency: per-page; Pro: site-level only).
        per_page = []
        if tier.has(CAP_PAGE_BREAKDOWN):
            pages = {}
            for r in rollups:
                pages.setdefault(r["page_path"], []).append(r)
            for path, rs in pages.items():
                per_page.append({
                    "page_path": path,
                    "samples": sum(x.get("sample_count") or 0 for x in rs),
                    "lcp_p75": _aggregate_p75(rs, "lcp_p75"),
                    "cls_p75": _aggregate_p75(rs, "cls_p75"),
                    "inp_p75": _aggregate_p75(rs, "inp_p75"),
                })
            per_page.sort(key=lambda p: (p["inp_p75"] or 0), reverse=True)

        # RUM vs CrUX comparison badges. Real CrUX values are injected via env or
        # the existing CrUX integration; absent that we expose RUM alone with a
        # null CrUX so the component renders "no CrUX yet" rather than fabricating.
        crux = _crux_baseline(site_id)
        comparison = {
            m: {
                "rum": cwv[m],
                "crux": (crux or {}).get(m),
                "divergence": (
                    round(cwv[m] - crux[m], 4)
                    if crux and crux.get(m) is not None and cwv[m] is not None else None
                ),
            }
            for m in ("lcp", "cls", "inp")
        }

        # LCP element + CLS source tracking (coarse).
        lcp_elements = _top_lcp_elements(conn, site_id)
        cls_sources = _top_cls_sources(conn, site_id)

        # Device / connection breakdown.
        breakdown = _device_connection_breakdown(conn, site_id)

        return jsonify({
            "enabled": True,
            "tier": tier.name,
            "sample_count": sample_count,
            "cwv": cwv,
            "ratings": ratings,
            "thresholds": THRESHOLDS,
            "inp_breakdown": inp_breakdown,
            "comparison": comparison,
            "per_page": per_page,
            "page_breakdown_available": tier.has(CAP_PAGE_BREAKDOWN),
            "lcp_elements": lcp_elements,
            "cls_sources": cls_sources,
            "device_connection": breakdown,
            "trend": [
                {
                    "t": r["bucket_start"].isoformat() if hasattr(r["bucket_start"], "isoformat") else str(r["bucket_start"]),
                    "lcp_p75": r.get("lcp_p75"), "cls_p75": r.get("cls_p75"), "inp_p75": r.get("inp_p75"),
                }
                for r in rollups
            ],
        })
    finally:
        conn.close()


@bp.route("/rum/api/sites/<int:site_id>/heatmaps", methods=["GET"])
def heatmaps_data(site_id: int):
    page_path = request.args.get("page")
    conn = _conn_for_site(site_id)
    try:
        tier = get_tier(conn.site_tier(site_id))
        if not tier.has(CAP_RUM):
            return jsonify({"enabled": False, "reason": "RUM requires Pro or Agency."}), 200

        rollups = _latest_rollups(conn, site_id, "day", 30, page_path=page_path)

        # Merge heatmap grids across the window.
        bins = 20
        clicks = [[0] * bins for _ in range(bins)]
        moves = [[0] * bins for _ in range(bins)]
        rage_total = dead_total = 0
        rage_hotspots, dead_hotspots = {}, {}
        scroll_hist = {}
        flows = {}
        for r in rollups:
            grid = r.get("heatmap_grid") or {}
            for y in range(min(bins, len(grid.get("clicks", [])))):
                for x in range(min(bins, len(grid["clicks"][y]))):
                    clicks[y][x] += grid["clicks"][y][x]
            if tier.has(CAP_MOVEMENT):
                for y in range(min(bins, len(grid.get("moves", [])))):
                    for x in range(min(bins, len(grid["moves"][y]))):
                        moves[y][x] += grid["moves"][y][x]
            summ = r.get("behavior_summary") or {}
            rage_total += summ.get("rage_clicks", 0)
            dead_total += summ.get("dead_clicks", 0)
            for h in summ.get("rage_hotspots", []):
                rage_hotspots[(h["x_bin"], h["y_bin"])] = rage_hotspots.get((h["x_bin"], h["y_bin"]), 0) + h["count"]
            for h in summ.get("dead_hotspots", []):
                dead_hotspots[(h["x_bin"], h["y_bin"])] = dead_hotspots.get((h["x_bin"], h["y_bin"]), 0) + h["count"]
            for k, v in (summ.get("scroll_depth_hist") or {}).items():
                scroll_hist[k] = scroll_hist.get(k, 0) + v
            if tier.has(CAP_SESSION_FLOW):
                for f in summ.get("flows", []):
                    key = tuple(f["path"])
                    flows[key] = flows.get(key, 0) + f["count"]

        out = {
            "enabled": True,
            "tier": tier.name,
            "bins": bins,
            "click_heatmap": clicks if tier.has(CAP_CLICK_HEATMAP) else None,
            "scroll_hist": scroll_hist if tier.has(CAP_SCROLL_HEATMAP) else None,
            "movement_heatmap": moves if tier.has(CAP_MOVEMENT) else None,
            "rage": {
                "total": rage_total,
                "hotspots": [{"x_bin": k[0], "y_bin": k[1], "count": v}
                             for k, v in sorted(rage_hotspots.items(), key=lambda i: i[1], reverse=True)[:10]],
            } if tier.has(CAP_RAGE) else None,
            "dead": {
                "total": dead_total,
                "hotspots": [{"x_bin": k[0], "y_bin": k[1], "count": v}
                             for k, v in sorted(dead_hotspots.items(), key=lambda i: i[1], reverse=True)[:10]],
            } if tier.has(CAP_DEAD) else None,
            "flows": [{"path": list(k), "count": v}
                      for k, v in sorted(flows.items(), key=lambda i: i[1], reverse=True)[:15]]
                     if tier.has(CAP_SESSION_FLOW) else None,
            "screenshot_url": _screenshot_url(site_id, page_path),
            "features": {
                "movement_heatmap": tier.has(CAP_MOVEMENT),
                "session_flow": tier.has(CAP_SESSION_FLOW),
            },
        }
        return jsonify(out)
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Dashboard pages
# --------------------------------------------------------------------------- #
@bp.route("/rum/sites/<int:site_id>", methods=["GET"])
def site_detail(site_id: int):
    conn = _conn_for_site(site_id)
    try:
        tier = get_tier(conn.site_tier(site_id))
    finally:
        conn.close()
    endpoint = request.url_root.rstrip("/")
    return render_template(
        "rum_dashboard.html",
        site_id=site_id,
        tier=tier.name,
        rum_enabled=tier.has(CAP_RUM),
        snippet_src=f"{endpoint}/rum/liftlog-rum.js",
        collect_endpoint=f"{endpoint}/rum/collect",
    )


@bp.route("/rum/install/<int:site_id>", methods=["GET"])
def install(site_id: int):
    endpoint = request.url_root.rstrip("/")
    tag = (
        f'<script async src="{endpoint}/rum/liftlog-rum.js" '
        f'data-site="{site_id}" data-endpoint="{endpoint}/rum/collect"></script>'
    )
    return jsonify({"site_id": site_id, "snippet_tag": tag,
                    "snippet_source_url": f"{endpoint}/rum/liftlog-rum.js"})


# --------------------------------------------------------------------------- #
# Helpers that source coarse attribution from raw rollup/event data
# --------------------------------------------------------------------------- #
def _crux_baseline(site_id: int):
    """
    CrUX p75 baseline for comparison badges. Hooks into the existing CrUX data
    source when configured (env `RUM_CRUX_<site_id>_<metric>`); returns None per
    metric otherwise so the UI shows "awaiting CrUX" rather than a fabricated value.
    """
    out = {}
    for m in ("lcp", "cls", "inp"):
        raw = os.environ.get(f"RUM_CRUX_{site_id}_{m.upper()}")
        if raw:
            try:
                out[m] = float(raw) if m == "cls" else int(raw)
            except ValueError:
                out[m] = None
        else:
            out[m] = None
    return out if any(v is not None for v in out.values()) else None


def _screenshot_url(site_id: int, page_path: str | None):
    """Server-captured screenshot the heatmap overlays on. Pluggable capture svc."""
    base = os.environ.get("RUM_SCREENSHOT_BASE")
    if not base:
        return None
    return f"{base.rstrip('/')}/{site_id}{page_path or '/'}"


def _top_lcp_elements(conn, site_id: int, limit=5):
    if conn.backend == "memory":
        counts = {}
        for e in conn._mem.events:  # type: ignore
            if e.get("site_id") == site_id and e.get("lcp_element"):
                counts[e["lcp_element"]] = counts.get(e["lcp_element"], 0) + 1
        return [{"element": k, "count": v}
                for k, v in sorted(counts.items(), key=lambda i: i[1], reverse=True)[:limit]]
    rows = conn.query(
        "SELECT lcp_element, COUNT(*) FROM rum_events "
        "WHERE site_id = %s AND lcp_element IS NOT NULL "
        "GROUP BY lcp_element ORDER BY 2 DESC LIMIT %s",
        (site_id, limit),
    )
    return [{"element": r[0], "count": r[1]} for r in rows]


def _top_cls_sources(conn, site_id: int, limit=5):
    # cls_sources is encrypted at rest; CLS source ranking is surfaced via the
    # rollup aggregation in a full build. Here we expose what the in-memory store
    # has (dev) and otherwise defer to rollups.
    if conn.backend == "memory":
        counts = {}
        for e in conn._mem.events:  # type: ignore
            if e.get("site_id") != site_id:
                continue
            for s in (e.get("cls_sources") or []):
                el = s.get("el") if isinstance(s, dict) else None
                if el:
                    counts[el] = counts.get(el, 0) + (s.get("value") or 0)
        return [{"element": k, "impact": round(v, 4)}
                for k, v in sorted(counts.items(), key=lambda i: i[1], reverse=True)[:limit]]
    return []


def _device_connection_breakdown(conn, site_id: int):
    if conn.backend == "memory":
        dev, net = {}, {}
        for e in conn._mem.events:  # type: ignore
            if e.get("site_id") != site_id:
                continue
            if e.get("device_class"):
                dev[e["device_class"]] = dev.get(e["device_class"], 0) + 1
            if e.get("connection_type"):
                net[e["connection_type"]] = net.get(e["connection_type"], 0) + 1
        return {"device_class": dev, "connection_type": net}
    dev = dict(conn.query(
        "SELECT device_class, COUNT(*) FROM rum_events WHERE site_id=%s "
        "AND device_class IS NOT NULL GROUP BY 1", (site_id,)))
    net = dict(conn.query(
        "SELECT connection_type, COUNT(*) FROM rum_events WHERE site_id=%s "
        "AND connection_type IS NOT NULL GROUP BY 1", (site_id,)))
    return {"device_class": dev, "connection_type": net}
