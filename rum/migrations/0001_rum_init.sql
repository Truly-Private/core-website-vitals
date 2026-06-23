-- ============================================================================
-- RUM system — initial schema (migration 0001)
-- ----------------------------------------------------------------------------
-- IMPORTANT: this migration runs INSIDE a single tenant's isolated Neon
-- database. There is intentionally NO tenant_id column anywhere — the database
-- itself is the tenant boundary (see docs/RUM_SYSTEM.md, "Database, isolation &
-- regional privacy bucketing"). A given tenant may have several of these
-- databases, one per residency region (EU / US / APAC); the same DDL is applied
-- to each regional database.
--
-- Every row carries a `privacy_bucket` (GDPR | CCPA | APAC | OTHER) derived from
-- the country-only edge geo lookup. The IP is discarded at the edge and never
-- reaches any table here.
-- ============================================================================

-- Minimal `sites` table. The existing product is stateless; RUM is the first
-- feature that persists data, so we bootstrap the sites table the FKs reference.
-- (If a richer sites table already exists in the tenant DB this is a no-op.)
CREATE TABLE IF NOT EXISTS sites (
    id          BIGSERIAL PRIMARY KEY,
    domain      TEXT NOT NULL,
    -- Pricing tier gates which RUM features collect/render. See rum/pricing.py.
    tier        TEXT NOT NULL DEFAULT 'free',   -- free | pro | agency
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_sites_domain ON sites (domain);

-- ----------------------------------------------------------------------------
-- rum_events — per-pageview raw data. Short retention (see Pricing).
-- Sensitive payloads (`behavior`, `cls_sources`) are written as application-layer
-- ciphertext (per-tenant envelope encryption); coarse aggregate/index columns
-- stay plaintext so rollups and residency routing work without decryption.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rum_events (
    id              BIGSERIAL PRIMARY KEY,
    site_id         BIGINT NOT NULL REFERENCES sites(id),
    page_path       TEXT   NOT NULL,
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    privacy_bucket  TEXT   NOT NULL,   -- GDPR | CCPA | APAC | OTHER (from edge geo)

    -- Core Web Vitals (per pageview)
    lcp_ms          INTEGER,
    cls             NUMERIC(6,4),
    inp_ms          INTEGER,

    -- INP three-part breakdown (the headline diagnostic)
    inp_input_delay_ms    INTEGER,
    inp_processing_ms     INTEGER,
    inp_presentation_ms   INTEGER,

    -- CWV attribution / context (all coarse, no PII)
    lcp_element     TEXT,          -- coarse tag+role only, never id/text
    cls_sources     JSONB,         -- coarse shift attribution (encrypted payload)
    device_class    TEXT,          -- mobile | tablet | desktop
    connection_type TEXT,          -- 4g | 3g | slow-2g | ...
    country         CHAR(2),       -- country-only; IP already discarded
    viewport_w      INTEGER,
    viewport_h      INTEGER,

    -- Behavioral data (clicks, scroll, rage/dead, movement, flow).
    -- Stored as an application-encrypted envelope (operator-blind).
    behavior        JSONB
);

CREATE INDEX IF NOT EXISTS idx_rum_events_site_time   ON rum_events (site_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_rum_events_site_page   ON rum_events (site_id, page_path);
CREATE INDEX IF NOT EXISTS idx_rum_events_behavior    ON rum_events USING GIN (behavior);

-- ----------------------------------------------------------------------------
-- rum_rollups — hourly / daily / weekly aggregations. Long retention, fast reads.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rum_rollups (
    id              BIGSERIAL PRIMARY KEY,
    site_id         BIGINT NOT NULL REFERENCES sites(id),
    page_path       TEXT   NOT NULL,
    bucket          TEXT   NOT NULL,   -- 'hour' | 'day' | 'week'
    bucket_start    TIMESTAMPTZ NOT NULL,
    privacy_bucket  TEXT   NOT NULL,   -- GDPR | CCPA | APAC | OTHER
    sample_count    INTEGER NOT NULL,

    -- Percentile distributions (p50 / p75 / p95) per metric
    lcp_p50 INTEGER, lcp_p75 INTEGER, lcp_p95 INTEGER,
    cls_p50 NUMERIC(6,4), cls_p75 NUMERIC(6,4), cls_p95 NUMERIC(6,4),
    inp_p50 INTEGER, inp_p75 INTEGER, inp_p95 INTEGER,

    -- INP breakdown (p75 of each component)
    inp_input_delay_p75   INTEGER,
    inp_processing_p75    INTEGER,
    inp_presentation_p75  INTEGER,

    -- Heatmap grid + behavior summaries (binned/aggregated — safe to keep plaintext
    -- because they are statistical and carry no per-session detail).
    heatmap_grid    JSONB,   -- binned click/scroll/movement densities
    behavior_summary JSONB,  -- rage/dead click counts, scroll depth dist, flows

    UNIQUE (site_id, page_path, bucket, bucket_start, privacy_bucket)
);

CREATE INDEX IF NOT EXISTS idx_rum_rollups_lookup ON rum_rollups (site_id, bucket, bucket_start DESC);
CREATE INDEX IF NOT EXISTS idx_rum_rollups_page   ON rum_rollups (site_id, page_path, bucket, bucket_start DESC);

-- ----------------------------------------------------------------------------
-- schema_migrations — tracks applied migrations within this tenant DB.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     TEXT PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
INSERT INTO schema_migrations (version) VALUES ('0001_rum_init')
    ON CONFLICT (version) DO NOTHING;
