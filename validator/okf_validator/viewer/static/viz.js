// Adapted from GoogleCloudPlatform/knowledge-catalog (okf/src/reference_agent/viewer/static/viz.js),
// Copyright Google LLC, licensed under the Apache License, Version 2.0.
// Modified for slo.okf: edges/backlinks keyed by typed-relationship field
// name, a "links to" list alongside "linked from", light/dark theming via
// CSS custom properties, and an okf:// link scheme for cross-concept prose
// links (see generator.py) in place of root-relative /*.md link rewriting.
// Full license text: ../../../../THIRD_PARTY_NOTICES.md
(function () {
  const bundle = window.BUNDLE;
  const bundleName = window.BUNDLE_NAME;
  document.title = `${bundleName} — OKF Viewer`;
  document.getElementById("bundle-name").textContent = bundleName;

  const darkQuery = window.matchMedia("(prefers-color-scheme: dark)");
  function colorFor(type) {
    const entry = bundle.palette[type] || bundle.defaultColor;
    return darkQuery.matches ? entry.dark : entry.light;
  }
  function cssVar(name) {
    return getComputedStyle(document.body).getPropertyValue(name).trim();
  }

  // Legend order follows the palette's fixed slot order (the CVD-safety
  // mechanism), restricted to types actually present in this bundle; any
  // type outside the validated palette (e.g. an unrecognized `type`) is
  // appended using the muted default swatch.
  const legendEl = document.getElementById("legend");
  const paletteOrder = Object.keys(bundle.palette).filter((t) => bundle.types.includes(t));
  const extraTypes = bundle.types.filter((t) => !bundle.palette[t]);
  const legendDots = [];
  for (const t of [...paletteOrder, ...extraTypes]) {
    const item = document.createElement("span");
    item.className = "legend-item";
    const dot = document.createElement("span");
    dot.className = "dot";
    legendDots.push({ type: t, el: dot });
    item.appendChild(dot);
    const label = document.createElement("span");
    label.textContent = t;
    item.appendChild(label);
    legendEl.appendChild(item);
  }

  // Populate type filter
  const typeSelect = document.getElementById("filter-type");
  for (const t of bundle.types) {
    const opt = document.createElement("option");
    opt.value = t;
    opt.textContent = t;
    typeSelect.appendChild(opt);
  }

  // Build reverse-link index for "Linked from"
  const backlinks = {};
  for (const edge of bundle.edges) {
    const { source, target, field } = edge.data;
    (backlinks[target] ||= []).push({ source, field });
  }
  const outlinks = {};
  for (const edge of bundle.edges) {
    const { source, target, field } = edge.data;
    (outlinks[source] ||= []).push({ target, field });
  }

  // Look up node label/type by id
  const nodeIndex = {};
  for (const n of bundle.nodes) nodeIndex[n.data.id] = n.data;

  const cy = cytoscape({
    container: document.getElementById("graph"),
    elements: [...bundle.nodes, ...bundle.edges],
    style: [
      {
        selector: "node",
        style: {
          "background-color": (ele) => colorFor(ele.data("type")),
          "label": "data(label)",
          "color": () => cssVar("--text-primary"),
          "font-size": 11,
          "text-valign": "bottom",
          "text-margin-y": 4,
          "text-wrap": "wrap",
          "text-max-width": 120,
          "width": "data(size)",
          "height": "data(size)",
          "border-width": 1,
          "border-color": (ele) => colorFor(ele.data("type")),
          "border-opacity": 0.6,
        },
      },
      {
        selector: "node:selected",
        style: {
          "border-width": 3,
          "border-color": () => cssVar("--accent"),
          "border-opacity": 1,
        },
      },
      {
        selector: "edge",
        style: {
          "width": 1.5,
          "line-color": () => cssVar("--baseline"),
          "target-arrow-color": () => cssVar("--baseline"),
          "target-arrow-shape": "triangle",
          "curve-style": "bezier",
          "arrow-scale": 0.9,
          "label": "data(field)",
          "font-size": 8,
          "color": () => cssVar("--text-muted"),
          "text-rotation": "autorotate",
          "text-background-color": () => cssVar("--surface-1"),
          "text-background-opacity": 0.85,
          "text-background-padding": 1,
        },
      },
      {
        selector: "edge:selected",
        style: {
          "line-color": () => cssVar("--accent"),
          "target-arrow-color": () => cssVar("--accent"),
          "width": 2.5,
        },
      },
      {
        selector: ".dim",
        style: { "opacity": 0.15 },
      },
    ],
    layout: { name: "cose", animate: false, padding: 30 },
    wheelSensitivity: 0.2,
  });

  let currentId = null;
  function repaintTheme() {
    cy.style().update();
    for (const { type, el } of legendDots) el.style.background = colorFor(type);
    if (currentId) {
      document.getElementById("detail-type-dot").style.background = colorFor(nodeIndex[currentId].type);
    }
  }
  repaintTheme();
  darkQuery.addEventListener("change", repaintTheme);

  cy.on("tap", "node", (evt) => showDetail(evt.target.id()));
  cy.on("tap", (evt) => {
    if (evt.target === cy) clearSelection();
  });

  document.getElementById("layout").addEventListener("change", (e) => {
    cy.layout({ name: e.target.value, animate: false, padding: 30, directed: true }).run();
  });

  document.getElementById("reset").addEventListener("click", () => {
    cy.fit(null, 30);
    clearSelection();
  });

  document.getElementById("search").addEventListener("input", (e) => {
    const q = e.target.value.trim().toLowerCase();
    if (!q) {
      cy.elements().removeClass("dim");
      return;
    }
    cy.nodes().forEach((n) => {
      const d = n.data();
      const hay =
        (d.label || "").toLowerCase() + " " +
        d.id.toLowerCase() + " " +
        (d.tags || []).join(" ").toLowerCase();
      n.toggleClass("dim", !hay.includes(q));
    });
    cy.edges().forEach((edge) => {
      const src = edge.source();
      const tgt = edge.target();
      edge.toggleClass("dim", src.hasClass("dim") || tgt.hasClass("dim"));
    });
  });

  document.getElementById("filter-type").addEventListener("change", (e) => {
    const t = e.target.value;
    if (!t) {
      cy.elements().removeClass("dim");
      return;
    }
    cy.nodes().forEach((n) => {
      n.toggleClass("dim", n.data("type") !== t);
    });
    cy.edges().forEach((edge) => {
      edge.toggleClass("dim", edge.source().hasClass("dim") || edge.target().hasClass("dim"));
    });
  });

  function clearSelection() {
    cy.elements().unselect();
    document.getElementById("detail-empty").hidden = false;
    document.getElementById("detail-content").hidden = true;
  }

  function renderLinkList(listEl, sectionEl, entries, keyName) {
    listEl.innerHTML = "";
    if (!entries.length) {
      sectionEl.hidden = true;
      return;
    }
    sectionEl.hidden = false;
    for (const entry of entries) {
      const id = entry[keyName];
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.textContent = nodeIndex[id]?.label || id;
      a.addEventListener("click", () => showDetail(id));
      li.appendChild(a);
      const field = document.createElement("span");
      field.className = "field";
      field.textContent = ` (${entry.field})`;
      li.appendChild(field);
      listEl.appendChild(li);
    }
  }

  function showDetail(conceptId) {
    const data = nodeIndex[conceptId];
    if (!data) return;
    currentId = conceptId;
    cy.elements().unselect();
    const node = cy.getElementById(conceptId);
    if (node) node.select();

    document.getElementById("detail-empty").hidden = true;
    const content = document.getElementById("detail-content");
    content.hidden = false;

    document.getElementById("detail-type-dot").style.background = colorFor(data.type);
    document.getElementById("detail-type-label").textContent = data.type;

    document.getElementById("detail-title").textContent = data.label;
    document.getElementById("detail-id").textContent = conceptId;
    document.getElementById("detail-description").textContent = data.description || "—";

    const resourceEl = document.getElementById("detail-resource");
    resourceEl.innerHTML = "";
    if (data.resource) {
      const a = document.createElement("a");
      a.href = data.resource;
      a.textContent = data.resource;
      a.target = "_blank";
      a.rel = "noopener";
      a.className = "external";
      resourceEl.appendChild(a);
    } else {
      resourceEl.textContent = "—";
    }

    document.getElementById("detail-owner").textContent = data.owner || "—";
    document.getElementById("detail-reviewed").textContent =
      data.reviewed ? `${data.reviewed}${data.review_interval ? ` (every ${data.review_interval})` : ""}` : "—";

    const tagsEl = document.getElementById("detail-tags");
    tagsEl.innerHTML = "";
    if (data.tags && data.tags.length) {
      for (const t of data.tags) {
        const span = document.createElement("span");
        span.className = "tag";
        span.textContent = t;
        tagsEl.appendChild(span);
      }
    } else {
      tagsEl.textContent = "—";
    }

    const body = bundle.bodies[conceptId] || "";
    const html = marked.parse(body, { breaks: false, gfm: true });
    const bodyEl = document.getElementById("detail-body");
    bodyEl.innerHTML = html;
    rewriteInternalLinks(bodyEl);

    renderLinkList(
      document.getElementById("links-list"),
      document.getElementById("detail-links"),
      outlinks[conceptId] || [],
      "target"
    );
    renderLinkList(
      document.getElementById("backlinks-list"),
      document.getElementById("detail-backlinks"),
      backlinks[conceptId] || [],
      "source"
    );

    cy.animate({ center: { eles: node }, zoom: Math.max(cy.zoom(), 1.0) }, { duration: 200 });
  }

  function rewriteInternalLinks(root) {
    root.querySelectorAll("a[href]").forEach((a) => {
      const href = a.getAttribute("href");
      if (!href) return;
      if (href.startsWith("okf://")) {
        const target = href.slice("okf://".length);
        if (nodeIndex[target]) {
          a.className = "internal";
          a.setAttribute("href", "javascript:void(0)");
          a.addEventListener("click", (e) => {
            e.preventDefault();
            showDetail(target);
          });
          return;
        }
      }
      a.className = "external";
      a.setAttribute("target", "_blank");
      a.setAttribute("rel", "noopener");
    });
  }

  // Auto-show the top of the graph (a CustomerJourney if available, else first concept)
  const initial =
    bundle.nodes.find((n) => n.data.type === "CustomerJourney") ||
    bundle.nodes[0];
  if (initial) showDetail(initial.data.id);
})();
