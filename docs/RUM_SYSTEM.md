---

# Brand Identity

The Real User Monitoring (RUM) system extends the Advanced SEO Analyzer / Core
Web Vitals platform from a point-in-time *lab* auditor into a continuous *field*
measurement product. The brand promise is simple and uncompromising:

> **Real performance data from real users — without tracking a single one of them.**

Three principles drive every design decision in this document:

1. **Field data beats lab data.** A synthetic audit tells you how a page *could*
   perform on one machine, one network, one moment. RUM tells you how it
   *actually* performs across every device, network, and geography your real
   visitors bring.
2. **Instant beats eventual.** Google's CrUX dataset is the industry baseline,
   but it is a 28-day trailing average that excludes low-traffic pages
   entirely. Our RUM gives users their own field data *today*, on *every* page,
   starting with the first visitor after install.
3. **Privacy is not a feature, it is the foundation.** The snippet collects zero
   PII, sets zero cookies, and performs zero cross-site tracking. It is the only
   way to build trust with the people whose browsers do the measuring.

---

# Why RUM (and why now)

| Dimension            | Lab audit (existing)        | CrUX field data            | LiftLog RUM (this spec)              |
| -------------------- | --------------------------- | -------------------------- | ------------------------------------ |
| Data source          | One synthetic run           | Aggregated Chrome users    | Your real visitors, all browsers     |
| Freshness            | On demand                   | 28-day trailing average    | Real-time, per session               |
| Page coverage        | Pages you audit             | Only high-traffic URLs     | Every page that gets a pageview      |
| Time to first data   | Seconds (one machine)       | ~28 days, if eligible      | First visitor after install          |
| Diagnostic depth     | Full waterfall, one device  | Distribution only          | Per-session CWV + behavior + INP breakdown |
| Privacy posture      | N/A (no visitors involved)  | Google's aggregation       | Cookie-free, PII-free, first-party   |

CrUX answers "are we in the green?" 28 days late, for popular pages only. RUM
answers "*why* are we not in the green, on *this* page, for *these* devices,
*right now*?"

---

# The RUM snippet

A first-party JavaScript snippet that users install on their own sites. It is the
data-collection edge of the entire system.

## Design constraints

- **`< 5KB gzipped`.** Performance monitoring must never become a performance
  problem. The snippet is the budget.
- **First-party.** Served from the customer's own domain (or our edge under their
  CNAME), so it is never blocked as a third-party tracker and never participates
  in cross-site identity.
- **Zero render-blocking.** Loaded `async`, all work scheduled off the critical
  path (`requestIdleCallback`, `visibilitychange` flush, `sendBeacon`).
- **Open source.** The full, unminified snippet source is published on GitHub so
  anyone — auditors, customers, regulators — can verify exactly what it does.
  "Trust us" is not in the privacy model; "read the code" is.

## What it collects

### Core Web Vitals — all three, in real time, per session

- **LCP** (Largest Contentful Paint) with the **LCP element** identified (by tag
  + role, never by text content or ID — see Privacy).
- **CLS** (Cumulative Layout Shift) with **CLS source** attribution (which layout
  shift sessions contribute most).
- **INP** (Interaction to Next Paint) with the full **three-part breakdown**:

  | Component         | What it measures                                  | What a high value means                         |
  | ----------------- | ------------------------------------------------- | ----------------------------------------------- |
  | Input delay       | Time from interaction to event handler start      | Main thread busy — defer/​chunk JS               |
  | Processing time   | Time spent running event handlers                 | Handler is doing too much — optimize the work    |
  | Presentation delay| Time from handler end to next frame painted       | Rendering/layout cost — simplify the DOM update  |

  The breakdown is the headline diagnostic value: it tells users *where* in the
  interaction lifecycle the bottleneck lives, instead of a single opaque number.

Supporting CWV diagnostics also captured per session: device class, effective
connection type (`navigator.connection.effectiveType`), viewport size, and
country (country-only, see Privacy).

### Behavioral signals (for heatmaps & UX diagnostics)

- **Click positions** recorded as **viewport percentages** (x%, y%), never as
  element identifiers — so heatmaps render correctly across viewport sizes and
  reveal nothing about the DOM.
- **Scroll depth** — maximum scroll reached, sampled milestones.
- **Rage clicks** — 3+ rapid clicks in a small region = a frustration signal,
  usually a non-responsive or misleading element.
- **Dead clicks** — a click that produced no DOM change, navigation, or network
  request = the user expected something to happen and nothing did.
- **Mouse movement sampling** — throttled coordinate sampling for movement
  heatmaps (Agency tier only).
- **Session flow paths** — the ordered sequence of pages in a session, for the
  session flow diagram. Path only; no user identity.

Every behavioral signal is positional or statistical. **Not one byte of PII** is
collected.

---

# Privacy pipeline

This is the non-negotiable core. The pipeline is designed so that PII *cannot*
reach storage even if we wanted it to.

1. **No cookies. No local storage identifiers. No fingerprinting.** Sessions are
   stitched in-memory for the lifetime of the page session only and are never
   persisted to a device. There is no cross-page-load durable identifier.
2. **No cross-site tracking.** First-party only; the snippet has no concept of a
   global user and cannot correlate visits across domains.
3. **IP handling — stripped at the edge.** The visitor IP is used *only* at the
   ingestion edge to perform a **country-only** geo lookup (which also yields the
   `privacy_bucket` — see *Database, isolation & regional privacy bucketing*),
   and is then **discarded** before the event is written. The IP never lands in
   `rum_events`, never lands in logs, never lands in rollups. Storage only ever
   sees a country code and its derived privacy bucket.
4. **No element IDs, no text content, no form values.** The snippet never reads
   `innerText`, never reads input/textarea/select values, never serializes
   element IDs or class names that could carry semantic/PII content. LCP/CLS
   attribution uses coarse tag+role descriptors only.
5. **Respects `globalPrivacyControl` and DNT.** If `navigator.globalPrivacyControl`
   is true, or the legacy `navigator.doNotTrack` signal is set, the snippet
   collects nothing and sends nothing.
6. **Cookie-free → no consent banner in most jurisdictions.** Because the system
   sets no cookies, stores no device identifiers, and processes no PII, it falls
   outside the ePrivacy "cookie consent" requirement and GDPR personal-data
   processing in most jurisdictions. (Customers remain responsible for their own
   legal posture; we provide a DPA and the open-source proof.)
7. **Open-source script.** The snippet source is published on GitHub. The privacy
   claims above are independently verifiable line by line.

> Design rule of thumb: if a signal could ever, in combination with others,
> single out an individual, it does not get collected.

---

# Dashboard

Two new tabs are added to the site detail page.

## Tab: "Real Users"

Field data sourced entirely from RUM (distinct from the lab-audit and CrUX views):

- **Live CWV gauges** — LCP, CLS, INP from RUM, with good/needs-improvement/poor
  thresholds and the p75 value (the metric Google scores on).
- **INP breakdown visualization** — the input delay / processing / presentation
  split rendered as a stacked bar (`<INPBreakdownBar>`).
- **LCP element tracking** — which element is the LCP across sessions, and how its
  timing varies by device/connection.
- **CLS source tracking** — which shifts contribute most of the cumulative score.
- **Device / connection breakdown** — CWV distributions segmented by device class
  and effective connection type.
- **Per-page performance table** — every page that received a pageview, with its
  own p75 CWV, sortable to find the worst offenders.
- **RUM vs CrUX comparison badges** — `<RUMvsCruxComparison>` showing where the
  customer's own field data agrees with or diverges from the 28-day CrUX average
  (divergence usually means recent changes CrUX hasn't caught up to yet).

## Tab: "Heatmaps"

Behavioral visualization overlaid on **server-captured page screenshots** via
canvas rendering:

- **Click heatmap** — click density rendered from viewport-percentage positions.
- **Scroll heatmap** — how far down the page users actually get.
- **Movement heatmap** — sampled mouse movement (Agency tier).
- **Rage click hotspots** — highlighted regions of repeated frustrated clicking.
- **Dead click detection** — clicked elements that did nothing, flagged inline.
- **Scroll depth visualization** — `<ScrollDepthGauge>` showing the fold/​depth
  distribution.
- **Session flow diagrams** — `<SessionFlowDiagram>` showing the common page
  paths visitors take through the site.

Heatmaps overlay on screenshots we capture server-side, so we never need the
visitor's DOM or any client-rendered content to reconstruct the page.

---

# Database, isolation & regional privacy bucketing

## Engine: Neon (serverless Postgres)

The RUM store runs on **Neon**. Neon is chosen specifically because it makes
the isolation and residency model below cheap and instant:

- **Database-per-tenant isolation.** Every customer account gets its **own Neon
  database** (its own project/branch), not a shared multi-tenant table with a
  `tenant_id` column. A customer's RUM data is physically separated from every
  other customer's. There is no query path — accidental or malicious — that can
  read across tenants, because the connection is scoped to one tenant's database.
- **Instant, cheap provisioning.** Neon projects/branches are created on demand,
  so onboarding a new customer (or a new region for an existing customer) is an
  API call, not a migration. Scale-to-zero means idle tenants cost almost nothing.
- **Regional placement for residency.** Neon projects are pinned to a specific
  cloud region. We provision a tenant's database (or a regional shard of it) in
  the region that satisfies its data-residency obligations — EU data stays in an
  EU region, and so on.

```
Account (customer)
└── Neon project (isolated)
    ├── db in EU region        → GDPR-bucketed visitor data
    ├── db in US region        → CCPA/CPRA-bucketed visitor data
    └── db in APAC region      → APAC-regime visitor data
```

## Encryption

Encryption is applied at three layers so that data is protected on the wire, on
disk, and against the database operator itself.

- **In transit (TLS everywhere).** The snippet → edge → Neon path is TLS 1.3 end
  to end. Beacons use `sendBeacon`/`fetch` over HTTPS only; the edge connects to
  Neon over TLS. No plaintext hop exists anywhere in the pipeline.
- **Encryption at rest.** Neon encrypts all stored data (database pages, WAL, and
  backups) at rest with **AES-256** by default. This covers every tenant database
  and every regional shard automatically.
- **End-to-end / application-layer encryption (operator-blind).** On top of
  at-rest encryption, sensitive RUM payloads are encrypted **in the application,
  before they are written to Neon**, using **envelope encryption**:
  - A central **KMS** holds a per-tenant root key (CMK). Each tenant has its own
    key, so cross-tenant decryption is impossible even with full DB access.
  - The edge encrypts the event's sensitive fields/JSONB (`behavior`,
    attribution detail) with a tenant data key wrapped by the tenant CMK. Neon
    stores only ciphertext for those fields; the database — and anyone with
    direct DB or backup access, including Neon operators and us — sees only
    ciphertext.
  - Decryption happens only in the application tier when rendering the dashboard
    for an authenticated, authorized member of that tenant.
  - Coarse, non-sensitive aggregate columns used for indexing/rollups (e.g.
    `lcp_p75`, `country`, `privacy_bucket`, timestamps) remain queryable in
    plaintext so percentile rollups and residency routing work without
    decrypting per-row payloads.
  - **Key rotation & deletion:** rotating a tenant CMK re-wraps data keys without
    rewriting ciphertext; destroying a tenant CMK cryptographically shreds that
    tenant's data (crypto-erase), which is also how regime-driven deletion is
    honored.

Per-tenant keys reinforce the database-per-tenant isolation: isolation prevents
cross-tenant *queries*, and per-tenant E2E keys make cross-tenant *plaintext*
unrecoverable even if isolation were bypassed.

## Regional privacy bucketing of visitors

Within a tenant's isolated database, each RUM event is **bucketed by the
visitor's region** so the correct privacy regime is applied per record. The
region is derived from the **country-only** geo lookup performed at the edge —
the same lookup after which the IP is discarded. No additional data is collected
to determine the bucket.

| Bucket   | Covers (examples)                                  | Regime drivers                          |
| -------- | -------------------------------------------------- | --------------------------------------- |
| `GDPR`   | EU/EEA + UK (UK GDPR)                               | GDPR / ePrivacy                         |
| `CCPA`   | California (and CPRA)                               | CCPA / CPRA                             |
| `APAC`   | e.g. Japan (APPI), South Korea (PIPA), Singapore (PDPA), Australia (Privacy Act), China (PIPL — see note) | Regional APAC laws |
| `OTHER`  | Everywhere else                                     | Baseline (our strictest-common policy)  |

The bucket is stored on the event/rollup (`privacy_bucket`) and drives:

- **Retention** — the bucket can shorten raw/rollup retention below the tier
  default where a regime requires it.
- **Residency** — the bucket determines *which regional database* the event is
  written to (e.g. a GDPR-bucketed event lands in the tenant's EU-region Neon
  database, never a US one).
- **Processing rules** — any regime-specific handling (e.g. honoring regional
  opt-out signals) keys off the bucket.

Because the system is already cookie-free and PII-free, bucketing is about
*residency and retention correctness*, not about gating personal-data
collection that we never do in the first place.

> **PIPL / China note:** cross-border transfer rules are strict; China-bucketed
> traffic, where served, is kept in-region and is not transferred out. If a
> tenant has no in-region database provisioned, China-origin events are dropped
> rather than transferred.

## Implications for the snippet & edge

- The edge still discards the IP immediately after deriving **country only**.
- Country → `privacy_bucket` mapping happens at the edge; the visitor IP is never
  needed again and never stored.
- The edge routes the event to the correct **regional Neon database** for that
  tenant based on the bucket, preserving residency end to end.

---

# Data model

Two new tables. These live inside **each tenant's isolated Neon database** (and,
where residency requires, are physically split across the tenant's regional
databases). There is intentionally no `tenant_id` column — the *database itself*
is the tenant boundary. Each row carries a `privacy_bucket` for regime-correct
retention and processing.

## `rum_events` — per-pageview raw data

One row per pageview. Short retention (see Pricing). Holds the full CWV
measurements, the INP breakdown, and behavioral data as JSONB.

```sql
CREATE TABLE rum_events (
    id              BIGSERIAL PRIMARY KEY,
    site_id         BIGINT NOT NULL REFERENCES sites(id),
    page_path       TEXT   NOT NULL,
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    privacy_bucket  TEXT   NOT NULL,   -- GDPR | CCPA | APAC | OTHER (from edge geo)

    -- Core Web Vitals (per pageview)
    lcp_ms          INTEGER,
    cls             NUMERIC(6,4),
    inp_ms          INTEGER,

    -- INP three-part breakdown
    inp_input_delay_ms    INTEGER,
    inp_processing_ms     INTEGER,
    inp_presentation_ms   INTEGER,

    -- CWV attribution / context
    lcp_element     TEXT,          -- coarse tag+role only, never id/text
    cls_sources     JSONB,         -- coarse shift attribution
    device_class    TEXT,          -- mobile | tablet | desktop
    connection_type TEXT,          -- 4g | 3g | slow-2g | ...
    country         CHAR(2),       -- country-only; IP already discarded
    viewport_w      INTEGER,
    viewport_h      INTEGER,

    -- Behavioral data (clicks, scroll, rage/dead, movement, flow)
    behavior        JSONB
);

CREATE INDEX idx_rum_events_site_time   ON rum_events (site_id, occurred_at DESC);
CREATE INDEX idx_rum_events_site_page   ON rum_events (site_id, page_path);
CREATE INDEX idx_rum_events_behavior    ON rum_events USING GIN (behavior);
```

## `rum_rollups` — hourly / daily / weekly aggregations

Pre-aggregated for fast dashboard queries and long retention. Stores percentile
distributions, heatmap grid data, and behavior summaries.

```sql
CREATE TABLE rum_rollups (
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

    -- INP breakdown medians
    inp_input_delay_p75   INTEGER,
    inp_processing_p75    INTEGER,
    inp_presentation_p75  INTEGER,

    -- Heatmap grid + behavior summaries
    heatmap_grid    JSONB,   -- binned click/scroll/movement densities
    behavior_summary JSONB,  -- rage/dead click counts, scroll depth dist, flows

    UNIQUE (site_id, page_path, bucket, bucket_start, privacy_bucket)
);

CREATE INDEX idx_rum_rollups_lookup ON rum_rollups (site_id, bucket, bucket_start DESC);
CREATE INDEX idx_rum_rollups_page   ON rum_rollups (site_id, page_path, bucket, bucket_start DESC);
```

---

# Components

New UI components added to the component list:

| Component                  | Purpose                                                              |
| -------------------------- | ------------------------------------------------------------------- |
| `<INPBreakdownBar>`        | Stacked bar of input delay / processing / presentation              |
| `<RUMvsCruxComparison>`    | Badge comparing own RUM field data against 28-day CrUX              |
| `<HeatmapOverlay>`         | Canvas-based heatmap rendered over a server-captured screenshot      |
| `<RageClickAlert>`         | Flags regions with repeated frustrated clicking                      |
| `<DeadClickAlert>`         | Flags clicked elements that produced no effect                       |
| `<ScrollDepthGauge>`       | Visualizes how far down the page users scroll                        |
| `<RUMInstallSnippet>`      | Copy-paste install UI for the first-party snippet                    |
| `<SessionFlowDiagram>`     | Diagram of common page paths through the site                        |

---

# Pricing

RUM features by tier:

| Capability                          | Free | Pro                          | Agency                          |
| ----------------------------------- | :--: | ---------------------------- | ------------------------------- |
| RUM data collection                 |  ✗   | ✓                            | ✓                               |
| Real-user Core Web Vitals + INP breakdown | ✗ | ✓                          | ✓                               |
| Click heatmaps                      |  ✗   | ✓                            | ✓                               |
| Scroll heatmaps                     |  ✗   | ✓                            | ✓                               |
| Rage-click detection                |  ✗   | ✓                            | ✓                               |
| Dead-click detection                |  ✗   | ✓                            | ✓                               |
| Movement heatmaps                   |  ✗   | ✗                            | ✓                               |
| Session flow diagrams               |  ✗   | ✗                            | ✓                               |
| Page-level breakdowns               |  ✗   | (site-level)                 | ✓ (per page)                    |
| Raw event retention (`rum_events`)  |  —   | 24 hours                     | 7 days                          |
| Rollup retention (`rum_rollups`)    |  —   | 90 days                      | 90 days+                        |

- **Free** — no RUM. Lab audits and CrUX only.
- **Pro** — RUM + click/scroll heatmaps + rage/dead click detection. 24-hour raw
  retention, 90-day rollups.
- **Agency** — everything in Pro, plus movement heatmaps, session flow diagrams,
  page-level breakdowns, and 7-day raw retention.

---

# Privacy section (customer-facing summary)

The existing privacy section now references RUM explicitly:

- We collect real-user performance and behavior data **without any PII**.
- **No cookies**, no device identifiers, no fingerprinting, no cross-site tracking.
- Visitor IPs are used only for a **country-only** lookup at the edge and are then
  **discarded** — they never reach storage.
- We never read element IDs, page text content, or form values.
- We respect **Global Privacy Control** and **Do Not Track**.
- Data is **encrypted in transit (TLS 1.3)**, **at rest (AES-256)**, and with
  **per-tenant end-to-end encryption** so sensitive payloads are unreadable even
  to the database operator.
- Because we set no cookies and process no personal data, **no consent banner is
  required** in most jurisdictions.
- The collection snippet is **open source** — verify every claim yourself.
