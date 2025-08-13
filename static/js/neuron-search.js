/**
 * Neuron Type Search and Autocomplete
 * Provides client-side search functionality for neuron types from queue.yaml
 */

class NeuronSearch {
  constructor(inputId = "menulines") {
    this.inputElement = document.getElementById(inputId);
    this.neuronTypes = [];
    this.filteredTypes = [];
    this.currentIndex = -1;
    this.isDropdownVisible = false;

    // Create autocomplete dropdown
    this.dropdown = this.createDropdown();

    // Initialize the search functionality
    this.init();
  }

  /**
   * Initialize the search functionality
   */
  async init() {
    if (!this.inputElement) {
      console.warn("Search input element not found");
      return;
    }

    // Load neuron types from queue.yaml
    await this.loadNeuronTypes();

    // Set up event listeners
    this.setupEventListeners();

    console.log(`Loaded ${this.neuronTypes.length} neuron types for search`);
  }

  /**
   * Create the autocomplete dropdown element
   */
  createDropdown() {
    const dropdown = document.createElement("div");
    dropdown.className = "neuron-search-dropdown";
    dropdown.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ddd;
            border-top: none;
            border-radius: 0 0 4px 4px;
            max-height: 200px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        `;

    // Insert dropdown after the input element
    const parent = this.inputElement.parentNode;
    parent.style.position = "relative";
    parent.appendChild(dropdown);

    return dropdown;
  }

  /**
   * Load neuron types from queue.yaml
   */
  async loadNeuronTypes() {
    try {
      // Try to load from the queue.yaml file
      const response = await fetch(".queue/queue.yaml");

      if (response.ok) {
        const yamlText = await response.text();
        this.neuronTypes = this.parseYaml(yamlText);
        console.log("Loaded neuron types from queue.yaml");
      } else if (response.status === 404) {
        // Queue file doesn't exist, try to discover from available files
        console.log("queue.yaml not found, attempting file discovery");
        await this.discoverFromFiles();
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.warn("Error loading neuron types:", error);
      // Use fallback list if everything fails
      this.neuronTypes = this.getFallbackTypes();
      console.log("Using fallback neuron types list");
    }
  }

  /**
   * Simple YAML parser for neuron_types list
   */
  parseYaml(yamlText) {
    const lines = yamlText.split("\n");
    const neuronTypes = [];
    let inNeuronTypes = false;

    for (const line of lines) {
      const trimmedLine = line.trim();

      if (trimmedLine === "neuron_types:") {
        inNeuronTypes = true;
        continue;
      }

      if (inNeuronTypes) {
        if (trimmedLine.startsWith("- ")) {
          // Extract neuron type name
          const neuronType = trimmedLine.substring(2).trim();
          if (neuronType) {
            neuronTypes.push(neuronType);
          }
        } else if (trimmedLine && !trimmedLine.startsWith(" ")) {
          // End of neuron_types section
          break;
        }
      }
    }

    return neuronTypes.sort();
  }

  /**
   * Discover neuron types from existing HTML files
   */
  async discoverFromFiles() {
    try {
      // Try to find HTML files that might be neuron type pages
      const commonNeuronTypes = this.getFallbackTypes();
      const discoveredTypes = [];

      // Test for common naming patterns
      for (const type of commonNeuronTypes) {
        const possibleUrls = [
          `${type}.html`,
          `${type.toLowerCase()}.html`,
          `${type}_both.html`,
          `${type.toLowerCase()}_both.html`,
        ];

        for (const url of possibleUrls) {
          try {
            const response = await fetch(url, { method: "HEAD" });
            if (response.ok) {
              discoveredTypes.push(type);
              break; // Found one, move to next type
            }
          } catch (e) {
            // Ignore individual file check errors
            continue;
          }
        }
      }

      this.neuronTypes =
        discoveredTypes.length > 0 ? discoveredTypes : this.getFallbackTypes();
      console.log(
        `Discovered ${this.neuronTypes.length} neuron types from file structure`,
      );
    } catch (error) {
      console.warn("File discovery failed:", error);
      this.neuronTypes = this.getFallbackTypes();
    }
  }

  /**
   * Fallback neuron types list
   */
  getFallbackTypes() {
    return [
      "Dm1",
      "Dm2",
      "Dm3",
      "Dm4",
      "Dm5",
      "Dm6",
      "Dm7",
      "Dm8",
      "Dm9",
      "Dm10",
      "Dm11",
      "Dm12",
      "LC4",
      "LC6",
      "LC9",
      "LC10",
      "LC10a",
      "LC10b",
      "LC10c",
      "LC10d",
      "LC11",
      "LC12",
      "LC13",
      "LC14",
      "LC15",
      "LC16",
      "LC17",
      "LC18",
      "LC20",
      "LC21",
      "LC22",
      "LC24",
      "LC25",
      "LC26",
      "LC27",
      "LPLC1",
      "LPLC2",
      "LPLC4",
      "LT10",
      "LT11",
      "LT60",
      "LT61",
      "Mi1",
      "Mi4",
      "Mi9",
      "Mi15",
      "Tm1",
      "Tm2",
      "Tm3",
      "Tm4",
      "Tm5a",
      "Tm5b",
      "Tm5c",
      "Tm6",
      "Tm7",
      "Tm8",
      "Tm9",
      "Tm16",
      "Tm20",
      "Tm27",
      "Tm28",
      "TmY3",
      "TmY4",
      "TmY5a",
      "TmY9",
      "TmY10",
      "TmY13",
      "TmY14",
      "TmY15",
      "T4a",
      "T4b",
      "T4c",
      "T4d",
      "T5a",
      "T5b",
      "T5c",
      "T5d",
    ].sort();
  }

  /**
   * Set up event listeners for the search functionality
   */
  setupEventListeners() {
    // Input event for real-time search
    this.inputElement.addEventListener("input", (e) => {
      this.handleInput(e.target.value);
    });

    // Keyboard navigation
    this.inputElement.addEventListener("keydown", (e) => {
      this.handleKeyDown(e);
    });

    // Focus and blur events
    this.inputElement.addEventListener("focus", () => {
      if (this.inputElement.value.trim()) {
        this.showDropdown();
      }
    });

    this.inputElement.addEventListener("blur", () => {
      // Delay hiding to allow click on dropdown items
      setTimeout(() => this.hideDropdown(), 150);
    });

    // Click outside to close dropdown
    document.addEventListener("click", (e) => {
      if (
        !this.inputElement.contains(e.target) &&
        !this.dropdown.contains(e.target)
      ) {
        this.hideDropdown();
      }
    });
  }

  /**
   * Handle input changes
   */
  handleInput(value) {
    const query = value.trim().toLowerCase();

    if (query.length === 0) {
      this.hideDropdown();
      return;
    }

    // Filter neuron types
    this.filteredTypes = this.neuronTypes.filter((type) =>
      type.toLowerCase().includes(query),
    );

    // Sort by relevance (exact matches first, then starts with, then contains)
    this.filteredTypes.sort((a, b) => {
      const aLower = a.toLowerCase();
      const bLower = b.toLowerCase();

      // Exact match comes first
      if (aLower === query) return -1;
      if (bLower === query) return 1;

      // Starts with query comes next
      if (aLower.startsWith(query) && !bLower.startsWith(query)) return -1;
      if (bLower.startsWith(query) && !aLower.startsWith(query)) return 1;

      // Otherwise alphabetical order
      return a.localeCompare(b);
    });

    // Limit results to prevent performance issues
    this.filteredTypes = this.filteredTypes.slice(0, 10);

    this.currentIndex = -1;
    this.updateDropdown();
    this.showDropdown();
  }

  /**
   * Handle keyboard navigation
   */
  handleKeyDown(e) {
    if (!this.isDropdownVisible) return;

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        this.currentIndex = Math.min(
          this.currentIndex + 1,
          this.filteredTypes.length - 1,
        );
        this.updateHighlight();
        break;

      case "ArrowUp":
        e.preventDefault();
        this.currentIndex = Math.max(this.currentIndex - 1, -1);
        this.updateHighlight();
        break;

      case "Enter":
        e.preventDefault();
        if (this.currentIndex >= 0) {
          this.selectNeuronType(this.filteredTypes[this.currentIndex]);
        } else if (this.filteredTypes.length > 0) {
          this.selectNeuronType(this.filteredTypes[0]);
        }
        break;

      case "Escape":
        this.hideDropdown();
        this.inputElement.blur();
        break;
    }
  }

  /**
   * Update the dropdown content
   */
  updateDropdown() {
    this.dropdown.innerHTML = "";

    if (this.filteredTypes.length === 0) {
      const noResults = document.createElement("div");
      noResults.className = "neuron-search-no-results";
      noResults.textContent = "No matching neuron types found";
      noResults.style.cssText = `
                padding: 8px 12px;
                color: #666;
                font-style: italic;
            `;
      this.dropdown.appendChild(noResults);
      return;
    }

    this.filteredTypes.forEach((type, index) => {
      const item = document.createElement("div");
      item.className = "neuron-search-item";
      item.textContent = type;
      item.style.cssText = `
                padding: 8px 12px;
                cursor: pointer;
                border-bottom: 1px solid #eee;
                transition: background-color 0.2s;
            `;

      // Highlight matching text
      const query = this.inputElement.value.trim().toLowerCase();
      if (query) {
        const regex = new RegExp(`(${query})`, "gi");
        item.innerHTML = type.replace(regex, "<strong>$1</strong>");
      }

      // Click handler
      item.addEventListener("click", () => {
        this.selectNeuronType(type);
      });

      // Hover handler
      item.addEventListener("mouseenter", () => {
        this.currentIndex = index;
        this.updateHighlight();
      });

      this.dropdown.appendChild(item);
    });
  }

  /**
   * Update visual highlighting of selected item
   */
  updateHighlight() {
    const items = this.dropdown.querySelectorAll(".neuron-search-item");
    items.forEach((item, index) => {
      if (index === this.currentIndex) {
        item.style.backgroundColor = "#f0f8ff";
        item.style.color = "#0066cc";
      } else {
        item.style.backgroundColor = "";
        item.style.color = "";
      }
    });
  }

  /**
   * Select a neuron type and navigate to its page
   */
  selectNeuronType(neuronType) {
    this.inputElement.value = neuronType;
    this.hideDropdown();

    // Navigate to the neuron type page
    this.navigateToNeuronType(neuronType);
  }

  /**
   * Navigate to the selected neuron type page
   */
  async navigateToNeuronType(neuronType) {
    // Check which file naming convention exists for this neuron type
    const possibleFilenames = [
      `${neuronType}.html`,
      `${neuronType.toLowerCase()}.html`,
      `${neuronType}_both.html`,
      `${neuronType.toLowerCase()}_both.html`,
      `${neuronType}_all.html`,
      `${neuronType.toLowerCase()}_all.html`,
    ];

    // Try to find which file exists
    let targetFile = possibleFilenames[0]; // default fallback

    for (const filename of possibleFilenames) {
      try {
        const response = await fetch(filename, { method: "HEAD" });
        if (response.ok) {
          targetFile = filename;
          break;
        }
      } catch (e) {
        // Continue trying other filenames
        continue;
      }
    }

    // Navigate to the found or fallback filename
    window.location.href = targetFile;
  }

  /**
   * Show the dropdown
   */
  showDropdown() {
    if (
      this.filteredTypes.length > 0 ||
      this.dropdown.querySelector(".neuron-search-no-results")
    ) {
      this.dropdown.style.display = "block";
      this.isDropdownVisible = true;
    }
  }

  /**
   * Hide the dropdown
   */
  hideDropdown() {
    this.dropdown.style.display = "none";
    this.isDropdownVisible = false;
    this.currentIndex = -1;
  }

  /**
   * Public method to refresh the neuron types list
   */
  async refresh() {
    await this.loadNeuronTypes();
  }
}

// Initialize the search functionality when the DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  // Initialize neuron search
  window.neuronSearch = new NeuronSearch("menulines");
});

// Export for module use if needed
if (typeof module !== "undefined" && module.exports) {
  module.exports = NeuronSearch;
}
