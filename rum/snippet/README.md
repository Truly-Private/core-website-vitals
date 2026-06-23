# LiftLog RUM snippet

The first-party Real User Monitoring snippet for the Advanced SEO Analyzer's RUM
system. **Open source on purpose** — the privacy model is "read the code", not
"trust us".

- **File:** [`liftlog-rum.js`](./liftlog-rum.js) (unminified source)
- **Size:** ~3.7 KB gzipped unminified — comfortably under the 5 KB budget
  (minify for ~2 KB).
- **Loads:** `async`, zero render-blocking. All work scheduled off the critical
  path (`PerformanceObserver`, `requestIdleCallback`, `visibilitychange` flush).

## Install

```html
<script async
        src="https://your-domain/rum/liftlog-rum.js"
        data-site="123"
        data-endpoint="https://your-domain/rum/collect"></script>
```

`data-site` is your numeric site id. `data-endpoint` defaults to `/rum/collect`
on the script's origin if omitted.

## What it collects (per page session, no cookies, no identifiers, no PII)

| Signal | Detail |
| ------ | ------ |
| LCP | value + LCP element by **tag + ARIA role only** (never id/text) |
| CLS | cumulative value + coarse shift sources (tag+role) |
| INP | value + **input delay / processing / presentation** breakdown |
| Context | device class, `connection.effectiveType`, viewport (country is derived at the edge from IP, then discarded — never sent here) |
| Behavior | click positions as viewport %, scroll depth, rage clicks (3+ rapid), dead clicks (no DOM/nav/network effect), throttled mouse movement, ordered page-path flow |

## Privacy guarantees (enforced in code)

1. **Opt-out first.** Returns immediately — collects/sends nothing — when
   `navigator.globalPrivacyControl` is true or Do Not Track is set.
2. **No PII.** Never reads element IDs, `innerText`/`textContent`, `name`,
   `value`, or any form field. Attribution is `tag` or `tag[role]` only.
3. **No durable identity.** No cookies, no `localStorage`, no fingerprinting.
   Session state is in-memory for the page lifetime only.
4. **HTTPS only.** Transmits via `sendBeacon`/`fetch` over HTTPS; refuses
   plaintext. Flushes on `visibilitychange`/`pagehide`.
5. **First-party.** Served from the customer's own domain (or our edge under
   their CNAME) — never a third-party tracker, no cross-site identity.

The edge then performs a **country-only** geo lookup from the request IP and
**discards the IP** before any write (see `rum/geo.py`).

## License

Same as the parent project (MIT) — see [`LICENSE`](../../LICENSE).
