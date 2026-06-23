/* RUM dashboard — fetches field data and renders the Real Users + Heatmaps tabs.
 * Components implemented as plain render functions (no framework, matching the
 * existing app's zero-build conventions):
 *   INPBreakdownBar, RUMvsCruxComparison, HeatmapOverlay, RageClickAlert,
 *   DeadClickAlert, ScrollDepthGauge, RUMInstallSnippet, SessionFlowDiagram.
 */
(function () {
  "use strict";
  var body = document.body;
  var SITE = body.dataset.siteId;
  var TIER = body.dataset.tier;
  var RUM_ENABLED = body.dataset.rumEnabled === "1";
  var BASE = "/rum/api/sites/" + SITE;

  // ---- Tabs ---------------------------------------------------------------- //
  var tabs = document.querySelectorAll(".rum-tab");
  var panels = document.querySelectorAll(".rum-panel");
  tabs.forEach(function (t) {
    t.addEventListener("click", function () {
      tabs.forEach(function (x) { x.classList.remove("active"); });
      panels.forEach(function (p) { p.classList.remove("active"); });
      t.classList.add("active");
      document.querySelector('.rum-panel[data-panel="' + t.dataset.tab + '"]').classList.add("active");
      if (t.dataset.tab === "heatmaps") { loadHeatmaps(); }
    });
  });

  function fmt(metric, v) {
    if (v === null || v === undefined) { return "—"; }
    if (metric === "cls") { return Number(v).toFixed(3); }
    return Math.round(v) + " ms";
  }

  // ---- Real Users ---------------------------------------------------------- //
  function gauge(metric, value, rating, thresh) {
    var pct = 0;
    if (value !== null && value !== undefined) {
      var max = thresh.poor * 1.5;
      pct = Math.min(100, (value / max) * 100);
    }
    return '<div class="gauge">' +
      '<div class="metric">' + metric.toUpperCase() + '</div>' +
      '<div class="value rating-' + rating + '">' + fmt(metric, value) + '</div>' +
      '<div class="bar"><span class="rating-' + rating + '" style="width:' + pct + '%"></span></div>' +
      '<div class="metric" style="margin-top:8px">' + rating.replace("-", " ") + '</div></div>';
  }

  // <INPBreakdownBar> — stacked input delay / processing / presentation.
  function INPBreakdownBar(b) {
    var id = b.input_delay || 0, pr = b.processing || 0, pe = b.presentation || 0;
    var total = id + pr + pe;
    if (!total) { return '<p class="rum-note">No INP interactions recorded yet.</p>'; }
    function seg(cls, label, v) {
      var w = (v / total) * 100;
      return '<div class="inp-seg ' + cls + '" style="width:' + w + '%" title="' + label + ': ' + v + 'ms">' +
        (w > 10 ? v + 'ms' : '') + '</div>';
    }
    return '<div class="inp-bar">' +
      seg("input", "Input delay", id) + seg("processing", "Processing", pr) +
      seg("presentation", "Presentation", pe) + '</div>' +
      '<div class="inp-legend">' +
      '<span><i style="background:#6366f1"></i>Input delay ' + id + 'ms</span>' +
      '<span><i style="background:#ec4899"></i>Processing ' + pr + 'ms</span>' +
      '<span><i style="background:#f59e0b"></i>Presentation ' + pe + 'ms</span></div>';
  }

  // <RUMvsCruxComparison> — badge per metric.
  function RUMvsCruxComparison(cmp) {
    return ["lcp", "cls", "inp"].map(function (m) {
      var c = cmp[m] || {};
      var delta = c.divergence;
      var deltaHtml = "—";
      if (delta !== null && delta !== undefined) {
        var better = delta < 0; // lower CWV is better
        deltaHtml = '<span class="delta ' + (better ? "better" : "worse") + '">' +
          (better ? "▼ " : "▲ ") + fmt(m, Math.abs(delta)) + "</span>";
      }
      return '<div class="crux-badge"><div class="m">' + m.toUpperCase() + '</div>' +
        '<div class="row"><span>Your RUM</span><b>' + fmt(m, c.rum) + '</b></div>' +
        '<div class="row"><span>CrUX 28-day</span><b>' + fmt(m, c.crux) + '</b></div>' +
        '<div class="row"><span>vs CrUX</span>' + deltaHtml + '</div></div>';
    }).join("");
  }

  function barList(obj) {
    var entries = Object.keys(obj || {}).map(function (k) { return [k, obj[k]]; });
    var total = entries.reduce(function (s, e) { return s + e[1]; }, 0) || 1;
    return '<div class="bars">' + entries.sort(function (a, b) { return b[1] - a[1]; })
      .map(function (e) {
        var w = (e[1] / total) * 100;
        return '<div class="row"><span style="width:70px">' + e[0] + '</span>' +
          '<span class="track"><span style="width:' + w + '%"></span></span>' +
          '<span>' + e[1] + '</span></div>';
      }).join("") + '</div>';
  }

  function loadRealUsers() {
    if (!RUM_ENABLED) { return; }
    fetch(BASE + "/realuser").then(function (r) { return r.json(); }).then(function (d) {
      if (!d.enabled) { return; }
      var empty = document.getElementById("ru-empty");
      if (!d.sample_count) { empty.hidden = false; } else { empty.hidden = true; }
      document.getElementById("ru-samples").textContent = d.sample_count || 0;

      document.getElementById("cwv-gauges").innerHTML =
        ["lcp", "cls", "inp"].map(function (m) {
          return gauge(m, d.cwv[m], d.ratings[m], d.thresholds[m]);
        }).join("");

      document.getElementById("inp-breakdown").innerHTML = INPBreakdownBar(d.inp_breakdown);
      document.getElementById("rum-vs-crux").innerHTML = RUMvsCruxComparison(d.comparison);

      document.getElementById("lcp-elements").innerHTML =
        (d.lcp_elements || []).map(function (e) {
          return '<li><code>' + e.element + '</code><span>' + e.count + '</span></li>';
        }).join("") || '<li class="rum-note">No LCP elements yet.</li>';

      document.getElementById("cls-sources").innerHTML =
        (d.cls_sources || []).map(function (e) {
          return '<li><code>' + (e.element || "?") + '</code><span>' + (e.impact || 0).toFixed(3) + '</span></li>';
        }).join("") || '<li class="rum-note">No CLS sources yet.</li>';

      document.getElementById("device-connection").innerHTML =
        '<div><h3 class="rum-section-title">By device</h3>' + barList(d.device_connection.device_class) + '</div>' +
        '<div><h3 class="rum-section-title">By connection</h3>' + barList(d.device_connection.connection_type) + '</div>';

      var scope = document.getElementById("page-scope");
      var tbody = document.querySelector("#per-page tbody");
      if (d.page_breakdown_available) {
        scope.textContent = "per page";
        tbody.innerHTML = (d.per_page || []).map(function (p) {
          return "<tr><td>" + p.page_path + "</td><td>" + p.samples + "</td><td>" +
            fmt("lcp", p.lcp_p75) + "</td><td>" + fmt("cls", p.cls_p75) + "</td><td>" +
            fmt("inp", p.inp_p75) + "</td></tr>";
        }).join("") || '<tr><td colspan="5" class="rum-note">No pages yet.</td></tr>';
      } else {
        scope.innerHTML = '<span class="locked">site-level only</span>';
        tbody.innerHTML = '<tr><td colspan="5" class="rum-note">Per-page breakdown is an Agency feature.</td></tr>';
      }
    }).catch(function () {});
  }

  // ---- Heatmaps ------------------------------------------------------------ //
  var activeLayer = "click";
  var lastHeatmap = null;
  document.querySelectorAll(".hm-layer").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll(".hm-layer").forEach(function (b) { b.classList.remove("active"); });
      btn.classList.add("active");
      activeLayer = btn.dataset.layer;
      if (lastHeatmap) { HeatmapOverlay(lastHeatmap); }
    });
  });
  var refreshBtn = document.getElementById("hm-refresh");
  if (refreshBtn) { refreshBtn.addEventListener("click", loadHeatmaps); }

  // <HeatmapOverlay> — canvas density render over a server-captured screenshot.
  function HeatmapOverlay(d) {
    var canvas = document.getElementById("heatmap-canvas");
    var ctx = canvas.getContext("2d");
    var W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    var grid = null;
    if (activeLayer === "click") { grid = d.click_heatmap; }
    else if (activeLayer === "move") { grid = d.movement_heatmap; }

    var bins = d.bins || 20;
    if (grid) {
      var max = 1;
      grid.forEach(function (row) { row.forEach(function (v) { if (v > max) { max = v; } }); });
      var cw = W / bins, ch = H / bins;
      for (var y = 0; y < bins; y++) {
        for (var x = 0; x < bins; x++) {
          var v = grid[y][x] || 0;
          if (!v) { continue; }
          var a = Math.min(0.85, 0.15 + (v / max) * 0.7);
          var hue = 240 - Math.round((v / max) * 240); // blue -> red
          ctx.fillStyle = "hsla(" + hue + ",90%,55%," + a + ")";
          ctx.fillRect(x * cw, y * ch, cw, ch);
        }
      }
    }

    // Rage / dead hotspots as ringed markers.
    function markers(set, color) {
      if (!set || !set.hotspots) { return; }
      set.hotspots.forEach(function (h) {
        var cx = (h.x_bin + 0.5) * (W / bins), cy = (h.y_bin + 0.5) * (H / bins);
        var rad = 10 + Math.min(30, h.count * 3);
        ctx.beginPath(); ctx.arc(cx, cy, rad, 0, Math.PI * 2);
        ctx.strokeStyle = color; ctx.lineWidth = 3; ctx.stroke();
        ctx.fillStyle = color; ctx.font = "12px sans-serif";
        ctx.fillText(String(h.count), cx + rad + 2, cy);
      });
    }
    if (activeLayer === "rage") { markers(d.rage, "#ff4e42"); }
    if (activeLayer === "dead") { markers(d.dead, "#ffa400"); }
  }

  // <RageClickAlert> / <DeadClickAlert>
  function ClickAlert(kind, set, label, cls) {
    if (!set) {
      return '<div class="alert ' + cls + '"><h3>' + label + '</h3>' +
        '<p class="rum-note locked">Not available on your plan.</p></div>';
    }
    return '<div class="alert ' + cls + '"><h3>' + label + '</h3>' +
      '<div class="big">' + (set.total || 0) + '</div>' +
      '<p class="rum-note">' + (set.hotspots || []).length + ' hotspot region(s) detected.</p></div>';
  }

  // <ScrollDepthGauge>
  function ScrollDepthGauge(hist) {
    if (!hist) { return '<p class="rum-note locked">Not available on your plan.</p>'; }
    var rows = [];
    for (var i = 0; i <= 10; i++) {
      rows.push([i * 10 + "%", hist[String(i)] || 0]);
    }
    var total = rows.reduce(function (s, r) { return s + r[1]; }, 0) || 1;
    return '<div class="bars">' + rows.map(function (r) {
      var w = (r[1] / total) * 100;
      return '<div class="row"><span style="width:48px">' + r[0] + '</span>' +
        '<span class="track"><span style="width:' + w + '%"></span></span>' +
        '<span>' + r[1] + '</span></div>';
    }).join("") + '</div>';
  }

  // <SessionFlowDiagram>
  function SessionFlowDiagram(flows) {
    if (!flows) { return '<p class="rum-note locked">Session flow is an Agency feature.</p>'; }
    if (!flows.length) { return '<p class="rum-note">No multi-page sessions yet.</p>'; }
    return '<div class="flow">' + flows.map(function (f) {
      var steps = f.path.map(function (p) { return '<span class="step">' + p + '</span>'; }).join('<span class="arrow">→</span>');
      return '<div class="path">' + steps + '<span class="count">' + f.count + ' sessions</span></div>';
    }).join("") + '</div>';
  }

  function loadHeatmaps() {
    if (!RUM_ENABLED) { return; }
    var page = (document.getElementById("hm-page").value || "").trim();
    var url = BASE + "/heatmaps" + (page ? "?page=" + encodeURIComponent(page) : "");
    fetch(url).then(function (r) { return r.json(); }).then(function (d) {
      if (!d.enabled) { return; }
      lastHeatmap = d;
      var img = document.getElementById("hm-screenshot");
      var noshot = document.getElementById("hm-noscreenshot");
      if (d.screenshot_url) { img.src = d.screenshot_url; img.hidden = false; noshot.hidden = true; }
      else { img.hidden = true; noshot.hidden = false; }
      HeatmapOverlay(d);
      document.getElementById("rage-alert").innerHTML = ClickAlert("rage", d.rage, "Rage clicks", "");
      document.getElementById("dead-alert").innerHTML = ClickAlert("dead", d.dead, "Dead clicks", "dead");
      document.getElementById("scroll-depth").innerHTML = ScrollDepthGauge(d.scroll_hist);
      document.getElementById("session-flow").innerHTML = SessionFlowDiagram(d.flows);

      // Disable movement layer button if the plan doesn't include it.
      var moveBtn = document.querySelector('.hm-layer[data-layer="move"]');
      if (moveBtn) { moveBtn.classList.toggle("locked", !(d.features && d.features.movement_heatmap)); }
    }).catch(function () {});
  }

  // ---- Install (<RUMInstallSnippet>) -------------------------------------- //
  function loadInstall() {
    fetch("/rum/install/" + SITE).then(function (r) { return r.json(); }).then(function (d) {
      var el = document.getElementById("install-snippet");
      var esc = d.snippet_tag.replace(/</g, "&lt;").replace(/>/g, "&gt;");
      el.innerHTML = '<div class="install-box"><code>' + esc + '</code><br>' +
        '<button id="copy-snippet">Copy</button></div>';
      document.getElementById("copy-snippet").addEventListener("click", function () {
        navigator.clipboard && navigator.clipboard.writeText(d.snippet_tag);
        this.textContent = "Copied ✓";
      });
    }).catch(function () {});
  }

  // ---- Boot ---------------------------------------------------------------- //
  loadRealUsers();
  loadInstall();
})();
