# rum/pricing.py
"""
Pricing tiers and feature gates for RUM (docs/RUM_SYSTEM.md, "Pricing").

  Free   — no RUM at all (lab audits + CrUX only).
  Pro    — RUM + click/scroll heatmaps + rage/dead click detection;
           24h raw retention, 90-day rollups; site-level breakdowns.
  Agency — everything in Pro + movement heatmaps + session flow +
           page-level breakdowns; 7-day raw retention.

Gates are enforced in two directions:
  * Ingest: features the tier doesn't include are stripped from the payload
    before write, so we never store data a customer isn't entitled to collect.
  * Dashboard: features the tier doesn't include are hidden/locked.
"""
from __future__ import annotations

from dataclasses import dataclass, field

FREE = "free"
PRO = "pro"
AGENCY = "agency"

# Capability flags.
CAP_RUM = "rum"
CAP_CWV = "cwv_inp_breakdown"
CAP_CLICK_HEATMAP = "click_heatmap"
CAP_SCROLL_HEATMAP = "scroll_heatmap"
CAP_RAGE = "rage_clicks"
CAP_DEAD = "dead_clicks"
CAP_MOVEMENT = "movement_heatmap"
CAP_SESSION_FLOW = "session_flow"
CAP_PAGE_BREAKDOWN = "page_breakdown"


@dataclass(frozen=True)
class Tier:
    name: str
    capabilities: frozenset
    raw_retention_hours: int           # rum_events retention
    rollup_retention_days: int         # rum_rollups retention

    def has(self, capability: str) -> bool:
        return capability in self.capabilities


_PRO_CAPS = {
    CAP_RUM, CAP_CWV, CAP_CLICK_HEATMAP, CAP_SCROLL_HEATMAP, CAP_RAGE, CAP_DEAD,
}
_AGENCY_CAPS = _PRO_CAPS | {CAP_MOVEMENT, CAP_SESSION_FLOW, CAP_PAGE_BREAKDOWN}

TIERS = {
    FREE: Tier(FREE, frozenset(), raw_retention_hours=0, rollup_retention_days=0),
    PRO: Tier(PRO, frozenset(_PRO_CAPS), raw_retention_hours=24, rollup_retention_days=90),
    # "90-day+" — Agency keeps rollups at least as long as Pro.
    AGENCY: Tier(AGENCY, frozenset(_AGENCY_CAPS), raw_retention_hours=24 * 7, rollup_retention_days=180),
}


def get_tier(name: str | None) -> Tier:
    return TIERS.get((name or FREE).strip().lower(), TIERS[FREE])


def gate_behavior_for_tier(behavior: dict, tier: Tier) -> dict:
    """
    Strip behavioral signals the tier isn't entitled to, BEFORE write.

      * Movement heatmaps  -> Agency only (drop `moves` below Agency).
      * Session flow        -> Agency only (drop `flow` below Agency).
    Click/scroll/rage/dead are included from Pro up.
    """
    if not isinstance(behavior, dict):
        return {}
    b = dict(behavior)
    if not tier.has(CAP_MOVEMENT):
        b.pop("moves", None)
    if not tier.has(CAP_SESSION_FLOW):
        b.pop("flow", None)
    if not tier.has(CAP_CLICK_HEATMAP):
        b.pop("clicks", None)
    if not tier.has(CAP_SCROLL_HEATMAP):
        b.pop("scroll_max", None)
        b.pop("scroll_milestones", None)
    if not tier.has(CAP_RAGE):
        b.pop("rage", None)
    if not tier.has(CAP_DEAD):
        b.pop("dead", None)
    return b
