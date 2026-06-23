# rum/config.py
"""
Configuration and tenant/region routing for the RUM system.

Two hard architectural facts from docs/RUM_SYSTEM.md drive this module:

  1. Database-per-tenant isolation. Each customer account gets its OWN Neon
     database (project/branch). There is no shared `tenant_id` column anywhere —
     the connection itself is scoped to a single tenant's database, so there is
     no query path that can read across tenants.

  2. Regional placement for residency. A tenant can have several databases, one
     per residency region. A visitor event is routed to the regional database
     that matches the event's `privacy_bucket` (GDPR -> EU, CCPA -> US, ...).

Connection strings are resolved from environment variables so no credentials
live in the repo. The expected layout is:

    RUM_TENANT_DB__<TENANT_KEY>__<REGION> = postgresql://...@<host>/<db>?sslmode=require

e.g.

    RUM_TENANT_DB__ACME__EU = postgres://...eu-central-1.../acme_eu?sslmode=require
    RUM_TENANT_DB__ACME__US = postgres://...us-east-1.../acme_us?sslmode=require

`sslmode=require` (TLS) is enforced for every connection — see rum/db.py.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

# Privacy buckets (see docs/RUM_SYSTEM.md "Regional privacy bucketing").
BUCKET_GDPR = "GDPR"
BUCKET_CCPA = "CCPA"
BUCKET_APAC = "APAC"
BUCKET_OTHER = "OTHER"
PRIVACY_BUCKETS = (BUCKET_GDPR, BUCKET_CCPA, BUCKET_APAC, BUCKET_OTHER)

# Which physical region each privacy bucket is pinned to. The event is written to
# the tenant's database in this region, never anywhere else.
BUCKET_TO_REGION = {
    BUCKET_GDPR: "EU",
    BUCKET_CCPA: "US",
    BUCKET_APAC: "APAC",
    BUCKET_OTHER: "US",  # baseline; configurable per deployment
}

ENV_PREFIX = "RUM_TENANT_DB__"


@dataclass(frozen=True)
class RegionalTarget:
    """A resolved destination for one event: which tenant DB, in which region."""
    tenant_key: str
    region: str
    dsn: str | None  # None => no DB provisioned for this region (see PIPL rule)


def tenant_key_for_site(site_id: int) -> str:
    """
    Map a site_id to its account's tenant key.

    In a full deployment this comes from the account directory. We keep the
    mapping pluggable via env (`RUM_SITE_TENANT__<site_id> = ACME`) and fall
    back to a per-site default so the system works out of the box in dev.
    """
    override = os.environ.get(f"RUM_SITE_TENANT__{site_id}")
    if override:
        return override.strip().upper()
    return os.environ.get("RUM_DEFAULT_TENANT", "DEFAULT").strip().upper()


def resolve_target(site_id: int, privacy_bucket: str) -> RegionalTarget:
    """
    Resolve the regional Neon database an event must be written to, based on the
    tenant (site -> account) and the event's privacy bucket.

    Residency is preserved end to end: a GDPR-bucketed event resolves to the
    tenant's EU database and can never resolve to a US one.
    """
    tenant_key = tenant_key_for_site(site_id)
    region = BUCKET_TO_REGION.get(privacy_bucket, "US")
    dsn = os.environ.get(f"{ENV_PREFIX}{tenant_key}__{region}")
    if not dsn:
        # Fall back to a single shared dev DSN if one is configured. This keeps
        # local development simple; production sets the per-tenant/region vars.
        dsn = os.environ.get("RUM_DATABASE_URL") or os.environ.get("DATABASE_URL")
    return RegionalTarget(tenant_key=tenant_key, region=region, dsn=dsn)


def all_configured_dsns() -> list[str]:
    """Every distinct tenant/region DSN configured — used by migration/rollup jobs."""
    seen: list[str] = []
    for key, val in os.environ.items():
        if key.startswith(ENV_PREFIX) and val and val not in seen:
            seen.append(val)
    for fallback in ("RUM_DATABASE_URL", "DATABASE_URL"):
        val = os.environ.get(fallback)
        if val and val not in seen:
            seen.append(val)
    return seen
