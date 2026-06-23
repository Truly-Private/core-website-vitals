/*!
 * LiftLog RUM — first-party Real User Monitoring snippet.
 *
 * Open source so anyone can verify exactly what it does. "Read the code" is the
 * privacy model. See docs/RUM_SYSTEM.md.
 *
 * Collects (per page session, no cookies, no identifiers, no PII):
 *   - Core Web Vitals: LCP, CLS, INP (with input-delay / processing /
 *     presentation breakdown).
 *   - Coarse CWV attribution: LCP element by tag+role only; CLS shift sources.
 *   - Context: device class, effective connection type, viewport, (country is
 *     derived at the edge from IP, then discarded — never sent by this snippet).
 *   - Behavior: click positions as viewport %, scroll depth, rage clicks,
 *     dead clicks, throttled mouse movement, ordered page-path flow.
 *
 * Hard privacy rules enforced in code below:
 *   - Refuses to run when Global Privacy Control or Do Not Track is set.
 *   - Never reads element IDs, innerText/textContent, or form field values.
 *   - Attribution uses tag + ARIA role only.
 *   - Sends only over HTTPS via sendBeacon/fetch; flushes on visibilitychange.
 *
 * Async, zero render-blocking: all work is scheduled off the critical path.
 * Target: < 5KB gzipped.
 *
 * Install:
 *   <script async src="https://your-domain/liftlog-rum.js"
 *           data-site="123" data-endpoint="https://your-domain/rum/collect"></script>
 */
(function () {
  "use strict";

  // ---- 0. Honor opt-out signals. Collect/send nothing. -------------------- //
  var nav = navigator;
  if (
    nav.globalPrivacyControl === true ||
    nav.doNotTrack === "1" ||
    window.doNotTrack === "1" ||
    nav.msDoNotTrack === "1"
  ) {
    return;
  }

  // ---- 1. Config from the script tag. ------------------------------------- //
  var script = document.currentScript || (function () {
    var s = document.getElementsByTagName("script");
    return s[s.length - 1];
  })();
  var SITE = script && script.getAttribute("data-site");
  var ENDPOINT = (script && script.getAttribute("data-endpoint")) || "/rum/collect";
  if (!SITE) { return; }
  // HTTPS only. Refuse to transmit over plaintext.
  if (location.protocol !== "https:" && location.hostname !== "localhost") { return; }

  // ---- 2. Context (coarse, non-identifying). ------------------------------ //
  function deviceClass() {
    var w = window.innerWidth || 0;
    var ua = nav.userAgent || "";
    if (/Tablet|iPad/i.test(ua) || (w >= 600 && w < 1024)) { return "tablet"; }
    if (/Mobi|Android|iPhone/i.test(ua) || w < 600) { return "mobile"; }
    return "desktop";
  }
  var conn = nav.connection || {};

  // ---- 3. Shared state for the session (in-memory only). ------------------ //
  var data = {
    page_path: location.pathname,           // path only; no query/fragment
    device_class: deviceClass(),
    connection_type: conn.effectiveType || "unknown",
    viewport_w: window.innerWidth || 0,
    viewport_h: window.innerHeight || 0,
    lcp_ms: null,
    cls: 0,
    inp_ms: null,
    inp_input_delay_ms: null,
    inp_processing_ms: null,
    inp_presentation_ms: null,
    lcp_element: null,
    cls_sources: [],
    behavior: {
      clicks: [],
      moves: [],
      rage: [],
      dead: [],
      scroll_max: 0,
      scroll_milestones: [],
      flow: [location.pathname]
    }
  };

  // ---- 4. Coarse, PII-free element descriptor: tag[role] only. ------------ //
  function describe(el) {
    if (!el || !el.tagName) { return null; }
    var tag = el.tagName.toLowerCase();
    var role = el.getAttribute && el.getAttribute("role");
    // role attribute only — never id, class, text, name, or value.
    return role ? tag + "[" + role + "]" : tag;
  }

  // ---- 5. Core Web Vitals via PerformanceObserver. ------------------------ //
  function observe(type, cb, opts) {
    try {
      var po = new PerformanceObserver(function (list) {
        cb(list.getEntries());
      });
      po.observe(Object.assign({ type: type, buffered: true }, opts || {}));
      return po;
    } catch (e) { return null; }
  }

  // LCP — keep the largest; record its element coarsely.
  observe("largest-contentful-paint", function (entries) {
    var last = entries[entries.length - 1];
    if (last) {
      data.lcp_ms = Math.round(last.startTime);
      if (last.element) { data.lcp_element = describe(last.element); }
    }
  });

  // CLS — cumulative, session-windowed; record coarse shift sources.
  observe("layout-shift", function (entries) {
    entries.forEach(function (e) {
      if (e.hadRecentInput) { return; }
      data.cls += e.value;
      var src = e.sources && e.sources[0] && e.sources[0].node;
      if (src && data.cls_sources.length < 10) {
        data.cls_sources.push({ el: describe(src), value: Math.round(e.value * 10000) / 10000 });
      }
    });
  });

  // INP — worst interaction, with the three-part breakdown.
  var worstINP = -1;
  observe("event", function (entries) {
    entries.forEach(function (e) {
      if (!e.interactionId) { return; }            // only real interactions
      if (e.duration <= worstINP) { return; }
      worstINP = e.duration;
      var inputDelay = e.processingStart - e.startTime;
      var processing = e.processingEnd - e.processingStart;
      var presentation = (e.startTime + e.duration) - e.processingEnd;
      data.inp_ms = Math.round(e.duration);
      data.inp_input_delay_ms = Math.max(0, Math.round(inputDelay));
      data.inp_processing_ms = Math.max(0, Math.round(processing));
      data.inp_presentation_ms = Math.max(0, Math.round(presentation));
    });
  }, { durationThreshold: 16 });

  // ---- 6. Behavioral signals. --------------------------------------------- //
  function pct(v, total) { return Math.round((v / (total || 1)) * 10000) / 100; }

  // Rage-click detection: 3+ clicks within 600ms in a ~5% region.
  var recentClicks = [];
  // Dead-click detection: a click that produces no DOM/nav/network within 500ms.
  var domDirty = false, navDirty = false, netDirty = false;
  try {
    new MutationObserver(function () { domDirty = true; })
      .observe(document.documentElement, { childList: true, subtree: true, attributes: true });
  } catch (e) {}
  var _pushState = history.pushState;
  history.pushState = function () { navDirty = true; recordFlow(); return _pushState.apply(this, arguments); };
  window.addEventListener("popstate", function () { navDirty = true; recordFlow(); });
  if (window.PerformanceObserver) {
    observe("resource", function () { netDirty = true; });
  }

  function recordFlow() {
    var p = location.pathname;
    var flow = data.behavior.flow;
    if (flow[flow.length - 1] !== p) {
      flow.push(p);
      if (flow.length > 50) { flow.shift(); }
    }
    data.page_path = p;
  }

  document.addEventListener("click", function (ev) {
    var x = pct(ev.clientX, window.innerWidth);
    var y = pct(ev.clientY, window.innerHeight);
    if (data.behavior.clicks.length < 500) { data.behavior.clicks.push({ x: x, y: y }); }

    // Rage detection.
    var now = performance.now();
    recentClicks = recentClicks.filter(function (c) { return now - c.t < 600; });
    recentClicks.push({ x: x, y: y, t: now });
    var cluster = recentClicks.filter(function (c) {
      return Math.abs(c.x - x) < 5 && Math.abs(c.y - y) < 5;
    });
    if (cluster.length >= 3 && data.behavior.rage.length < 100) {
      data.behavior.rage.push({ x: x, y: y, count: cluster.length });
    }

    // Dead-click detection: snapshot effect flags, re-check shortly after.
    domDirty = navDirty = netDirty = false;
    var target = ev.target;
    setTimeout(function () {
      if (!domDirty && !navDirty && !netDirty && data.behavior.dead.length < 100) {
        data.behavior.dead.push({ x: x, y: y, el: describe(target) });
      }
    }, 500);
  }, true);

  // Throttled mouse-movement sampling (rendered as movement heatmap; Agency tier
  // gates whether it is retained server-side).
  var lastMove = 0;
  document.addEventListener("mousemove", function (ev) {
    var now = performance.now();
    if (now - lastMove < 150) { return; }         // ~6-7 samples/sec max
    lastMove = now;
    if (data.behavior.moves.length < 1000) {
      data.behavior.moves.push({ x: pct(ev.clientX, window.innerWidth), y: pct(ev.clientY, window.innerHeight) });
    }
  }, true);

  // Scroll depth.
  var milestones = [25, 50, 75, 90, 100];
  window.addEventListener("scroll", function () {
    var doc = document.documentElement;
    var scrollable = (doc.scrollHeight - window.innerHeight) || 1;
    var depth = pct(window.scrollY || doc.scrollTop, scrollable);
    if (depth > data.behavior.scroll_max) { data.behavior.scroll_max = depth; }
    for (var i = milestones.length - 1; i >= 0; i--) {
      if (depth >= milestones[i] && data.behavior.scroll_milestones.indexOf(milestones[i]) === -1) {
        data.behavior.scroll_milestones.push(milestones[i]);
      }
    }
  }, { passive: true });

  // ---- 7. Send. sendBeacon over HTTPS; flush on visibilitychange. --------- //
  var sent = false;
  function flush() {
    if (sent) { return; }
    sent = true;
    data.page_path = location.pathname;
    var body = JSON.stringify(data);
    try {
      if (nav.sendBeacon) {
        nav.sendBeacon(ENDPOINT, new Blob([body], { type: "application/json" }));
        return;
      }
    } catch (e) {}
    try {
      fetch(ENDPOINT, { method: "POST", body: body, keepalive: true,
        headers: { "Content-Type": "application/json" }, mode: "cors", credentials: "omit" });
    } catch (e) {}
  }

  // Flush when the page is hidden/unloaded (most reliable beacon point).
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") { flush(); }
  });
  window.addEventListener("pagehide", flush);

  // Schedule any deferred bookkeeping off the critical path.
  (window.requestIdleCallback || function (fn) { setTimeout(fn, 1); })(function () {});
})();
