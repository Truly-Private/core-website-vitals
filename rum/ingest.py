# rum/ingest.py
"""
Ingest orchestration — the edge step that turns a raw beacon into a stored event.

Order of operations (privacy-first by construction):

  1. Honor opt-out (GPC / DNT) at the transport layer  -> drop, store nothing.
  2. Derive country + privacy_bucket from the IP, then DISCARD the IP. The IP is
     never passed beyond rum.geo and is never logged or stored.
  3. Enforce PIPL: a China-origin event with no in-region DB is dropped, never
     transferred out of region.
  4. Resolve the regional tenant DB for the bucket (residency routing).
  5. Gate behavioral signals by the site's pricing tier (strip what's not owned).
  6. Sanitize to the coarse, PII-free shape the schema allows.
  7. Envelope-encrypt the sensitive JSONB (`behavior`, `cls_sources`) per tenant
     BEFORE write; keep coarse aggregate/index columns plaintext.
  8. Write to the resolved regional database.

Returns a small status dict; never returns anything derived from the IP.
"""
from __future__ import annotations

from datetime import datetime, timezone

from . import db
from .config import resolve_target
from .crypto import encrypt_field, encryption_available
from .geo import country_and_bucket, is_pipl_origin
from .pricing import get_tier, gate_behavior_for_tier, CAP_RUM
from .privacy import opted_out, sanitize_event


class IngestResult:
    def __init__(self, status: str, code: int, detail: str = "", event_id: int | None = None):
        self.status = status
        self.code = code
        self.detail = detail
        self.event_id = event_id

    def as_dict(self) -> dict:
        d = {"status": self.status}
        if self.detail:
            d["detail"] = self.detail
        return d


def ingest(site_id: int, payload: dict, headers: dict, client_ip: str | None) -> IngestResult:
    # Normalize headers to lowercase keys once — HTTP header names are
    # case-insensitive and callers may pass a title-cased dict.
    h = {str(k).lower(): v for k, v in dict(headers).items()}

    # 1. Opt-out: collect/store nothing.
    if opted_out(h):
        return IngestResult("ignored", 204, "opt-out honored (GPC/DNT)")

    # 2. Country-only geo, then the IP is discarded (never propagated past here).
    country_override = h.get("cf-ipcountry") or h.get("x-country")
    country, privacy_bucket = country_and_bucket(client_ip, country_override)
    client_ip = None  # explicit: drop the IP reference immediately.

    # 4. Resolve the regional tenant database for this bucket (residency).
    target = resolve_target(site_id, privacy_bucket)

    # 3. PIPL: China-origin with no in-region DB -> drop, do not transfer.
    if is_pipl_origin(country) and target.region != "APAC" and not target.dsn:
        return IngestResult("dropped", 204, "PIPL: no in-region store; not transferred")
    if is_pipl_origin(country) and target.dsn is None:
        return IngestResult("dropped", 204, "PIPL: no in-region store; not transferred")

    conn = db.connect(target.dsn)
    try:
        # 5. Tier gate. Free tier collects no RUM at all.
        tier = get_tier(conn.site_tier(site_id))
        if not tier.has(CAP_RUM):
            return IngestResult("ignored", 204, "RUM not enabled for plan")

        # 6. Sanitize to the coarse PII-free shape.
        clean = sanitize_event(payload)
        clean["behavior"] = gate_behavior_for_tier(clean.get("behavior") or {}, tier)

        # 7. Envelope-encrypt sensitive JSONB before write (operator-blind).
        behavior_payload = clean.get("behavior") or {}
        cls_payload = clean.get("cls_sources") or []
        if encryption_available():
            behavior_stored = encrypt_field(target.tenant_key, behavior_payload) if behavior_payload else None
            cls_stored = encrypt_field(target.tenant_key, cls_payload) if cls_payload else None
        else:
            # No KMS configured (dev). Store plaintext JSONB so the dashboard still
            # works locally; production requires RUM_KMS_MASTER_KEY (see crypto.py).
            behavior_stored = behavior_payload or None
            cls_stored = cls_payload or None

        row = {
            "site_id": site_id,
            "page_path": clean["page_path"],
            "occurred_at": datetime.now(timezone.utc),
            "privacy_bucket": privacy_bucket,
            "lcp_ms": clean["lcp_ms"],
            "cls": clean["cls"],
            "inp_ms": clean["inp_ms"],
            "inp_input_delay_ms": clean["inp_input_delay_ms"],
            "inp_processing_ms": clean["inp_processing_ms"],
            "inp_presentation_ms": clean["inp_presentation_ms"],
            "lcp_element": clean["lcp_element"],
            "cls_sources": cls_stored,
            "device_class": clean["device_class"],
            "connection_type": clean["connection_type"],
            "country": country,
            "viewport_w": clean["viewport_w"],
            "viewport_h": clean["viewport_h"],
            "behavior": behavior_stored,
        }

        # 8. Write to the resolved regional database.
        event_id = conn.insert_event(row)
        return IngestResult("ok", 204, event_id=event_id)
    finally:
        conn.close()
