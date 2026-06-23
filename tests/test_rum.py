# tests/test_rum.py
"""
Tests for the RUM system, focused on the privacy invariants (the non-negotiable
core) plus bucketing, rollup math, encryption, and the ingest/dashboard flow.

Run: python -m pytest tests/test_rum.py   (or: python tests/test_rum.py)
"""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rum import privacy, geo, pricing, rollups
from rum.config import BUCKET_GDPR, BUCKET_CCPA, BUCKET_APAC, BUCKET_OTHER


# --------------------------------------------------------------------------- #
# Privacy invariants
# --------------------------------------------------------------------------- #
def test_opt_out_signals_honored():
    assert privacy.opted_out({"Sec-GPC": "1"})
    assert privacy.opted_out({"DNT": "1"})
    assert not privacy.opted_out({})


def test_opt_out_is_case_insensitive():
    # HTTP headers are case-insensitive; Flask's dict(request.headers) title-cases
    # keys ("Sec-Gpc"). Opt-out must still be honored — privacy invariant.
    assert privacy.opted_out({"Sec-Gpc": "1"})
    assert privacy.opted_out({"Dnt": "1"})
    assert privacy.opted_out({"sec-gpc": "1"})


def test_ingest_honors_title_cased_optout_and_country():
    from rum import db, ingest
    store = db._memory_store(None)
    store.sites[1] = {"id": 1, "domain": "localhost", "tier": "agency"}
    before = len(store.events)
    # Title-cased opt-out header (as Flask delivers it) must store nothing.
    res = ingest.ingest(1, {"page_path": "/"}, {"Sec-Gpc": "1"}, "203.0.113.2")
    assert res.status == "ignored"
    assert len(store.events) == before
    # Title-cased country header must still bucket correctly.
    ingest.ingest(1, {"page_path": "/"}, {"Cf-Ipcountry": "FR"}, "203.0.113.3")
    assert store.events[-1]["privacy_bucket"] == "GDPR"
    assert store.events[-1]["country"] == "FR"


def test_pii_is_stripped_from_attribution():
    # ids, classes, selectors, free text must never survive.
    assert privacy._coarse_tag_role("div#login-email") is None
    assert privacy._coarse_tag_role(".user-name") is None
    assert privacy._coarse_tag_role("Some visible text") is None
    assert privacy._coarse_tag_role("img") == "img"
    assert privacy._coarse_tag_role("button[button]") == "button[button]"
    # unknown role dropped, safe tag kept
    assert privacy._coarse_tag_role("a[secret]") == "a"


def test_click_positions_are_percentages_only():
    b = privacy.sanitize_behavior({
        "clicks": [{"x": 50, "y": 25, "id": "#email", "text": "hi"}, {"x": 999, "y": -5}],
    })
    assert b["clicks"][0] == {"x": 50.0, "y": 25.0}     # extra keys dropped
    assert b["clicks"][1] == {"x": 100.0, "y": 0.0}     # clamped to [0,100]


def test_page_path_strips_query_and_fragment():
    assert privacy.sanitize_page_path("/checkout?token=secret#section") == "/checkout"


def test_sanitize_event_allow_lists_fields():
    clean = privacy.sanitize_event({
        "page_path": "/p?q=1",
        "lcp_ms": "2500.7", "cls": "0.1234", "inp_ms": 240,
        "inp_input_delay_ms": 40, "inp_processing_ms": 120, "inp_presentation_ms": 80,
        "lcp_element": "img[img]", "device_class": "mobile", "connection_type": "4g",
        "viewport_w": 390, "viewport_h": 844,
        "email": "should-not-appear@example.com",   # rogue field
    })
    assert "email" not in clean
    assert clean["page_path"] == "/p"
    assert clean["lcp_ms"] == 2501
    assert clean["device_class"] == "mobile"
    assert clean["lcp_element"] == "img[img]"


# --------------------------------------------------------------------------- #
# Geo / privacy bucketing (IP never returned)
# --------------------------------------------------------------------------- #
def test_country_to_bucket():
    assert geo.country_to_bucket("DE") == BUCKET_GDPR
    assert geo.country_to_bucket("GB") == BUCKET_GDPR
    assert geo.country_to_bucket("US") == BUCKET_CCPA
    assert geo.country_to_bucket("JP") == BUCKET_APAC
    assert geo.country_to_bucket("BR") == BUCKET_OTHER
    assert geo.country_to_bucket(None) == BUCKET_OTHER


def test_country_and_bucket_discards_ip():
    country, bucket = geo.country_and_bucket("203.0.113.7", country_override="FR")
    assert country == "FR" and bucket == BUCKET_GDPR
    # The return signature carries no IP, by construction.
    assert "203.0.113.7" not in str((country, bucket))


def test_pipl_origin():
    assert geo.is_pipl_origin("CN")
    assert not geo.is_pipl_origin("US")


# --------------------------------------------------------------------------- #
# Pricing gates
# --------------------------------------------------------------------------- #
def test_free_tier_has_no_rum():
    assert not pricing.get_tier("free").has(pricing.CAP_RUM)


def test_movement_and_flow_are_agency_only():
    pro = pricing.get_tier("pro")
    agency = pricing.get_tier("agency")
    behavior = {"clicks": [{"x": 1, "y": 1}], "moves": [{"x": 2, "y": 2}], "flow": ["/a", "/b"]}
    gated_pro = pricing.gate_behavior_for_tier(behavior, pro)
    assert "moves" not in gated_pro and "flow" not in gated_pro and "clicks" in gated_pro
    gated_agency = pricing.gate_behavior_for_tier(behavior, agency)
    assert "moves" in gated_agency and "flow" in gated_agency


def test_retention_windows():
    assert pricing.get_tier("pro").raw_retention_hours == 24
    assert pricing.get_tier("agency").raw_retention_hours == 24 * 7
    assert pricing.get_tier("pro").rollup_retention_days == 90


# --------------------------------------------------------------------------- #
# Rollup math
# --------------------------------------------------------------------------- #
def test_percentile():
    vals = list(range(1, 101))  # 1..100
    assert abs(rollups.percentile(vals, 50) - 50.5) < 0.5
    assert abs(rollups.percentile(vals, 75) - 75.25) < 0.5
    assert rollups.percentile([], 75) is None


def test_build_rollups_aggregates_inp_breakdown():
    now = datetime.now(timezone.utc)
    events = [
        {"site_id": 1, "page_path": "/", "occurred_at": now, "privacy_bucket": "GDPR",
         "lcp_ms": 2000, "cls": 0.05, "inp_ms": 200,
         "inp_input_delay_ms": 40, "inp_processing_ms": 100, "inp_presentation_ms": 60,
         "behavior": {"clicks": [{"x": 10, "y": 20}], "rage": [{"x": 10, "y": 20, "count": 3}]}},
        {"site_id": 1, "page_path": "/", "occurred_at": now, "privacy_bucket": "GDPR",
         "lcp_ms": 3000, "cls": 0.15, "inp_ms": 400,
         "inp_input_delay_ms": 80, "inp_processing_ms": 200, "inp_presentation_ms": 120,
         "behavior": {"clicks": [{"x": 10, "y": 20}]}},
    ]
    out = rollups.build_rollups_for_events(events, buckets=("day",))
    assert len(out) == 1
    r = out[0]
    assert r["sample_count"] == 2
    assert r["inp_input_delay_p75"] is not None
    assert r["behavior_summary"]["rage_clicks"] == 1
    assert r["heatmap_grid"]["clicks"][rollups._bin(20)][rollups._bin(10)] == 2


# --------------------------------------------------------------------------- #
# Encryption roundtrip (operator-blind envelope)
# --------------------------------------------------------------------------- #
def test_envelope_encryption_roundtrip():
    os.environ["RUM_KMS_MASTER_KEY"] = "test-master-key-for-rum"
    from rum import crypto
    if not crypto.encryption_available():
        return  # cryptography not installed in this env; skip
    payload = {"clicks": [{"x": 12.5, "y": 80.0}], "flow": ["/a", "/b"]}
    env = crypto.encrypt_field("ACME", payload)
    assert "ct" in env and env["t"] == "ACME"
    assert "clicks" not in str(env)  # ciphertext only; plaintext not visible
    assert crypto.decrypt_field(env) == payload
    # Different tenant key cannot decrypt (cross-tenant plaintext unrecoverable).
    forged = dict(env, t="EVIL")
    try:
        crypto.decrypt_field(forged)
        assert False, "cross-tenant decryption must fail"
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# End-to-end ingest -> in-memory store (no DB / no KMS needed)
# --------------------------------------------------------------------------- #
def test_ingest_flow_in_memory():
    from rum import db, ingest
    # Ensure a clean store and an agency-tier site.
    store = db._memory_store(None)
    store.sites[1] = {"id": 1, "domain": "localhost", "tier": "agency"}
    before = len(store.events)
    res = ingest.ingest(
        1,
        {"page_path": "/home?x=1", "lcp_ms": 2400, "cls": 0.08, "inp_ms": 180,
         "inp_input_delay_ms": 30, "inp_processing_ms": 100, "inp_presentation_ms": 50,
         "lcp_element": "img", "device_class": "mobile", "connection_type": "4g",
         "viewport_w": 390, "viewport_h": 844,
         "behavior": {"clicks": [{"x": 50, "y": 50}], "flow": ["/home"]}},
        {"CF-IPCountry": "DE"},
        "203.0.113.9",
    )
    assert res.status == "ok"
    assert len(store.events) == before + 1
    row = store.events[-1]
    assert row["privacy_bucket"] == "GDPR"
    assert row["country"] == "DE"
    assert row["page_path"] == "/home"          # query stripped
    assert "203.0.113.9" not in str(row)        # IP never stored


def test_ingest_opt_out_stores_nothing():
    from rum import db, ingest
    store = db._memory_store(None)
    store.sites[1] = {"id": 1, "domain": "localhost", "tier": "pro"}
    before = len(store.events)
    res = ingest.ingest(1, {"page_path": "/"}, {"Sec-GPC": "1"}, "203.0.113.1")
    assert res.status == "ignored"
    assert len(store.events) == before


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {fn.__name__}")
            traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
