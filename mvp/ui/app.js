(function () {
  "use strict";

  const cfg = window.MVP_UI_CONFIG || {};
  const esBase = (cfg.elasticsearch || "http://odis.org:9400").replace(/\/$/, "");
  const indexPattern = cfg.indexPattern || "gleaner-*";
  const size = cfg.size || 20;

  const form = document.getElementById("search-form");
  const input = document.getElementById("q");
  const statusEl = document.getElementById("status");
  const resultsEl = document.getElementById("results");
  const submitBtn = form.querySelector('button[type="submit"]');

  function setStatus(msg, isError) {
    statusEl.textContent = msg || "";
    statusEl.classList.toggle("error", !!isError);
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function isHttpUrl(s) {
    return typeof s === "string" && /^https?:\/\//i.test(s);
  }

  function bestLink(src) {
    if (isHttpUrl(src.url)) return src.url;
    if (isHttpUrl(src.source_url)) return src.source_url;
    if (isHttpUrl(src.id)) return src.id;
    return null;
  }

  function truncate(text, max) {
    if (!text) return "";
    const t = String(text).replace(/\s+/g, " ").trim();
    if (t.length <= max) return t;
    return t.slice(0, max - 1).trimEnd() + "…";
  }

  function formatJsonld(jsonld) {
    if (jsonld == null) return null;
    try {
      return JSON.stringify(jsonld, null, 2);
    } catch (e) {
      return String(jsonld);
    }
  }

  function renderJsonldAccordion(src) {
    const pretty = formatJsonld(src.jsonld);
    if (!pretty) {
      return (
        '<details class="jsonld-panel empty">' +
        "<summary>Original JSON-LD</summary>" +
        '<p class="jsonld-missing">No JSON-LD payload on this hit (re-index if older documents omit <code>jsonld</code>).</p>' +
        "</details>"
      );
    }
    const s3note = src.s3_key
      ? '<p class="jsonld-provenance">S3: <code>' + escapeHtml(src.s3_key) + "</code></p>"
      : "";
    return (
      '<details class="jsonld-panel">' +
      "<summary>Original JSON-LD</summary>" +
      s3note +
      '<pre class="jsonld-body"><code>' +
      escapeHtml(pretty) +
      "</code></pre>" +
      "</details>"
    );
  }

  function renderHit(hit) {
    const src = hit._source || {};
    const title = src.name || src.id || "(untitled)";
    const desc = truncate(src.description || "", 320);
    const link = bestLink(src);
    const types = Array.isArray(src.type) ? src.type.join(", ") : src.type || "";
    const source = src.source || "";
    const metaParts = [];
    if (source) metaParts.push(escapeHtml(source));
    if (types) metaParts.push(escapeHtml(types));

    let titleHtml;
    if (link) {
      titleHtml =
        '<a href="' +
        escapeHtml(link) +
        '" target="_blank" rel="noopener noreferrer">' +
        escapeHtml(title) +
        "</a>";
    } else {
      titleHtml = '<span class="no-link">' + escapeHtml(title) + "</span>";
    }

    let indexedFrom = "";
    if (src.source_url && src.source_url !== link) {
      indexedFrom =
        ' · indexed from <a href="' +
        escapeHtml(src.source_url) +
        '" target="_blank" rel="noopener noreferrer">' +
        escapeHtml(truncate(src.source_url, 60)) +
        "</a>";
    } else if (src.source_url && !link) {
      indexedFrom =
        ' · <a href="' +
        escapeHtml(src.source_url) +
        '" target="_blank" rel="noopener noreferrer">open page</a>';
    }

    const card = document.createElement("article");
    card.className = "card";
    card.innerHTML =
      "<h2>" +
      titleHtml +
      "</h2>" +
      (desc ? '<p class="description">' + escapeHtml(desc) + "</p>" : "") +
      '<p class="meta">' +
      metaParts.join(" · ") +
      indexedFrom +
      "</p>" +
      renderJsonldAccordion(src);
    return card;
  }

  async function search(query) {
    const q = (query || "").trim();
    resultsEl.innerHTML = "";
    if (!q) {
      setStatus("Enter a search term.");
      return;
    }

    setStatus("Searching…");
    submitBtn.disabled = true;

    const body = {
      query: {
        multi_match: {
          query: q,
          fields: ["name^3", "description", "keywords", "type"],
        },
      },
      size: size,
      _source: [
        "name",
        "description",
        "url",
        "source_url",
        "id",
        "source",
        "type",
        "s3_key",
        "jsonld",
      ],
    };

    // Keep * unencoded for multi-index patterns like gleaner-*
    const url = esBase + "/" + indexPattern + "/_search";

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error("Elasticsearch HTTP " + res.status + ": " + text.slice(0, 200));
      }

      const data = await res.json();
      const hits = (data.hits && data.hits.hits) || [];
      const total =
        data.hits && data.hits.total
          ? typeof data.hits.total === "object"
            ? data.hits.total.value
            : data.hits.total
          : hits.length;

      if (!hits.length) {
        setStatus('No results for “' + q + '”.');
        return;
      }

      setStatus(total + " result" + (total === 1 ? "" : "s") + " for “" + q + "”");
      const frag = document.createDocumentFragment();
      hits.forEach(function (hit) {
        frag.appendChild(renderHit(hit));
      });
      resultsEl.appendChild(frag);
    } catch (err) {
      console.error(err);
      setStatus(
        "Search failed. Is Elasticsearch running at " +
          esBase +
          " with CORS enabled? " +
          (err && err.message ? err.message : String(err)),
        true
      );
    } finally {
      submitBtn.disabled = false;
    }
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    search(input.value);
  });

  // --- Theme (light / dark) ---
  const THEME_KEY = "mvp-ui-theme";
  const themeToggle = document.getElementById("theme-toggle");

  function currentTheme() {
    const t = document.documentElement.getAttribute("data-theme");
    return t === "dark" ? "dark" : "light";
  }

  function applyTheme(theme) {
    const next = theme === "dark" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch (e) {
      /* ignore */
    }
    if (themeToggle) {
      const goingDark = next === "light";
      themeToggle.setAttribute(
        "aria-label",
        goingDark ? "Switch to dark mode" : "Switch to light mode"
      );
      const label = themeToggle.querySelector(".theme-toggle-label");
      if (label) label.textContent = goingDark ? "Dark" : "Light";
    }
  }

  function resolveInitialTheme() {
    try {
      const stored = localStorage.getItem(THEME_KEY);
      if (stored === "light" || stored === "dark") return stored;
    } catch (e) {
      /* ignore */
    }
    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      return "dark";
    }
    return "light";
  }

  // Sync control labels with stored / system preference (matches FOUC head script)
  applyTheme(resolveInitialTheme());

  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      applyTheme(currentTheme() === "dark" ? "light" : "dark");
    });
  }

  // Optional deep-link: ?q=topographic
  const params = new URLSearchParams(window.location.search);
  if (params.get("q")) {
    input.value = params.get("q");
    search(input.value);
  }
})();
