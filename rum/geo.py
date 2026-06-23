# rum/geo.py
"""
Edge geo handling — the single place a visitor IP is ever touched.

The contract (docs/RUM_SYSTEM.md, "Privacy pipeline" step 3) is absolute:

  * The IP is used ONLY here, ONLY to derive a country code (and from it the
    privacy bucket), and is then DISCARDED.
  * The IP is NEVER returned to callers, NEVER logged, NEVER written to storage.
    `country_and_bucket()` returns only a 2-letter country code and a bucket.

This module deliberately exposes no function that returns or stores an IP.
"""
from __future__ import annotations

from .config import BUCKET_GDPR, BUCKET_CCPA, BUCKET_APAC, BUCKET_OTHER

# EU/EEA + UK -> GDPR / UK GDPR.
_GDPR_COUNTRIES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
    "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
    "SI", "ES", "SE", "IS", "LI", "NO", "GB",
}

# APAC privacy regimes (APPI / PIPA / PDPA / Privacy Act / PIPL ...).
_APAC_COUNTRIES = {"JP", "KR", "SG", "AU", "NZ", "CN", "HK", "TW", "IN", "MY", "TH", "ID", "PH", "VN"}

# China-family origins fall under PIPL cross-border transfer rules.
_PIPL_COUNTRIES = {"CN"}


def country_to_bucket(country: str | None) -> str:
    """
    Map a country code to a privacy bucket. CCPA is a US-state regime; at the
    country granularity we collect, US traffic is bucketed CCPA (CPRA is the
    strictest-common US baseline and is applied conservatively to all US rows).
    """
    if not country:
        return BUCKET_OTHER
    cc = country.strip().upper()
    if cc in _GDPR_COUNTRIES:
        return BUCKET_GDPR
    if cc == "US":
        return BUCKET_CCPA
    if cc in _APAC_COUNTRIES:
        return BUCKET_APAC
    return BUCKET_OTHER


def is_pipl_origin(country: str | None) -> bool:
    """China-family origins subject to PIPL cross-border transfer restrictions."""
    return bool(country) and country.strip().upper() in _PIPL_COUNTRIES


def _lookup_country(ip: str | None) -> str | None:
    """
    Resolve an IP to a 2-letter country code. In production this is the edge's
    geo provider (Cloudflare `CF-IPCountry`, Fastly geo, MaxMind, etc.). Here we
    accept a pre-resolved country header when present and otherwise return None.

    This function never returns or retains the IP itself.
    """
    # Most CDNs hand the edge a resolved country header already; the caller
    # passes that through `country_override`. A raw-IP database lookup would slot
    # in here. We intentionally keep no IP state beyond this call frame.
    return None


def country_and_bucket(ip: str | None, country_override: str | None = None) -> tuple[str | None, str]:
    """
    Derive (country, privacy_bucket) from a request, then drop the IP.

    `country_override` is the CDN-resolved country header (preferred). If absent,
    we attempt a lookup; either way the IP is discarded when this function
    returns — nothing upstream is given the IP.

    Returns a (country_code_or_None, bucket) tuple. The bucket is always one of
    the four valid buckets.
    """
    country = (country_override or _lookup_country(ip) or "").strip().upper() or None
    # `ip` goes out of scope here and is never propagated. Do not log it.
    bucket = country_to_bucket(country)
    return country, bucket
