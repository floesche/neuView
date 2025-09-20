/**
 * Neuroglancer URL Generator
 *
 * This module provides functionality to generate Neuroglancer URLs dynamically
 * on the client side, replacing server-side template generation.
 * The template is embedded directly for file:// URL compatibility.
 */

// Embedded neuroglancer template - complete configuration as JavaScript object

// Function to detect if current dataset is FAFB based on neuroglancer template layers
function isFAFBDataset() {
  return (
    NEUROGLANCER_TEMPLATE.layers &&
    NEUROGLANCER_TEMPLATE.layers.some(
      (l) => l.type === "segmentation" && l.name === "flywire-fafb:v783b",
    )
  );
}

const NEUROGLANCER_TEMPLATE = {
  title: "WEBSITE_TITLE_PLACEHOLDER",
  dimensions: {
    x: [4e-9, "m"],
    y: [4e-9, "m"],
    z: [4e-8, "m"],
  },
  position: [137941.625, 58115.6171875, 367.5460510253906],
  crossSectionScale: 2,
  projectionScale: 175720.37814796658,
  layers: [
    {
      type: "image",
      source: {
        url: "precomputed://gs://flywire_em/aligned/v1",
        subsources: {
          default: true,
        },
        enableDefaultSubsources: false,
      },
      tab: "rendering",
      name: "em-v1",
    },
    {
      type: "segmentation",
      source: [
        {
          url: "precomputed://gs://flywire_v141_m783",
          subsources: {
            default: true,
            mesh: true,
          },
          enableDefaultSubsources: false,
        },
        "precomputed://gs://flywire-neuprint-artifacts/fafb/v783b/flywire-783b-segment-properties",
      ],
      tab: "segments",
      segments: [],
      segmentQuery: "NEURON_QUERY_PLACEHOLDER",
      name: "flywire-fafb:v783b",
    },
    {
      type: "segmentation",
      source: {
        url: "precomputed://gs://flywire_neuropil_meshes/whole_neuropil/brain_mesh_v3",
        subsources: {
          mesh: true,
        },
        enableDefaultSubsources: false,
      },
      pick: false,
      tab: "rendering",
      meshSilhouetteRendering: 4,
      segments: ["1"],
      segmentDefaultColor: "#ffffff",
      name: "brain",
    },
    {
      type: "segmentation",
      source: {
        url: "precomputed://gs://flywire_neuropil_meshes/neuropils/neuropil_mesh_v141_v6#type=mesh",
        subsources: {
          mesh: true,
        },
        enableDefaultSubsources: false,
      },
      pick: false,
      tab: "segments",
      meshSilhouetteRendering: 4,
      segments: [
        "0",
        "1",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "2",
        "20",
        "21",
        "22",
        "23",
        "24",
        "25",
        "26",
        "27",
        "28",
        "29",
        "3",
        "30",
        "31",
        "32",
        "33",
        "34",
        "35",
        "36",
        "37",
        "38",
        "39",
        "4",
        "40",
        "41",
        "42",
        "43",
        "44",
        "45",
        "46",
        "47",
        "48",
        "49",
        "5",
        "50",
        "51",
        "52",
        "53",
        "54",
        "55",
        "56",
        "57",
        "58",
        "59",
        "6",
        "60",
        "61",
        "62",
        "63",
        "64",
        "65",
        "66",
        "67",
        "68",
        "69",
        "7",
        "70",
        "71",
        "72",
        "73",
        "74",
        "75",
        "76",
        "77",
        "8",
        "9",
      ],
      segmentColors: {
        0: "#fdb95d",
        1: "#ffda59",
        2: "#dd41d3",
        3: "#2081f2",
        4: "#ffae79",
        5: "#274bfe",
        6: "#bc21a2",
        7: "#0dbfc2",
        8: "#07c4ac",
        9: "#50bcfe",
        10: "#ff9e69",
        11: "#5479ef",
        12: "#00b5d3",
        13: "#00957e",
        14: "#8a34d4",
        15: "#fdb95d",
        16: "#3d8ce2",
        17: "#fe9e3e",
        18: "#fead49",
        19: "#febd3b",
        20: "#fe99b8",
        21: "#fe9e3f",
        22: "#4c9efe",
        23: "#fead49",
        24: "#4c9efe",
        25: "#285bfa",
        26: "#603ee4",
        27: "#30d2fe",
        28: "#ffa88d",
        29: "#bc21a2",
        30: "#febd3b",
        31: "#fbb256",
        32: "#00b5d3",
        33: "#fbb256",
        34: "#3d8ce2",
        35: "#10cac8",
        36: "#bc21a2",
        37: "#1a57ee",
        38: "#0dbfc2",
        39: "#1a57ee",
        40: "#02dcc0",
        41: "#ff9e69",
        42: "#ffda59",
        43: "#dd41d3",
        44: "#02dcc0",
        45: "#145ddc",
        46: "#285bfa",
        47: "#fed942",
        48: "#ffa88d",
        49: "#3d89fe",
        50: "#3b8dfe",
        51: "#8a34d4",
        52: "#07c4ac",
        53: "#513bfe",
        54: "#fe99b8",
        55: "#ffae79",
        56: "#bc21a2",
        57: "#30d2fe",
        58: "#21adc4",
        59: "#50bcfe",
        60: "#3b8dfe",
        61: "#000000",
        62: "#fed942",
        63: "#feb13a",
        64: "#00957e",
        65: "#049a93",
        66: "#fe9e3f",
        67: "#fe9e3e",
        68: "#36cfdc",
        69: "#3d89fe",
        70: "#543bfe",
        71: "#145ddc",
        72: "#feb13a",
        73: "#5479ef",
        74: "#274bfe",
        75: "#a21a78",
        76: "#a21a78",
        77: "#ea4bea",
      },
      name: "neuropils",
      visible: false,
    },
    {
      type: "segmentation",
      source: {
        url: "precomputed://gs://neuroglancer/drosophila_v0/nucleus/v5_z_intp_intp/seg",
        subsources: {
          default: true,
          mesh: true,
        },
        enableDefaultSubsources: false,
      },
      tab: "segments",
      name: "nuclei",
      archived: true,
    },
    {
      type: "annotation",
      source:
        "precomputed://gs://flywire-neuprint-artifacts/fafb/v783b/flywire-783b-synapse-annotations",
      tab: "rendering",
      shader:
        '#uicontrol bool show_pre checkbox(default=true)\n#uicontrol bool show_post_partners checkbox(default=false)\n\n#uicontrol vec3 pre_color color(default="red")\n#uicontrol vec3 post_color color(default="blue")\n\n#uicontrol float pre_size slider(min=3, max=20, step=1, default=5)\n#uicontrol float post_size slider(min=3, max=20, step=1, default=5)\n  \nvoid main() {\n  setLineColor(vec3(1.0, 1.0, 1.0));\n\n  setEndpointMarkerColor(\n    vec4(pre_color, 0.5),\n    vec4(post_color, 0.5));\n  \n  if (show_pre && show_post_partners) {\n    setLineWidth(1.0);\n    setEndpointMarkerSize(pre_size, post_size);\n  }\n  else if (show_post_partners) {\n    setLineWidth(0.0);\n    setEndpointMarkerSize(0.0, post_size);\n  }\n  else if (show_pre) {\n    setLineWidth(0.0);\n    setEndpointMarkerSize(pre_size, 0.0);\n  }\n  else {\n    setLineWidth(0.0);\n    setEndpointMarkerSize(0.0, 0.0);\n  }\n  }\n',
      linkedSegmentationLayer: {
        body_pre: "flywire-fafb:v783b",
        body_post: "flywire-fafb:v783b",
      },
      filterBySegmentation: ["body_pre"],
      name: "presyn",
      visible: false,
    },
    {
      type: "annotation",
      source:
        "precomputed://gs://flywire-neuprint-artifacts/fafb/v783b/flywire-783b-synapse-annotations",
      tab: "rendering",
      shader:
        '#uicontrol bool show_pre_partners checkbox(default=false)\n#uicontrol bool show_post checkbox(default=true)\n\n#uicontrol vec3 pre_color color(default="red")\n#uicontrol vec3 post_color color(default="blue")\n\n#uicontrol float pre_size slider(min=3, max=20, step=1, default=5)\n#uicontrol float post_size slider(min=3, max=20, step=1, default=5)\n  \nvoid main() {\n  setLineColor(vec3(1.0, 1.0, 1.0));\n\n  setEndpointMarkerColor(\n    vec4(pre_color, 0.5),\n    vec4(post_color, 0.5));\n  \n  if (show_pre_partners && show_post) {\n    setLineWidth(1.0);\n    setEndpointMarkerSize(pre_size, post_size);\n  }\n  else if (show_post) {\n    setLineWidth(0.0);\n    setEndpointMarkerSize(0.0, post_size);\n  }\n  else if (show_pre_partners) {\n    setLineWidth(0.0);\n    setEndpointMarkerSize(pre_size, 0.0);\n  }\n  else {\n    setLineWidth(0.0);\n    setEndpointMarkerSize(0.0, 0.0);\n  }\n}\n',
      linkedSegmentationLayer: {
        body_pre: "flywire-fafb:v783b",
        body_post: "flywire-fafb:v783b",
      },
      filterBySegmentation: ["body_post"],
      name: "postsyn",
      visible: false,
    },
  ],
  showSlices: false,
  selectedLayer: {
    size: 333,
    visible: true,
    layer: "flywire-fafb:v783b",
  },
  layout: "3d",
};

/* ────────────────────────────────────────────────────────────────────────── */
/* Background colour                                                          */
/* ────────────────────────────────────────────────────────────────────────── */

// Theme → NG projection background color
const BG_BY_THEME = { dark: "#1a1a1a", light: "#ffffff" };
let currentNgTheme = "dark";
let currentProjectionBg = BG_BY_THEME[currentNgTheme];

/* ────────────────────────────────────────────────────────────────────────── */
/* Connectivity partners: click-to-toggle bodyIds per type                    */
/* ──────────────────────────────────────────────────────────────────────────

 * Wire click-to-toggle for upstream/downstream partner types in the connectivity tables.
 * Toggle rule:
 *  - If *all* bodyIds for the clicked type are already selected => remove them (OFF).
 *  - Otherwise => add them all (ON).
 * @param {{
 *   websiteTitle: string,
 *   visibleNeurons?: (string|number)[],
 *   neuronQuery?: string,
 *   visibleRois?: string[]
 * }}
 */

// Robust JSON.parse for data-body-ids
const safeParseIds = (s) => {
  try {
    const v = JSON.parse(s || "[]");
    return Array.isArray(v) ? v : []; // coalesce "null" → []
  } catch {
    return [];
  }
};

/**
 * Get all body IDs that come from connectivity partners
 * @returns {Set<string>} Set of all body IDs from partner cells
 */
function getAllConnectivityBodyIds() {
  const connectivityBodyIds = new Set();
  document.querySelectorAll("td.p-c").forEach((td) => {
    const bodyIds = safeParseIds(td.dataset.bodyIds);
    bodyIds.forEach((id) => connectivityBodyIds.add(String(id)));
  });
  return connectivityBodyIds;
}

/**
 * Check if any connectivity body IDs are currently active in visibleNeurons
 * @param {string[]} visibleNeurons - Array of currently visible neuron IDs
 * @returns {boolean} True if any connectivity body IDs are active
 */
function hasActiveConnectivityBodies(visibleNeurons) {
  const connectivityBodyIds = getAllConnectivityBodyIds();
  const visibleSet = new Set((visibleNeurons || []).map(String));

  console.log(
    "[CONNECTIVITY CHECK] connectivityBodyIds:",
    Array.from(connectivityBodyIds),
    "visibleNeurons:",
    visibleNeurons,
  );

  for (const bodyId of connectivityBodyIds) {
    if (visibleSet.has(bodyId)) {
      console.log(
        "[CONNECTIVITY ACTIVE] Found active connectivity body:",
        bodyId,
      );
      return true;
    }
  }
  return false;
}

function syncConnectivityCheckboxes(pageData, limitToDirection = null) {
  const pd = pageData;
  const selected = new Set((pd.visibleNeurons || []).map(String));
  // define tableSelector safely
  const tableSelector = limitToDirection
    ? limitToDirection === "upstream"
      ? "#upstream-table"
      : "#downstream-table"
    : "";

  const cellSelector = limitToDirection ? `${tableSelector} td.p-c` : "td.p-c";

  document.querySelectorAll(cellSelector).forEach((td) => {
    // Get connected bodyIds from table
    const bodyIds = safeParseIds(td.dataset.bodyIds);

    // Check if bodyIds is empty
    const hasNoBodyIds = bodyIds.length === 0;

    // Determine if all body IDs are currently selected
    const allOn =
      bodyIds.length > 0 && bodyIds.every((id) => selected.has(String(id)));

    // Create or update checkbox
    let checkbox = td.querySelector("input[type='checkbox']");
    if (!checkbox) {
      checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.className = "";
      const plural = bodyIds.length > 1 ? "s" : "";
      checkbox.title = `Toggle neuron ${plural} ${bodyIds.join(" and ")} in neuron visualization (above)`;
      checkbox.setAttribute("aria-label", `Toggle partner`);

      // Create label wrapper
      const label = document.createElement("label");
      label.className = "p-c-label";

      // Move existing content to label and add checkbox before
      const existingContent = td.innerHTML;
      label.innerHTML = existingContent;
      td.innerHTML = "";
      td.appendChild(checkbox);
      td.appendChild(label);
    }

    // Handle empty body IDs case
    if (hasNoBodyIds) {
      console.log("[CHECKBOX] Empty body IDs detected for partner cell:", td);
      checkbox.disabled = true;
      checkbox.checked = false;
      td.classList.add("no-body-ids");
      td.classList.remove("partner-on");
    } else {
      checkbox.disabled = false;
      td.classList.remove("no-body-ids");
      // Update checkbox state
      checkbox.checked = allOn;
      // Apply styling to the wrapper
      td.classList.toggle("partner-on", allOn);
    }
  });
}

function wireConnectivityCheckboxes(pageData) {
  const pd = pageData;

  // Handle user toggles using event delegation
  document.addEventListener("change", (e) => {
    const checkbox = e.target;
    if (!(checkbox instanceof HTMLInputElement) || checkbox.type !== "checkbox")
      return;

    const td = checkbox.closest("td.p-c");
    if (!td) return;

    // Skip interaction if checkbox is disabled (no body IDs)
    if (checkbox.disabled) {
      checkbox.checked = false;
      return;
    }

    // Only this cell’s IDs (keep original number types if provided)
    const cellIds = safeParseIds(td.dataset.bodyIds);
    if (cellIds.length === 0) {
      checkbox.checked = false;
      return;
    }

    // Track user intent
    const intended = checkbox.checked;

    // Build a string Set for comparisons
    const selStrings = new Set((pd.visibleNeurons || []).map(String));

    // Keep a numeric array for storage (important for Neuroglancer)
    let current = Array.isArray(pd.visibleNeurons)
      ? pd.visibleNeurons.slice()
      : [];

    // Helpers to keep string/numeric views consistent
    const addId = (id) => {
      const s = String(id);
      if (!selStrings.has(s)) {
        selStrings.add(s);
        current.push(id); // store numeric
      }
    };
    const removeId = (id) => {
      const s = String(id);
      if (selStrings.has(s)) {
        selStrings.delete(s);
        const idx = current.findIndex((x) => String(x) === s);
        if (idx !== -1) current.splice(idx, 1);
      }
    };

    if (intended) {
      // ON: add only this cell's IDs
      cellIds.forEach(addId);
    } else {
      // OFF: remove this cell’s IDs unless another checked cell still selects them
      const otherSelected = new Set();
      document.querySelectorAll("td.p-c").forEach((otherTd) => {
        if (otherTd === td) return;
        const otherCb = otherTd.querySelector("input[type='checkbox']");
        if (otherCb && otherCb.checked && !otherCb.disabled) {
          const ids = safeParseIds(otherTd.dataset.bodyIds);
          ids.forEach((id) => otherSelected.add(String(id)));
        }
      });

      cellIds.forEach((id) => {
        if (!otherSelected.has(String(id))) removeId(id);
      });
    }

    // Store back numeric IDs (critical for Neuroglancer resolution)
    pd.visibleNeurons = current;

    // Style just this cell
    td.classList.toggle("partner-on", intended);

    const ngVisibleNeurons = Array.isArray(pd.visibleNeurons)
      ? pd.visibleNeurons
      : [];
    const ngVisibleRois = Array.isArray(pd.visibleRois) ? pd.visibleRois : [];
    const ngQuery = typeof pd.neuronQuery === "string" ? pd.neuronQuery : "";

    // Update Neuroglancer
    try {
      updateNeuroglancerLinks(
        pd.websiteTitle,
        pd.visibleNeurons, // numeric IDs
        pd.neuronQuery || "",
        pd.visibleRois || [],
        pd.region || "",
        typeof currentProjectionBg !== "undefined" ? currentProjectionBg : null,
      );
    } catch (err) {
      console.error("[NG] updateNeuroglancerLinks failed:", err);
    }
  });

  // Initial sync
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () =>
      syncConnectivityCheckboxes(pd),
    );
  } else {
    syncConnectivityCheckboxes(pd);
  }

  // Re-sync after DataTables redraws (run once)
  if (window.jQuery && jQuery.fn && jQuery.fn.dataTable) {
    jQuery("#upstream-table, #downstream-table").on("draw.dt", () =>
      syncConnectivityCheckboxes(pd),
    );
    jQuery("#roi-table").on("draw.dt", () => {
      if (typeof syncRoiCheckboxes === "function") syncRoiCheckboxes();
      setTimeout(() => {
        const roiTable = document.getElementById("roi-table");
        if (roiTable) {
          roiTable.style.tableLayout = "fixed";
          roiTable.querySelectorAll("tbody td:first-child").forEach((cell) => {
            cell.style.width = "250px";
            cell.style.maxWidth = "250px";
          });
        }
      }, 10);
    });
  }
}

/* ────────────────────────────────────────────────────────────────────────── */
/* ROI checkboxes: create checkboxes, sync state, handle toggles              */
/* ────────────────────────────────────────────────────────────────────────── */

/**
 * Creates checkboxes for ROI cells and syncs their state with selectedRoiIds
 * For FAFB datasets, skips checkbox creation since neuroglancer data is not reliable
 */
function syncRoiCheckboxes() {
  document.querySelectorAll("td.roi-cell").forEach((td) => {
    const roiName = td.dataset.roiName;
    if (!roiName) return;

    const roiId = roiNameToId(roiName);
    if (!roiId) return;

    // Skip checkbox creation for FAFB datasets - neuroglancer data not reliable
    if (isFAFBDataset()) {
      // Just apply width enforcement for consistent table layout
      td.style.width = "250px";
      td.style.maxWidth = "250px";
      return;
    }

    // Determine if this ROI is currently selected
    const isSelected = selectedRoiIds.has(roiId);

    // Create or update checkbox
    let checkbox = td.querySelector("input[type='checkbox']");
    if (!checkbox) {
      checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.className = "";
      checkbox.setAttribute("aria-label", `Toggle ${roiName}`);

      // Create label wrapper
      const label = document.createElement("label");
      label.className = "roi-cell-label";

      // Move existing content to label and add checkbox before
      const existingContent = td.innerHTML;
      label.innerHTML = existingContent;
      td.innerHTML = "";
      td.appendChild(checkbox);
      td.appendChild(label);
    }

    // Update checkbox state
    checkbox.checked = isSelected;

    // Apply styling to the wrapper
    td.classList.toggle("roi-on", isSelected);

    // Simple width enforcement
    td.style.width = "250px";
    td.style.maxWidth = "250px";
  });
}

/**
 * Wire ROI checkbox event handlers
 * For FAFB datasets, this is a no-op since checkboxes are not created
 */
function wireRoiCheckboxes(pageData) {
  // Skip event handling for FAFB datasets since checkboxes don't exist
  if (isFAFBDataset()) {
    return;
  }

  document.addEventListener("change", (e) => {
    const checkbox = e.target;
    if (!(checkbox instanceof HTMLInputElement)) return;
    if (checkbox.type !== "checkbox") return;
    if (!checkbox.closest("td.roi-cell")) return;

    const td = checkbox.closest("td.roi-cell");
    if (!td) return;

    const roiName = td.dataset.roiName;
    if (!roiName) {
      console.warn("[ROI CHECKBOX] Missing data-roi-name on element:", td);
      checkbox.checked = false;
      return;
    }

    const roiId = roiNameToId(roiName);
    if (!roiId) {
      console.warn("[ROI CHECKBOX] Could not map ROI name to ID:", roiName);
      checkbox.checked = false;
      return;
    }

    console.log(
      "[ROI CHECKBOX] name:",
      roiName,
      " -> id:",
      roiId,
      "checked:",
      checkbox.checked,
    );

    if (checkbox.checked) {
      selectedRoiIds.add(roiId);
      console.log(
        "[ROI TOGGLE] added",
        roiId,
        "current:",
        Array.from(selectedRoiIds),
      );
    } else {
      selectedRoiIds.delete(roiId);
      console.log(
        "[ROI TOGGLE] removed",
        roiId,
        "current:",
        Array.from(selectedRoiIds),
      );
    }

    td.classList.toggle("roi-on", checkbox.checked);

    // Update page data and neuroglancer
    pageData.visibleRois = Array.from(selectedRoiIds);
    console.log("[UPDATE] visibleRois:", pageData.visibleRois);

    updateNeuroglancerLinks(
      pageData.websiteTitle,
      pageData.visibleNeurons,
      pageData.neuronQuery,
      pageData.visibleRois,
      pageData.region,
      currentProjectionBg,
    );
  });
}

/* ────────────────────────────────────────────────────────────────────────── */
/* ROI clicking: map label → segment ID; toggle; style; update NG             */
/* ────────────────────────────────────────────────────────────────────────── */
// --- Make ROI shell visible when clicked on within the ROI table.
//    Eventually retrieve these values programmatically.
const ROI_IDS = [
  1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
  23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41,
  42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60,
  61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79,
  80, 81, 82, 83, 84, 85, 86, 93, 94, 95, 96,
];

const ALL_ROIS = [
  "AL(L)",
  "AL(R)",
  "AME(L)",
  "AME(R)",
  "AMMC(L)",
  "AMMC(R)",
  "AOTU(L)",
  "AOTU(R)",
  "ATL(L)",
  "ATL(R)",
  "AVLP(L)",
  "AVLP(R)",
  "BU(L)",
  "BU(R)",
  "CA(L)",
  "CA(R)",
  "CAN(L)",
  "CAN(R)",
  "CRE(L)",
  "CRE(R)",
  "EB",
  "EPA(L)",
  "EPA(R)",
  "FB",
  "FLA(L)",
  "FLA(R)",
  "GA(L)",
  "GA(R)",
  "GNG",
  "GOR(L)",
  "GOR(R)",
  "IB",
  "ICL(L)",
  "ICL(R)",
  "IPS(L)",
  "IPS(R)",
  "LA(L)",
  "LA(R)",
  "LAL(L)",
  "LAL(R)",
  "LH(L)",
  "LH(R)",
  "LO(L)",
  "LO(R)",
  "LOP(L)",
  "LOP(R)",
  "ME(L)",
  "ME(R)",
  "NO",
  "PB",
  "PED(L)",
  "PED(R)",
  "PLP(L)",
  "PLP(R)",
  "PRW",
  "PVLP(L)",
  "PVLP(R)",
  "ROB(L)",
  "ROB(R)",
  "RUB(L)",
  "RUB(R)",
  "SAD",
  "SCL(L)",
  "SCL(R)",
  "SIP(L)",
  "SIP(R)",
  "SLP(L)",
  "SLP(R)",
  "SMP(L)",
  "SMP(R)",
  "SPS(L)",
  "SPS(R)",
  "VES(L)",
  "VES(R)",
  "WED(L)",
  "WED(R)",
  "a'L(L)",
  "a'L(R)",
  "aL(L)",
  "aL(R)",
  "b'L(L)",
  "b'L(R)",
  "bL(L)",
  "bL(R)",
  "gL(L)",
  "gL(R)",
  "AB(R)",
  "AB(L)",
  "CV-anterior",
  "CRN",
];

if (ROI_IDS.length !== ALL_ROIS.length) {
  console.warn(
    "[ROI MAP] Length mismatch:",
    ROI_IDS.length,
    "ids vs",
    ALL_ROIS.length,
    "labels",
  );
}

const ROI_TO_ID = (() => {
  const map = Object.create(null);
  for (let i = 0; i < Math.min(ROI_IDS.length, ALL_ROIS.length); i++) {
    map[ALL_ROIS[i]] = String(ROI_IDS[i]); // ensure string
  }
  return map;
})();

/**
 * Resolve an ROI label to its Neuroglancer segment ID (as a string).
 *
 * Looks up the label in the prebuilt ROI_TO_ID table. If the label is not found,
 * a warning is logged and `null` is returned (callers should handle this).
 *
 * @param {string} roiName - ROI label, e.g., "ME(R)".
 * @returns {string|null} Segment ID as a string ("1".."96"), or `null` if unknown.
 */
function roiNameToId(roiName) {
  const key = String(roiName).trim();
  const mapped = ROI_TO_ID[key];
  if (mapped) return mapped;

  console.warn("[ROI MAP] Shell for ROI not found:", key);
  return null;
}

/**
 * Recompute which ROI names should be red, given current pageData/selection.
 * @param {{ visibleRois?: string[] }} pageData
 */
function renderRoiLinkStyles(pageData) {
  const layerVisible =
    pageData.visibleRois &&
    pageData.visibleRois.length > 0 &&
    pageData.visibleRois.length < 96;

  // Update legacy roi-link elements if they exist
  document.querySelectorAll(".roi-link").forEach((el) => {
    const roiName = el.getAttribute("data-roi-name");
    if (!roiName) return;

    const roiId = roiNameToId(roiName);
    if (!roiId) return;

    const isSelected = selectedRoiIds.has(roiId);
    const isShown = layerVisible && isSelected;

    el.classList.toggle("roi-on", isShown);
  });

  // Update roi-cell elements
  document.querySelectorAll("td.roi-cell").forEach((td) => {
    const roiName = td.dataset.roiName;
    if (!roiName) return;

    const roiId = roiNameToId(roiName);
    if (!roiId) return;

    const isSelected = selectedRoiIds.has(roiId);
    const isShown = layerVisible && isSelected;

    td.classList.toggle("roi-on", isShown);

    // Update checkbox if it exists
    const checkbox = td.querySelector("input[type='checkbox']");
    if (checkbox) {
      checkbox.checked = isSelected;
    }
  });
}

/** @type {Set<string>} Selected ROI segment IDs (as strings) used for toggling. */
const selectedRoiIds = new Set();

/**
 * Handle clicks on ROI links (class `.roi-link`, attribute `data-roi-name`).
 * Toggles ROI ID in selection, updates pageData.visibleRois, refreshes NG, and restyles.
 * This function is kept for backward compatibility with legacy roi-link elements.
 *
 * @param {Object} pageData - Neuroglancer params object (mutated in place).
 * @param {string} pageData.websiteTitle
 * @param {string[]} pageData.visibleNeurons
 * @param {string} pageData.neuronQuery
 * @param {string[]} pageData.visibleRois
 * @returns {void}
 */
function wireRoiClicks(pageData) {
  const table = document.getElementById("roi-table") || document;

  console.log("[wireRoiClicks] binding to:", table.id || "document");

  table.addEventListener("click", (e) => {
    const el = e.target.closest(".roi-link");
    if (!el) return;

    const roiName = el.getAttribute("data-roi-name");
    if (!roiName) {
      console.warn("[ROI CLICK] Missing data-roi-name on element:", el);
      return;
    }

    const roiId = roiNameToId(roiName);
    console.log("[ROI CLICK] name:", roiName, " -> id:", roiId);

    if (selectedRoiIds.has(roiId)) {
      selectedRoiIds.delete(roiId);
      el.classList.remove("selected");
      console.log(
        "[ROI TOGGLE] removed",
        roiId,
        "current:",
        Array.from(selectedRoiIds),
      );
    } else {
      selectedRoiIds.add(roiId);
      el.classList.add("selected");
      console.log(
        "[ROI TOGGLE] added",
        roiId,
        "current:",
        Array.from(selectedRoiIds),
      );
    }

    pageData.visibleRois = Array.from(selectedRoiIds);
    console.log("[UPDATE] visibleRois:", pageData.visibleRois);

    updateNeuroglancerLinks(
      pageData.websiteTitle,
      pageData.visibleNeurons,
      pageData.neuronQuery,
      pageData.visibleRois,
      pageData.region,
      currentProjectionBg,
    );
    renderRoiLinkStyles(pageData);
  });
}

/* ────────────────────────────────────────────────────────────────────────── */
/* Neuroglancer URL generation + DOM updates                                  */
/* ────────────────────────────────────────────────────────────────────────── */

/**
 * Generates a Neuroglancer URL based on the provided parameters
 *
 * @param {string} websiteTitle - The title for the neuroglancer session
 * @param {string[]} visibleNeurons - Array of neuron bodyIDs to display
 * @param {string} neuronQuery - Query string for neuron search
 * @param {string[]} visibleRois - List of numbers as strings representing visible ROIs
 * @param {string[]} region - Region the type belongs to. Used for setting NG view.
 * @param {string} projectionBg - Background color for projection
 * @returns {string} The complete Neuroglancer URL
 */
// Inside generateNeuroglancerUrl
function generateNeuroglancerUrl(
  websiteTitle,
  visibleNeurons = [],
  neuronQuery = "",
  visibleRois = [],
  region = "",
  projectionBg = currentProjectionBg,
) {
  try {
    const neuroglancerState = JSON.parse(JSON.stringify(NEUROGLANCER_TEMPLATE));
    neuroglancerState.title = websiteTitle;
    neuroglancerState.projectionBackgroundColor = projectionBg;

    // Check if this is FAFB dataset by looking for the flywire-fafb layer
    const isFAFB = neuroglancerState.layers.some(
      (l) => l.type === "segmentation" && l.name === "flywire-fafb:v783b",
    );

    // Choose NG view based on dataset type and region
    if (isFAFB) {
      // For FAFB dataset, preserve the original position, scale, and orientation from template
      // These values are already set in the template, so we don't need to modify them
    } else if (region === "VNC") {
      // VNC-specific settings for CNS dataset
      neuroglancerState.position = [49613.625, 31780.240234375, 76198.75];
      neuroglancerState.projectionOrientation = [
        0.7071970105171204, 0.0005355576286092401, 0.0005249528330750763,
        0.707016110420227,
      ];
      neuroglancerState.projectionScale = 134532.41491591922;
    } else {
      // Other CNS regions (non-VNC)
      neuroglancerState.position = [
        48850.046875, 31780.1796875, 26790.14453125,
      ];
      neuroglancerState.projectionOrientation = [];
      neuroglancerState.projectionScale = 74323.4144763075;
    }

    // Find the main segmentation layer (flexible for different datasets)
    const mainSegLayer = neuroglancerState.layers.find(
      (l) =>
        l.type === "segmentation" &&
        l.segments !== undefined &&
        (l.name === "cns-seg" || l.name === "flywire-fafb:v783b"),
    );

    // Find the neuropil layer (flexible for different datasets)
    const neuropilLayer = neuroglancerState.layers.find(
      (l) => l.name === "brain-neuropils" || l.name === "neuropils",
    );

    // Add ROIs
    const rois = Array.isArray(visibleRois)
      ? visibleRois.map(String)
      : visibleRois
        ? [String(visibleRois)]
        : [];
    if (mainSegLayer) {
      mainSegLayer.segments = Array.isArray(visibleNeurons)
        ? visibleNeurons
        : [];

      // Clear segmentQuery if any connectivity body IDs are active
      const hasConnectivityBodies = hasActiveConnectivityBodies(visibleNeurons);
      console.log(
        "[SEGMENT QUERY] hasConnectivityBodies:",
        hasConnectivityBodies,
        "segmentQuery:",
        hasConnectivityBodies ? "CLEARED" : neuronQuery || "",
        "layerName:",
        mainSegLayer.name,
      );
      mainSegLayer.segmentQuery = hasConnectivityBodies
        ? ""
        : neuronQuery || "";
    }
    if (neuropilLayer) {
      neuropilLayer.segments = rois;
      neuropilLayer.visible = rois.length > 0;
    }

    console.log(
      "[generateNeuroglancerUrl] rois:",
      rois,
      "visible:",
      neuropilLayer?.visible,
    );

    const encodedState = encodeURIComponent(JSON.stringify(neuroglancerState));
    return `https://clio-ng.janelia.org/#!${encodedState}`;
  } catch (error) {
    console.error("Error generating neuroglancer URL:", error);
    throw error;
  }
}

/**
 * Updates neuroglancer links in the DOM with the provided parameters
 *
 * @param {string} websiteTitle - The title for the neuroglancer session
 * @param {string[]} visibleNeurons - Array of neuron bodyIDs to display
 * @param {string} neuronQuery - Query string for neuron search
 * @param {string[]} visibleRois - List of numbers as strings representing visible ROIs
 * @param {string[]} region - Region the type belongs to. Used for setting NG view.
 * @param {string} projectionBg - Background color for projection
 * @returns {void}
 */
function updateNeuroglancerLinks(
  websiteTitle,
  visibleNeurons = [],
  neuronQuery = "",
  visibleRois = [],
  region = "",
  projectionBg = currentProjectionBg,
) {
  try {
    const neuroglancerUrl = generateNeuroglancerUrl(
      websiteTitle,
      visibleNeurons,
      neuronQuery,
      visibleRois,
      region,
      projectionBg,
    );

    // Update all elements with class 'neuroglancer-link'
    const linkElements = document.querySelectorAll(".neuroglancer-link");
    linkElements.forEach((element) => {
      element.href = neuroglancerUrl;
    });

    // Update all elements with class 'neuroglancer-iframe'
    const iframeElements = document.querySelectorAll(".neuroglancer-iframe");
    iframeElements.forEach((element) => {
      element.src = neuroglancerUrl;
    });
  } catch (error) {
    console.error("Error updating neuroglancer links:", error);
  }
}

/* ────────────────────────────────────────────────────────────────────────── */
/* Initialization                                                             */
/* ────────────────────────────────────────────────────────────────────────── */
/** Initializes neuroglancer links when the DOM is ready
 * This function should be called with the page data
 *
 * @param {Object} pageData - The page data containing neuroglancer parameters
 * @param {string} pageData.websiteTitle - The title for the neuroglancer session
 * @param {string[]} pageData.visibleNeurons - Array of neuron bodyIDs to display
 * @param {string} pageData.neuronQuery - Query string for neuron search
 * @param {string[]} pageData.visibleRois - Array of ROIs to display
 * @param {string[]} pageData.region - Region the type belongs to. Used for setting NG view.
 */
// During init
function initializeNeuroglancerLinks(pageData) {
  const run = () => {
    const input = document.getElementById("nv-theme-toggle");
    const saved = localStorage.getItem("nvTheme");
    const initialTheme = saved || (input && input.checked ? "light" : "dark");

    currentNgTheme = initialTheme;
    currentProjectionBg = BG_BY_THEME[initialTheme] || BG_BY_THEME.dark;
    if (input) input.checked = initialTheme === "light";

    updateNeuroglancerLinks(
      pageData.websiteTitle,
      pageData.visibleNeurons,
      pageData.neuronQuery,
      pageData.visibleRois,
      pageData.region,
      currentProjectionBg,
    );
    wireRoiClicks(pageData);
    wireConnectivityCheckboxes(pageData);
    syncConnectivityCheckboxes(pageData);
    wireRoiCheckboxes(pageData);
    syncRoiCheckboxes();

    if (input) {
      input.addEventListener("change", () => {
        currentNgTheme = input.checked ? "light" : "dark";
        currentProjectionBg = BG_BY_THEME[currentNgTheme];
        localStorage.setItem("nvTheme", currentNgTheme);

        updateNeuroglancerLinks(
          pageData.websiteTitle,
          pageData.visibleNeurons,
          pageData.neuronQuery,
          pageData.visibleRois,
          pageData.region,
          currentProjectionBg,
        );
      });
    }
  };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }
}

// Export functions if using modules
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    generateNeuroglancerUrl,
    updateNeuroglancerLinks,
    initializeNeuroglancerLinks,
    wireRoiClicks,
    syncConnectivityCheckboxes,
    wireConnectivityCheckboxes,
    syncRoiCheckboxes,
    wireRoiCheckboxes,
    getAllConnectivityBodyIds,
    hasActiveConnectivityBodies,
  };
}

// Simple ROI table layout fix on page load
function forceRoiTableLayout() {
  const roiTable = document.getElementById("roi-table");
  if (!roiTable) return;

  roiTable.style.tableLayout = "fixed";
  const firstColumnCells = roiTable.querySelectorAll("tbody td:first-child");
  firstColumnCells.forEach((cell) => {
    cell.style.width = "250px";
    cell.style.maxWidth = "250px";
  });
}

// Run on page load
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", forceRoiTableLayout);
} else {
  forceRoiTableLayout();
}
