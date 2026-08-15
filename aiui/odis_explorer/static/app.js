(() => {
  const TYPE_THEMES = {
    dataset: { key: "dataset", color: "#0f6e56", tint: "#e1f5ee" },
    creativework: { key: "literature", color: "#a3401f", tint: "#faeee7" },
    person: { key: "org", color: "#1f5c8b", tint: "#e7f1fa" },
    organization: { key: "org", color: "#1f5c8b", tint: "#e7f1fa" },
    datacatalog: { key: "org", color: "#1f5c8b", tint: "#e7f1fa" },
    event: { key: "training", color: "#8b5e0b", tint: "#fbf1de" },
    course: { key: "training", color: "#8b5e0b", tint: "#fbf1de" },
    researchproject: { key: "project", color: "#5a4a96", tint: "#efedfa" },
    place: { key: "default", color: "#4b5d63", tint: "#f3f6f4" },
    geoshape: { key: "default", color: "#4b5d63", tint: "#f3f6f4" },
    geocoordinates: { key: "default", color: "#4b5d63", tint: "#f3f6f4" },
  };

  const state = {
    page: 1,
    selectedId: null,
    data: null,
    types: new Set(),
    map: null,
    featureLayer: null,
    featureByRecord: new Map(),
    network: null,
    nodeIdsByRecord: new Map(),
  };

  const els = {
    form: document.getElementById("search-form"),
    q: document.getElementById("q"),
    size: document.getElementById("size"),
    fragments: document.getElementById("fragments"),
    typePills: document.getElementById("type-pills"),
    status: document.getElementById("status"),
    mapNote: document.getElementById("map-note"),
    graphNote: document.getElementById("graph-note"),
    tbody: document.getElementById("results-body"),
    pager: document.getElementById("pager"),
    prev: document.getElementById("prev-page"),
    next: document.getElementById("next-page"),
    pageLabel: document.getElementById("page-label"),
  };

  function normalizeType(type) {
    return String(type || "")
      .toLowerCase()
      .replace(/^schema:/, "")
      .replace(/[\s_-]+/g, "");
  }

  function typeTheme(type) {
    return TYPE_THEMES[normalizeType(type)] || { key: "default", color: "#4b5d63", tint: "#f3f6f4" };
  }

  function stripTags(html) {
    const template = document.createElement("template");
    template.innerHTML = html || "";
    return (template.content.textContent || "").replace(/\s+/g, " ").trim();
  }

  function escapeHtml(text) {
    return String(text ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function sourceLabel(item) {
    const source = item.source || {};
    return source.name || source.id || "";
  }

  function hasSpatial(item) {
    const spatial = item.spatial || {};
    return Boolean(
      (spatial.boxes && spatial.boxes.length) ||
        (spatial.points && spatial.points.length) ||
        (spatial.polygons && spatial.polygons.length),
    );
  }

  function readUrl() {
    const params = new URLSearchParams(window.location.search);
    els.q.value = params.get("q") || "";
    els.size.value = params.get("size") || "20";
    els.fragments.checked = ["1", "true", "yes"].includes((params.get("include_graph_fragments") || "").toLowerCase());
    state.page = Math.max(1, Number(params.get("page") || 1));
    state.types = new Set(params.getAll("types").filter(Boolean));
  }

  function writeUrl() {
    const params = new URLSearchParams();
    if (els.q.value.trim()) params.set("q", els.q.value.trim());
    for (const type of state.types) params.append("types", type);
    if (els.size.value !== "20") params.set("size", els.size.value);
    if (state.page > 1) params.set("page", String(state.page));
    if (els.fragments.checked) params.set("include_graph_fragments", "true");
    const query = params.toString();
    history.replaceState(null, "", query ? `?${query}` : location.pathname);
  }

  function initMap() {
    state.map = L.map("map", { worldCopyJump: true, scrollWheelZoom: true }).setView([10, 0], 2);
    const carto = L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
      attribution: "&copy; OpenStreetMap &copy; CARTO",
      subdomains: "abcd",
      maxZoom: 19,
    });
    carto.on("tileerror", () => {
      if (state.map._osmFallback) return;
      state.map._osmFallback = true;
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap",
        maxZoom: 19,
      }).addTo(state.map);
    });
    carto.addTo(state.map);
    state.featureLayer = L.layerGroup().addTo(state.map);
  }

  function popupHtml(feature) {
    const title = escapeHtml(feature.title || "(untitled)");
    const source = escapeHtml(feature.source || "");
    const url = feature.url ? `<br><a href="${escapeHtml(feature.url)}" target="_blank" rel="noopener">Open record</a>` : "";
    return `<strong>${title}</strong>${source ? `<br>${source}` : ""}${url}`;
  }

  function bindFeature(layer, recordId) {
    if (!state.featureByRecord.has(recordId)) {
      state.featureByRecord.set(recordId, []);
    }
    state.featureByRecord.get(recordId).push(layer);
    layer.on("click", () => select(recordId, { from: "map" }));
  }

  function renderMap(geo) {
    state.featureLayer.clearLayers();
    state.featureByRecord.clear();
    const fitBounds = [];
    const points = geo?.points || [];
    const boxes = geo?.boxes || [];
    const polygons = geo?.polygons || [];

    for (const polygon of polygons) {
      const ring = (polygon.coordinates || []).map((pair) => [pair[0], pair[1]]);
      if (ring.length < 3) continue;
      const theme = typeTheme(polygon.type);
      const layer = L.polygon(ring, {
        color: theme.color,
        weight: 1.5,
        fillColor: theme.color,
        fillOpacity: 0.18,
      }).bindPopup(popupHtml(polygon));
      layer.addTo(state.featureLayer);
      bindFeature(layer, polygon.recordId);
      if (!polygon.nearGlobal) fitBounds.push(layer.getBounds());
    }

    for (const box of boxes) {
      const bounds = [
        [box.south, box.west],
        [box.north, box.east],
      ];
      const theme = typeTheme(box.type);
      const rect = L.rectangle(bounds, {
        color: theme.color,
        weight: 1.5,
        fillColor: theme.color,
        fillOpacity: 0.18,
      }).bindPopup(popupHtml(box));
      rect.addTo(state.featureLayer);
      bindFeature(rect, box.recordId);
      if (!box.nearGlobal) fitBounds.push(bounds);
    }

    for (const point of points) {
      const theme = typeTheme(point.type);
      const marker = L.circleMarker([point.lat, point.lon], {
        radius: 7,
        color: theme.color,
        weight: 2,
        fillColor: theme.tint,
        fillOpacity: 0.95,
      }).bindPopup(popupHtml(point));
      marker.addTo(state.featureLayer);
      bindFeature(marker, point.recordId);
      fitBounds.push([point.lat, point.lon]);
    }

    const withSpatial = geo?.recordsWithSpatial || 0;
    const total = geo?.recordCount || 0;
    const polygonCount = polygons.length;
    const boxCount = boxes.length;
    const pointCount = points.length;
    let note = total ? `${withSpatial} of ${total} have coordinates` : "";
    if (total && (polygonCount || boxCount || pointCount)) {
      const parts = [];
      if (polygonCount) parts.push(`${polygonCount} polygon${polygonCount === 1 ? "" : "s"}`);
      if (boxCount) parts.push(`${boxCount} box${boxCount === 1 ? "" : "es"}`);
      if (pointCount) parts.push(`${pointCount} point${pointCount === 1 ? "" : "s"}`);
      note += ` · ${parts.join(", ")}`;
    }
    els.mapNote.textContent = note;

    if (fitBounds.length) {
      state.map.fitBounds(fitBounds, { padding: [24, 24], maxZoom: 6 });
    } else {
      state.map.setView([10, 0], 2);
    }
    requestAnimationFrame(() => state.map.invalidateSize());
  }

  function renderGraph(graph) {
    const nodes = (graph?.nodes || []).map((node) => {
      const theme = typeTheme(node.type);
      return {
        id: node.id,
        label: node.label,
        title: `${node.type}${node.details?.name ? ` — ${node.details.name}` : ""}`,
        color: {
          background: node.isRecord ? theme.color : theme.tint,
          border: theme.color,
          highlight: { background: theme.color, border: "#12232b" },
        },
        font: {
          color: node.isRecord ? "#ffffff" : "#12232b",
          face: "IBM Plex Sans",
          size: node.isRecord ? 14 : 12,
        },
        shape: node.isRecord ? "box" : "dot",
        size: node.isRecord ? 18 : 12,
        recordIds: node.recordIds || [],
        recordId: node.recordId || (node.recordIds || [])[0] || null,
      };
    });
    const edges = (graph?.edges || []).map((edge, index) => ({
      id: `e${index}`,
      from: edge.from,
      to: edge.to,
      label: edge.label,
      font: { size: 10, color: "#8a9b98", face: "IBM Plex Sans" },
      color: { color: "#b7c6c1" },
      arrows: "to",
    }));

    state.nodeIdsByRecord.clear();
    for (const node of nodes) {
      for (const recordId of node.recordIds || []) {
        if (!state.nodeIdsByRecord.has(recordId)) state.nodeIdsByRecord.set(recordId, []);
        state.nodeIdsByRecord.get(recordId).push(node.id);
      }
    }

    const container = document.getElementById("graph");
    if (state.network) {
      state.network.destroy();
      state.network = null;
    }
    state.network = new vis.Network(
      container,
      { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) },
      {
        interaction: { hover: true, tooltipDelay: 120 },
        physics: {
          barnesHut: { gravitationalConstant: -2800, springLength: 110, springConstant: 0.04 },
          stabilization: { iterations: 80 },
        },
        edges: { smooth: { type: "continuous" } },
      },
    );
    state.network.on("click", (params) => {
      if (!params.nodes.length) return;
      const node = nodes.find((item) => item.id === params.nodes[0]);
      if (node?.recordId) select(node.recordId, { from: "graph" });
    });
    els.graphNote.textContent = `${nodes.length} nodes · ${edges.length} edges`;
  }

  function renderTypePills(facets) {
    const buckets = facets?.types || [];
    els.typePills.replaceChildren();
    for (const bucket of buckets.slice(0, 12)) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = `${bucket.value} (${bucket.count})`;
      if (state.types.has(bucket.value)) button.classList.add("active");
      button.addEventListener("click", () => {
        if (state.types.has(bucket.value)) state.types.delete(bucket.value);
        else state.types.add(bucket.value);
        state.page = 1;
        runSearch();
      });
      els.typePills.append(button);
    }
  }

  function renderTable(items) {
    els.tbody.replaceChildren();
    if (!items.length) {
      const row = document.createElement("tr");
      row.className = "empty";
      row.innerHTML = `<td colspan="5">No results.</td>`;
      els.tbody.append(row);
      return;
    }

    for (const item of items) {
      const theme = typeTheme(item.type);
      const row = document.createElement("tr");
      row.dataset.recordId = item.id;
      if (item.id === state.selectedId) row.classList.add("selected");
      const title = escapeHtml(item.title || "(untitled)");
      const summary = escapeHtml(stripTags(item.summary || "").slice(0, 180));
      const source = escapeHtml(sourceLabel(item));
      const url = item.url ? escapeHtml(item.url) : "";
      row.innerHTML = `
        <td class="title-cell">
          ${item.url ? `<a href="${url}" target="_blank" rel="noopener">${title}</a>` : title}
          ${summary ? `<span class="summary">${summary}</span>` : ""}
        </td>
        <td><span class="type-badge ${theme.key}">${escapeHtml(item.type || "record")}</span></td>
        <td>${source}</td>
        <td class="${hasSpatial(item) ? "spatial-yes" : "spatial-no"}">${hasSpatial(item) ? "yes" : "—"}</td>
        <td class="link-cell">${item.url ? `<a href="${url}" target="_blank" rel="noopener">${url}</a>` : ""}</td>
      `;
      row.addEventListener("click", (event) => {
        if (event.target.closest("a")) return;
        select(item.id, { from: "table" });
      });
      els.tbody.append(row);
    }
  }

  function renderPager(data) {
    const total = data.total || 0;
    const size = data.size || Number(els.size.value);
    const page = data.page || 1;
    const pages = Math.max(1, Math.ceil(total / size));
    els.pager.hidden = total === 0;
    els.pageLabel.textContent = `Page ${page} of ${pages}`;
    els.prev.disabled = page <= 1;
    els.next.disabled = page >= pages;
  }

  function select(recordId, { from } = {}) {
    state.selectedId = recordId;
    for (const row of els.tbody.querySelectorAll("tr[data-record-id]")) {
      row.classList.toggle("selected", row.dataset.recordId === recordId);
    }
    const layers = state.featureByRecord.get(recordId) || [];
    if (layers.length && from !== "map") {
      layers[0].openPopup();
      if (layers[0].getBounds) state.map.fitBounds(layers[0].getBounds(), { padding: [28, 28], maxZoom: 6 });
      else if (layers[0].getLatLng) state.map.panTo(layers[0].getLatLng());
    }
    const nodeIds = state.nodeIdsByRecord.get(recordId) || [];
    if (state.network && nodeIds.length && from !== "graph") {
      state.network.selectNodes(nodeIds);
      state.network.focus(nodeIds[0], { scale: 1.1, animation: true });
    }
  }

  async function runSearch() {
    writeUrl();
    const params = new URLSearchParams();
    if (els.q.value.trim()) params.set("q", els.q.value.trim());
    for (const type of state.types) params.append("types", type);
    params.set("page", String(state.page));
    params.set("size", els.size.value);
    if (els.fragments.checked) params.set("include_graph_fragments", "true");

    els.status.textContent = "Searching…";
    els.status.classList.remove("error");
    try {
      const response = await fetch(`/api/search?${params.toString()}`);
      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        throw new Error(detail.detail || `Search failed (${response.status})`);
      }
      const data = await response.json();
      state.data = data;
      const items = data.items || [];
      els.status.textContent = `${Number(data.total || 0).toLocaleString()} results — showing page ${data.page} (${items.length})`;
      renderTypePills(data.facets);
      renderTable(items);
      renderMap(data.geo);
      renderGraph(data.graph);
      renderPager(data);
      if (state.selectedId) select(state.selectedId, { from: "reload" });
    } catch (error) {
      els.status.textContent = error.message || String(error);
      els.status.classList.add("error");
    }
  }

  els.form.addEventListener("submit", (event) => {
    event.preventDefault();
    state.page = 1;
    runSearch();
  });
  els.prev.addEventListener("click", () => {
    state.page = Math.max(1, state.page - 1);
    runSearch();
  });
  els.next.addEventListener("click", () => {
    state.page += 1;
    runSearch();
  });
  els.fragments.addEventListener("change", () => {
    state.page = 1;
    if (els.q.value.trim() || state.types.size) runSearch();
  });

  initMap();
  readUrl();
  if (els.q.value.trim() || state.types.size) {
    runSearch();
  } else {
    els.q.value = "coral";
    state.types.add("Dataset");
    runSearch();
  }
})();
