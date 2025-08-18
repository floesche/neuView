/**
 * Neuroglancer URL Generator
 *
 * This module provides functionality to generate Neuroglancer URLs dynamically
 * on the client side, replacing server-side template generation.
 */

// Cache for the neuroglancer template
let neuroglancerTemplate = null;

/**
 * Loads the neuroglancer template from the static file
 * @returns {Promise<string>} The template content
 */
async function loadNeuroglancerTemplate() {
  if (neuroglancerTemplate === null) {
    try {
      const response = await fetch(
        "static/js/neuroglancer-clean-template.json",
      );
      if (!response.ok) {
        throw new Error(`Failed to load template: ${response.status}`);
      }
      neuroglancerTemplate = await response.text();
    } catch (error) {
      console.error("Error loading neuroglancer template:", error);
      throw error;
    }
  }
  return neuroglancerTemplate;
}

/**
 * Generates a Neuroglancer URL based on the provided parameters
 *
 * @param {string} websiteTitle - The title for the neuroglancer session
 * @param {string[]} visibleNeurons - Array of neuron bodyIDs to display
 * @param {string} neuronQuery - Query string for neuron search
 * @returns {Promise<string>} The complete Neuroglancer URL
 */
async function generateNeuroglancerUrl(
  websiteTitle,
  visibleNeurons,
  neuronQuery,
) {
  try {
    // Load the template
    const template = await loadNeuroglancerTemplate();

    // Replace placeholders in the template
    let neuroglancerJson = template
      .replace(/WEBSITE_TITLE_PLACEHOLDER/g, websiteTitle)
      .replace(/VISIBLE_NEURONS_PLACEHOLDER/g, JSON.stringify(visibleNeurons))
      .replace(/NEURON_QUERY_PLACEHOLDER/g, neuronQuery);

    // Parse and re-stringify to validate JSON and ensure compact format
    const neuroglancerState = JSON.parse(neuroglancerJson);
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
 * @returns {Promise<void>}
 */
async function updateNeuroglancerLinks(
  websiteTitle,
  visibleNeurons,
  neuronQuery,
) {
  try {
    const neuroglancerUrl = await generateNeuroglancerUrl(
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
