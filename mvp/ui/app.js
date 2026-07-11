(function () {
  "use strict";

  const cfg = window.MVP_UI_CONFIG || {};
  const esBase = (cfg.elasticsearch || "http://localhost:9200").replace(/\/$/, "");
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
      "</p>";
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

  // Optional deep-link: ?q=topographic
  const params = new URLSearchParams(window.location.search);
  if (params.get("q")) {
    input.value = params.get("q");
    search(input.value);
  }
})();
