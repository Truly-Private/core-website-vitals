# rum/privacy.py
"""
Privacy invariants enforced server-side at ingest.

The snippet is built to never collect PII, but the pipeline must not *trust* the
payload — these are hard invariants, not config toggles (docs/RUM_SYSTEM.md,
"Privacy pipeline"). Anything that arrives is sanitized to the coarse, positional,
statistical shape the schema allows; anything outside that shape is dropped.

Enforced here:
  * GPC / DNT honored: a request that signals opt-out collects/stores nothing.
  * No element IDs, no text content, no form values: only coarse tag+role
    descriptors survive; free-text / id-like fields are stripped.
  * Click positions kept only as viewport percentages clamped to [0, 100].
  * Numeric metrics coerced and bounded; unknown keys dropped (allow-list only).
"""
from __future__ import annotations

import re
from typing import Any

# Coarse descriptors are limited to an allow-list of HTML tag names + ARIA roles.
_ALLOWED_TAGS = {
    "img", "video", "picture", "svg", "canvas", "h1", "h2", "h3", "p", "div",
    "section", "main", "header", "footer", "nav", "a", "button", "input",
    "form", "ul", "ol", "li", "table", "span", "iframe", "figure", "article",
}
_ALLOWED_ROLES = {
    "button", "link", "img", "banner", "navigation", "main", "heading",
    "list", "listitem", "form", "textbox", "region", "article", "contentinfo",
}
_TAG_ROLE_RE = re.compile(r"^[a-z][a-z0-9]{0,15}(\[[a-z]{1,20}\])?$")

DEVICE_CLASSES = {"mobile", "tablet", "desktop"}
CONNECTION_TYPES = {"slow-2g", "2g", "3g", "4g", "5g", "unknown"}


def opted_out(headers: dict) -> bool:
    """
    True if the request signals Global Privacy Control or Do Not Track.

    The snippet already refuses to send when these are set, but we re-check the
    transport headers (`Sec-GPC: 1`, `DNT: 1`) so an opt-out is honored even if a
    beacon slips through. When true, the caller collects and stores nothing.
    """
    # HTTP header names are case-insensitive; normalize so a title-cased dict
    # (e.g. Flask's `dict(request.headers)` -> "Sec-Gpc") still matches.
    lower = {str(k).lower(): v for k, v in dict(headers).items()}

    def _h(name: str) -> str:
        return str(lower.get(name.lower()) or "").strip()

    if _h("Sec-GPC") == "1":
        return True
    if _h("DNT") == "1":
        return True
    return False


def _clamp_pct(value: Any) -> float | None:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v < 0:
        v = 0.0
    if v > 100:
        v = 100.0
    return round(v, 2)


def _coarse_tag_role(value: Any) -> str | None:
    """
    Accept only a coarse `tag` or `tag[role]` descriptor. Reject anything that
    looks like an id, class, selector, or free text — those could carry PII.
    """
    if not isinstance(value, str):
        return None
    v = value.strip().lower()
    if not v or not _TAG_ROLE_RE.match(v):
        return None
    tag = v.split("[", 1)[0]
    if tag not in _ALLOWED_TAGS:
        return None
    if "[" in v:
        role = v[v.index("[") + 1: v.index("]")]
        if role not in _ALLOWED_ROLES:
            return tag  # drop an unrecognized role, keep the safe tag
    return v


def _int(value: Any, lo: int = 0, hi: int = 600000) -> int | None:
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        return None
    if n < lo:
        n = lo
    if n > hi:
        n = hi
    return n


def _num(value: Any, lo: float = 0.0, hi: float = 100.0) -> float | None:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    if n < lo:
        n = lo
    if n > hi:
        n = hi
    return round(n, 4)


def sanitize_cls_sources(raw: Any) -> list[dict]:
    """Coarse CLS shift attribution: [{el: tag[role], value: float}, ...]."""
    out: list[dict] = []
    if not isinstance(raw, list):
        return out
    for item in raw[:10]:
        if not isinstance(item, dict):
            continue
        el = _coarse_tag_role(item.get("el"))
        val = _num(item.get("value"), 0.0, 5.0)
        if el or val is not None:
            out.append({"el": el, "value": val})
    return out


def sanitize_behavior(raw: Any) -> dict:
    """
    Reduce a raw behavior payload to the strict allow-listed, positional/statistical
    shape. Clicks/movement become viewport percentages; rage/dead clicks become
    counts and coarse positions; scroll becomes depth milestones; flow is an
    ordered list of page paths (no identity).
    """
    b = raw if isinstance(raw, dict) else {}
    out: dict[str, Any] = {}

    # Clicks: list of {x%, y%} only.
    clicks = []
    for c in (b.get("clicks") or [])[:500]:
        if not isinstance(c, dict):
            continue
        x, y = _clamp_pct(c.get("x")), _clamp_pct(c.get("y"))
        if x is not None and y is not None:
            clicks.append({"x": x, "y": y})
    if clicks:
        out["clicks"] = clicks

    # Throttled mouse-movement samples: list of {x%, y%} (Agency tier).
    moves = []
    for m in (b.get("moves") or [])[:1000]:
        if not isinstance(m, dict):
            continue
        x, y = _clamp_pct(m.get("x")), _clamp_pct(m.get("y"))
        if x is not None and y is not None:
            moves.append({"x": x, "y": y})
    if moves:
        out["moves"] = moves

    # Rage clicks: count + coarse positions.
    rage = []
    for r in (b.get("rage") or [])[:100]:
        if not isinstance(r, dict):
            continue
        x, y = _clamp_pct(r.get("x")), _clamp_pct(r.get("y"))
        n = _int(r.get("count"), 3, 100)
        if x is not None and y is not None:
            rage.append({"x": x, "y": y, "count": n or 3})
    if rage:
        out["rage"] = rage

    # Dead clicks: coarse positions (+ coarse tag/role, never id/text).
    dead = []
    for d in (b.get("dead") or [])[:100]:
        if not isinstance(d, dict):
            continue
        x, y = _clamp_pct(d.get("x")), _clamp_pct(d.get("y"))
        if x is not None and y is not None:
            dead.append({"x": x, "y": y, "el": _coarse_tag_role(d.get("el"))})
    if dead:
        out["dead"] = dead

    # Scroll depth: max % + sampled milestones.
    max_scroll = _clamp_pct(b.get("scroll_max"))
    if max_scroll is not None:
        out["scroll_max"] = max_scroll
    milestones = [m for m in (b.get("scroll_milestones") or []) if _clamp_pct(m) is not None][:10]
    if milestones:
        out["scroll_milestones"] = [_clamp_pct(m) for m in milestones]

    # Session flow: ordered page-path list only (no identity, no query strings).
    flow = []
    for p in (b.get("flow") or [])[:50]:
        if isinstance(p, str) and p.startswith("/"):
            flow.append(sanitize_page_path(p))
    if flow:
        out["flow"] = flow

    return out


def sanitize_page_path(path: Any) -> str:
    """Keep path only — strip query string and fragment (can carry PII/tokens)."""
    if not isinstance(path, str) or not path:
        return "/"
    p = path.split("#", 1)[0].split("?", 1)[0].strip()
    if not p.startswith("/"):
        p = "/" + p
    return p[:512]


def sanitize_event(raw: dict) -> dict:
    """
    Validate + sanitize a full inbound RUM event into the coarse, PII-free shape
    the schema accepts. Unknown keys are dropped (allow-list only).
    """
    e = raw if isinstance(raw, dict) else {}
    device = str(e.get("device_class") or "").strip().lower()
    conn = str(e.get("connection_type") or "").strip().lower()
    return {
        "page_path": sanitize_page_path(e.get("page_path")),
        "lcp_ms": _int(e.get("lcp_ms")),
        "cls": _num(e.get("cls"), 0.0, 100.0),
        "inp_ms": _int(e.get("inp_ms")),
        "inp_input_delay_ms": _int(e.get("inp_input_delay_ms")),
        "inp_processing_ms": _int(e.get("inp_processing_ms")),
        "inp_presentation_ms": _int(e.get("inp_presentation_ms")),
        "lcp_element": _coarse_tag_role(e.get("lcp_element")),
        "cls_sources": sanitize_cls_sources(e.get("cls_sources")),
        "device_class": device if device in DEVICE_CLASSES else None,
        "connection_type": conn if conn in CONNECTION_TYPES else None,
        "viewport_w": _int(e.get("viewport_w"), 0, 20000),
        "viewport_h": _int(e.get("viewport_h"), 0, 20000),
        "behavior": sanitize_behavior(e.get("behavior")),
    }
