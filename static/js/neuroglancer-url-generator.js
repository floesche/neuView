/**
 * Neuroglancer URL Generator
 *
 * This module provides functionality to generate Neuroglancer URLs dynamically
 * on the client side, replacing server-side template generation.
 * The template is embedded directly for file:// URL compatibility.
 */

// Embedded neuroglancer template - complete configuration as JavaScript object
const NEUROGLANCER_TEMPLATE = {
  title: "WEBSITE_TITLE_PLACEHOLDER",
  dimensions: { x: [8e-9, "m"], y: [8e-9, "m"], z: [8e-9, "m"] },
  position: [48850.046875, 31780.1796875, 26790.14453125],
  crossSectionScale: 132.13536694825854,
  projectionScale: 74323.4144763075,
  layers: [
    {
      type: "image",
      source: {
        url: "precomputed://gs://cns-full-clahe",
        subsources: { default: true },
        enableDefaultSubsources: false,
      },
      tab: "source",
      name: "em-clahe",
    },
    {
      type: "segmentation",
      source: [
        {
          url: "dvid://https://emdata-mcns.janelia.org/f3969:master/segmentation?dvid-service=https://ngsupport-bmcp5imp6q-uk.a.run.app",
          subsources: { default: true, meshes: true },
          enableDefaultSubsources: false,
        },
        {
          url: "precomputed://https://ngsupport-bmcp5imp6q-uk.a.run.app/neuronjson_segment_properties/emdata-mcns.janelia.org/f3969:master/segmentation_annotations/type",
          subsources: { default: true },
          enableDefaultSubsources: false,
        },
        {
          url: "#precomputed://https://ngsupport-bmcp5imp6q-uk.a.run.app/neuronjson_segment_properties/emdata-mcns.janelia.org/f3969:master/segmentation_annotations/type/status",
          enableDefaultSubsources: false,
        },
        {
          url: "precomputed://https://ngsupport-bmcp5imp6q-uk.a.run.app/neuronjson_segment_tags_properties/emdata-mcns.janelia.org/f3969:master/segmentation_annotations/soma_side",
          subsources: { default: true },
          enableDefaultSubsources: false,
        },
        {
          url: "#precomputed://https://ngsupport-bmcp5imp6q-uk.a.run.app/neuronjson_segment_synapse_properties/emdata-mcns.janelia.org/f3969:master/synapses_labelsz/250000",
          enableDefaultSubsources: false,
        },
        {
          url: "#precomputed://https://ngsupport-bmcp5imp6q-uk.a.run.app/neuronjson_segment_note_properties/emdata-mcns.janelia.org/f3969:master/neck-fibers-anterior_labelsz/neck-ant/5000",
          enableDefaultSubsources: false,
        },
        {
          url: "#precomputed://https://ngsupport-bmcp5imp6q-uk.a.run.app/neuronjson_segment_note_properties/emdata-mcns.janelia.org/f3969:master/neck-fibers-posterior_labelsz/neck-post/5000",
          enableDefaultSubsources: false,
        },
        {
          url: "#precomputed://https://ngsupport-bmcp5imp6q-uk.a.run.app/neuronjson_segment_note_properties/emdata-mcns.janelia.org/f3969:master/nuclei-centroids_labelsz/nuclei/200000",
          enableDefaultSubsources: false,
        },
        {
          url: "#precomputed://https://ngsupport-bmcp5imp6q-uk.a.run.app/neuronjson_segment_note_properties/emdata-mcns.janelia.org/f3969:master/segmentation_todo_labelsz/todo/200000",
          enableDefaultSubsources: false,
        },
        {
          url: "precomputed://https://ngsupport-bmcp5imp6q-uk.a.run.app/svmesh/emdata-mcns.janelia.org/f3969:master/segmentation_sv_meshes/body",
          enableDefaultSubsources: false,
        },
      ],
      toolBindings: { Q: "selectSegments" },
      tab: "segments",
      segments: "VISIBLE_NEURONS_PLACEHOLDER",
      segmentQuery: "NEURON_QUERY_PLACEHOLDER",
      name: "cns-seg",
    },
    {
      type: "segmentation",
      source: [
        {
          url: "dvid://https://emdata-mcns.janelia.org/f3969:master/segmentation?dvid-service=https://ngsupport-bmcp5imp6q-uk.a.run.app&supervoxels=true",
          subsources: { default: true },
          enableDefaultSubsources: false,
        },
        "precomputed://https://ngsupport-bmcp5imp6q-uk.a.run.app/svmesh/emdata-mcns.janelia.org/f3969:master/segmentation_sv_meshes/supervoxels",
      ],
      tab: "segments",
      name: "supervoxels",
      archived: true,
    },
    {
      type: "segmentation",
      source: {
        url: "dvid://https://emdata-mcns.janelia.org/f3969:master/segmentation_mirrored",
        subsources: { meshes: true },
        enableDefaultSubsources: false,
      },
      tab: "segments",
      linkedSegmentationGroup: "cns-seg",
      name: "brain-mirror",
      archived: true,
    },
    {
      type: "segmentation",
      source: {
        url: "precomputed://gs://flyem-cns-roi-7c971aa681da83f9a074a1f0e8ef60f4/fullbrain-major-shells",
        subsources: { default: true, properties: true, mesh: true },
        enableDefaultSubsources: false,
      },
      pick: false,
      tab: "rendering",
      selectedAlpha: 0,
      saturation: 0,
      meshSilhouetteRendering: 7,
      segments: ["1", "2", "3"],
      colorSeed: 1336242844,
      segmentDefaultColor: "#ffffff",
      name: "brain-neuropil-shell",
    },
    {
      type: "segmentation",
      source: {
        url: "precomputed://gs://flyem-cns-roi-7c971aa681da83f9a074a1f0e8ef60f4/brain-shell-v2.2",
        subsources: { default: true, properties: true, mesh: true },
        enableDefaultSubsources: false,
      },
      pick: false,
      tab: "rendering",
      selectedAlpha: 0,
      saturation: 0,
      meshSilhouetteRendering: 7,
      segments: ["1"],
      colorSeed: 1336242844,
      segmentDefaultColor: "#ffffff",
      name: "brain-shell",
      archived: true,
    },
    {
      type: "segmentation",
      source: {
        url: "precomputed://gs://flyem-cns-roi-7c971aa681da83f9a074a1f0e8ef60f4/brain-shell-with-lamina-v2.1",
        subsources: { default: true, properties: true, mesh: true },
        enableDefaultSubsources: false,
      },
      pick: false,
      tab: "rendering",
      selectedAlpha: 0,
      saturation: 0,
      meshSilhouetteRendering: 7,
      segments: ["1"],
      colorSeed: 1336242844,
      segmentDefaultColor: "#ffffff",
      name: "brain-shell-with-lamina",
      archived: true,
    },
    {
      type: "segmentation",
      source: {
        url: "precomputed://gs://flyem-cns-roi-7c971aa681da83f9a074a1f0e8ef60f4/vnc-neuropil-shell",
        subsources: { default: true, properties: true, mesh: true },
        enableDefaultSubsources: false,
      },
      pick: false,
      tab: "rendering",
      selectedAlpha: 0,
      saturation: 0,
      meshSilhouetteRendering: 7,
      segments: ["1"],
      colorSeed: 1336242844,
      segmentDefaultColor: "#ffffff",
      name: "vnc-neuropil-shell",
    },
    {
      type: "segmentation",
      source: {
        url: "precomputed://gs://flyem-cns-roi-7c971aa681da83f9a074a1f0e8ef60f4/vnc-shell",
        subsources: { default: true, properties: true, mesh: true },
        enableDefaultSubsources: false,
      },
      pick: false,
      tab: "rendering",
      selectedAlpha: 0,
      saturation: 0,
      meshSilhouetteRendering: 7,
      segments: ["1"],
      colorSeed: 1336242844,
      segmentDefaultColor: "#ffffff",
      name: "vnc-shell",
      archived: true,
    },
    {
      type: "segmentation",
      source: {
        url: "precomputed://gs://flyem-cns-roi-7c971aa681da83f9a074a1f0e8ef60f4/fullbrain-roi-v4",
        subsources: { default: true, properties: true, mesh: true },
        enableDefaultSubsources: false,
      },
      pick: false,
      tab: "segments",
      selectedAlpha: 0,
      meshSilhouetteRendering: 4,
      segments: [
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
        "78",
        "79",
        "8",
        "80",
        "81",
        "82",
        "83",
        "84",
        "85",
        "86",
        "9",
        "93",
        "94",
        "95",
        "96",
      ],
      name: "brain-neuropils",
      visible: false,
    },
    {
      type: "segmentation",
      source: {
        url: "precomputed://gs://flyem-cns-roi-7c971aa681da83f9a074a1f0e8ef60f4/malecns-vnc-neuropil-roi-v0",
        subsources: { default: true, properties: true, mesh: true },
        enableDefaultSubsources: false,
      },
      pick: false,
      tab: "segments",
      selectedAlpha: 0,
      meshSilhouetteRendering: 4,
      segments: [
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
        "20",
        "21",
        "22",
        "23",
        "24",
        "25",
        "26",
        "27",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
      ],
      name: "vnc-neuropils",
      visible: false,
    },
    {
      type: "segmentation",
      source: {
        url: "precomputed://gs://flyem-cns-roi-7c971aa681da83f9a074a1f0e8ef60f4/malecns-vnc-nerve-roi-v2",
        subsources: { default: true, properties: true, mesh: true },
        enableDefaultSubsources: false,
      },
      pick: false,
      tab: "segments",
      meshSilhouetteRendering: 3,
      segments: [
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
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
      ],
      name: "vnc-nerves",
      archived: true,
    },
    {
      type: "segmentation",
      source: {
        url: "precomputed://gs://flyem-cns-roi-7c971aa681da83f9a074a1f0e8ef60f4/malecns-major-compartments-v1",
        subsources: { default: true, properties: true, mesh: true },
        enableDefaultSubsources: false,
      },
      tab: "segments",
      meshSilhouetteRendering: 4,
      name: "major-compartments",
      archived: true,
    },
    {
      type: "segmentation",
      source: [
        "precomputed://gs://flyem-cns-roi-7c971aa681da83f9a074a1f0e8ef60f4/pointcloud-shells",
        "precomputed://gs://flyem-cns-roi-7c971aa681da83f9a074a1f0e8ef60f4/pointcloud-shells/segment_props",
      ],
      pick: false,
      tab: "rendering",
      selectedAlpha: 0,
      saturation: 0,
      segments: ["1", "2"],
      colorSeed: 1336242844,
      segmentDefaultColor: "#ffffff",
      name: "pointcloud-shells",
      archived: true,
    },
    {
      type: "annotation",
      source: "dvid://https://emdata-mcns.janelia.org/f3969:master/synapses",
      tab: "rendering",
      shader:
        '#uicontrol bool show_tbars checkbox(default=true)\n#uicontrol bool show_psds checkbox(default=true)\n#uicontrol float confidence_threshold slider(min=0.0, max=1.0, step=0.1, default=0.5)\n\n#uicontrol float radius slider(min=3, max=20, step=1, default=5)\n#uicontrol float opacity slider(min=0, max=1, step=0.1, default=1)\n#uicontrol float opacity3D slider(min=0, max=1, step=0.1, default=1)\n#uicontrol vec3 tbar_color color(default="#FFFF00")\n#uicontrol vec3 psd_color color(default="#808080")\n\nvoid main() {\n  if (prop_confidence() < confidence_threshold) {\n      discard;\n  }\n\n  setPointMarkerSize(radius);\n  float final_opacity = PROJECTION_VIEW ? opacity3D : opacity;\n  setPointMarkerBorderColor(vec4(0, 0, 0, final_opacity));\n\n  if (prop_rendering_attribute() == 4) {\n    if (!show_tbars)\n      discard;\n    setColor(vec4(tbar_color, final_opacity));\n  } else if (prop_rendering_attribute() == 5) {\n    if (!show_psds)\n      discard;\n    setColor(vec4(psd_color, final_opacity));\n  } else {\n    setColor(vec4(defaultColor(), final_opacity));\n  }\n}\n',
      linkedSegmentationLayer: { segments: "cns-seg" },
      filterBySegmentation: ["segments"],
      name: "synapses",
      visible: false,
    },
    {
      type: "segmentation",
      source: {
        url: "dvid://https://emdata-mcns.janelia.org/f3969:master/nuclei-seg?dvid-service=https://ngsupport-bmcp5imp6q-uk.a.run.app",
        subsources: { default: true, meshes: true, bounds: true },
        enableDefaultSubsources: false,
      },
      tab: "segments",
      name: "nuclei-seg",
      archived: true,
    },
    {
      type: "annotation",
      source:
        "dvid://https://emdata-mcns.janelia.org/f3969:master/nuclei-centroids",
      tab: "rendering",
      shader:
        '#uicontrol float radius slider(min=3, max=20, step=1, default=5)\n#uicontrol float opacity slider(min=0, max=1, step=0.1, default=1)\n#uicontrol float opacity3D slider(min=0, max=1, step=0.1, default=1)\n#uicontrol vec3 color color(default="#FFFFFF")\n\t\nvoid main() {\n  setPointMarkerSize(radius);\n  float finalOpacity = PROJECTION_VIEW ? opacity3D : opacity;\n  setPointMarkerBorderColor(vec4(0, 0, 0, finalOpacity));\n  setColor(vec4(color, finalOpacity));\n}\n',
      shaderControls: { radius: 20 },
      linkedSegmentationLayer: { segments: "cns-seg" },
      filterBySegmentation: ["segments"],
      name: "nuclei-centroids",
      archived: true,
    },
    {
      type: "annotation",
      source: "dvid://https://emdata-mcns.janelia.org/f3969:master/tosoma",
      tab: "rendering",
      shader:
        '#uicontrol float radius slider(min=3, max=20, step=1, default=5)\n#uicontrol float opacity slider(min=0, max=1, step=0.1, default=1)\n#uicontrol float opacity3D slider(min=0, max=1, step=0.1, default=1)\n#uicontrol vec3 color color(default="#FFFFFF")\n\t\nvoid main() {\n  setPointMarkerSize(radius);\n  float finalOpacity = PROJECTION_VIEW ? opacity3D : opacity;\n  setPointMarkerBorderColor(vec4(0, 0, 0, finalOpacity));\n  setColor(vec4(color, finalOpacity));\n}\n',
      shaderControls: { radius: 10, color: "#00ffff" },
      linkedSegmentationLayer: { segments: "cns-seg" },
      filterBySegmentation: ["segments"],
      name: "tosoma-points",
      archived: true,
    },
    {
      type: "segmentation",
      source: [
        "dvid://https://emdata-mcns.janelia.org/f3969dc/semantic-masks-cns?dvid-service=https://ngsupport-bmcp5imp6q-uk.a.run.app",
        "precomputed://https://emdata-mcns.janelia.org/api/node/f3969dc/semantic-masks-ng-segprops/key/cns-segprops-info",
      ],
      tab: "segments",
      segmentColors: { 0: "#000000" },
      name: "semantic-masks",
      archived: true,
    },
    {
      type: "segmentation",
      source: {
        url: "precomputed://gs://flyem-cns-roi-7c971aa681da83f9a074a1f0e8ef60f4/fullbrain-defects",
        subsources: { default: true, properties: true, mesh: true },
        enableDefaultSubsources: false,
      },
      tab: "segments",
      meshSilhouetteRendering: 2,
      segments: ["1", "2", "3", "4", "5"],
      name: "brain-defects",
      archived: true,
    },
    {
      type: "segmentation",
      source: {
        url: "precomputed://gs://flyem-cns-roi-7c971aa681da83f9a074a1f0e8ef60f4/vnc-defects",
        subsources: { default: true, properties: true, mesh: true },
        enableDefaultSubsources: false,
      },
      pick: false,
      tab: "segments",
      meshSilhouetteRendering: 2,
      segments: ["1", "2"],
      name: "vnc-defects",
      archived: true,
    },
    {
      type: "annotation",
      source: {
        url: "local://annotations",
        transform: {
          outputDimensions: {
            x: [8e-9, "m"],
            y: [8e-9, "m"],
            z: [8e-9, "m"],
          },
        },
      },
      tool: "annotatePoint",
      tab: "annotations",
      annotations: [
        {
          pointA: [39298, 0, 9578],
          pointB: [41856, 55296, 40316],
          type: "axis_aligned_bounding_box",
          id: "7ec7d4d742ac94ed304f4b1d9c535a162c947ab4",
        },
        {
          pointA: [4125.13134765625, 20381.453125, 28350.43359375],
          pointB: [6771, 48774.40625, 44534.76953125],
          type: "axis_aligned_bounding_box",
          id: "dde25826ea384cdc8d89f22f28dc7f5992c43830",
        },
      ],
      name: "realigned-tabs",
      archived: true,
    },
    {
      type: "segmentation",
      source: {
        url: "precomputed://gs://flyem-cns-roi-7c971aa681da83f9a074a1f0e8ef60f4/halfbrain-roi",
        transform: {
          matrix: [
            [1, 0, 0, 4096],
            [0, 1, 0, 4096],
            [0, 0, 1, 4096],
          ],
          outputDimensions: {
            x: [8e-9, "m"],
            y: [8e-9, "m"],
            z: [8e-9, "m"],
          },
        },
        subsources: { default: true, properties: true, mesh: true },
        enableDefaultSubsources: false,
      },
      pick: false,
      tab: "segments",
      selectedAlpha: 0.63,
      saturation: 0.5,
      meshSilhouetteRendering: 4,
      segments: [
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
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
      ],
      name: "halfbrain-orig-roi",
      archived: true,
    },
    {
      type: "annotation",
      source:
        "dvid://https://emdata-mcns.janelia.org/f3969:master/neck-fibers-anterior",
      tab: "source",
      annotationColor: "#ff00ff",
      crossSectionAnnotationSpacing: 55.39433990439313,
      projectionAnnotationSpacing: 64,
      linkedSegmentationLayer: { segments: "cns-seg" },
      filterBySegmentation: ["segments"],
      name: "neck-ant",
      archived: true,
    },
    {
      type: "annotation",
      source:
        "dvid://https://emdata-mcns.janelia.org/f3969:master/neck-fibers-posterior",
      tab: "source",
      annotationColor: "#ff00ff",
      crossSectionAnnotationSpacing: 55.39433990439313,
      projectionAnnotationSpacing: 64,
      linkedSegmentationLayer: { segments: "cns-seg" },
      filterBySegmentation: ["segments"],
      name: "neck-post",
      archived: true,
    },
    {
      type: "annotation",
      source: {
        url: "precomputed://gs://cns-connectivity-labels",
        subsources: { default: true },
        enableDefaultSubsources: false,
      },
      filterBySegmentation: ["cns-seg"],
      ignoreNullSegmentFilter: false,
      shader: "#uicontrol invlerp normalized",
      shaderControls: {},
      linkedSegmentationGroup: "cns-seg",
      name: "connectivity-labels",
      archived: true,
    },
  ],
  selectedLayer: { visible: true, layer: "cns-seg" },
  layout: "4panel",
};

/**
 * Generates a Neuroglancer URL based on the provided parameters
 *
 * @param {string} websiteTitle - The title for the neuroglancer session
 * @param {string[]} visibleNeurons - Array of neuron bodyIDs to display
 * @param {string} neuronQuery - Query string for neuron search
 * @returns {string} The complete Neuroglancer URL
 */
function generateNeuroglancerUrl(websiteTitle, visibleNeurons, neuronQuery) {
  try {
    // Create a deep copy of the template to avoid modifying the original
    const neuroglancerState = JSON.parse(JSON.stringify(NEUROGLANCER_TEMPLATE));

    // Replace placeholders with actual values
    neuroglancerState.title = websiteTitle;

    // Find the cns-seg layer and update its segments and segmentQuery
    const cnsSegLayer = neuroglancerState.layers.find(
      (layer) => layer.name === "cns-seg",
    );
    if (cnsSegLayer) {
      cnsSegLayer.segments = visibleNeurons;
      cnsSegLayer.segmentQuery = neuronQuery;
    }

    // Convert to JSON string with no spacing to match the original behavior
    const neuroglancerJsonString = JSON.stringify(neuroglancerState, null, 0);

    // URL encode the JSON string
    const encodedState = encodeURIComponent(neuroglancerJsonString);

    // Create the full Neuroglancer URL
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
 * @returns {void}
 */
function updateNeuroglancerLinks(websiteTitle, visibleNeurons, neuronQuery) {
  try {
    const neuroglancerUrl = generateNeuroglancerUrl(
      websiteTitle,
      visibleNeurons,
      neuronQuery,
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

/**
 * Initializes neuroglancer links when the DOM is ready
 * This function should be called with the page data
 *
 * @param {Object} pageData - The page data containing neuroglancer parameters
 * @param {string} pageData.websiteTitle - The title for the neuroglancer session
 * @param {string[]} pageData.visibleNeurons - Array of neuron bodyIDs to display
 * @param {string} pageData.neuronQuery - Query string for neuron search
 */
function initializeNeuroglancerLinks(pageData) {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      updateNeuroglancerLinks(
        pageData.websiteTitle,
        pageData.visibleNeurons,
        pageData.neuronQuery,
      );
    });
  } else {
    updateNeuroglancerLinks(
      pageData.websiteTitle,
      pageData.visibleNeurons,
      pageData.neuronQuery,
    );
  }
}

// Export functions if using modules
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    generateNeuroglancerUrl,
    updateNeuroglancerLinks,
    initializeNeuroglancerLinks,
  };
}
