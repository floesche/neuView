"""
Index Generator Service

Generates various index and helper pages including JavaScript search files,
README documentation, help pages, and landing pages.
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class IndexGeneratorService:
    """Service for generating various index and helper pages."""

    def __init__(self, page_generator):
        self.page_generator = page_generator

    async def generate_neuron_search_js(
        self, output_dir: Path, neuron_data: List[Dict[str, Any]], generation_time
    ) -> Optional[str]:
        """Generate the neuron-search.js file with embedded neuron types data."""
        # Prepare neuron types data for JavaScript
        neuron_types_for_js = []

        for neuron in neuron_data:
            # Create an entry with the neuron name and available URLs
            neuron_entry = {
                "name": neuron["name"],
                "urls": {},
                "synonyms": neuron.get("synonyms", ""),
                "flywire_types": neuron.get("flywire_types", ""),
            }

            # Add available URLs for this neuron type
            if neuron.get("combined_url") or neuron.get("both_url"):
                combined_url = neuron.get("combined_url")
                neuron_entry["urls"]["combined"] = combined_url
            if neuron["left_url"]:
                neuron_entry["urls"]["left"] = neuron["left_url"]
            if neuron["right_url"]:
                neuron_entry["urls"]["right"] = neuron["right_url"]
            if neuron["middle_url"]:
                neuron_entry["urls"]["middle"] = neuron["middle_url"]

            # Set primary URL (prefer 'combined' if available, otherwise first available)
            if neuron.get("combined_url") or neuron.get("both_url"):
                neuron_entry["primary_url"] = neuron.get("combined_url") or neuron.get(
                    "both_url"
                )
            elif neuron["left_url"]:
                neuron_entry["primary_url"] = neuron["left_url"]
            elif neuron["right_url"]:
                neuron_entry["primary_url"] = neuron["right_url"]
            elif neuron["middle_url"]:
                neuron_entry["primary_url"] = neuron["middle_url"]
            else:
                neuron_entry["primary_url"] = f"{neuron['name']}.html"  # fallback

            neuron_types_for_js.append(neuron_entry)

        # Sort neuron types alphabetically
        neuron_types_for_js.sort(key=lambda x: x["name"])

        # Extract just the names for the simple search functionality
        neuron_names = [neuron["name"] for neuron in neuron_types_for_js]

        # Prepare template data
        js_template_data = {
            "neuron_types_json": json.dumps(neuron_names, indent=2),
            "neuron_types_data_json": json.dumps(neuron_types_for_js, indent=2),
            "generation_timestamp": generation_time.strftime("%Y-%m-%d %H:%M:%S")
            if generation_time
            else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "neuron_types": neuron_types_for_js,
        }

        # Load and render the neuron-search.js template
        js_template = self.page_generator.env.get_template(
            "static/js/neuron-search.js.template.jinja"
        )
        js_content = js_template.render(js_template_data)

        # Ensure static/js directory exists
        js_dir = output_dir / "static" / "js"
        js_dir.mkdir(parents=True, exist_ok=True)

        # Write the neuron-search.js file
        js_path = js_dir / "neuron-search.js"
        js_path.write_text(js_content, encoding="utf-8")
        return str(js_path)

    async def generate_readme(
        self, output_dir: Path, template_data: Dict[str, Any]
    ) -> Optional[str]:
        """Generate README.md documentation for the generated website."""
        try:
            # Load the README template
            readme_template = self.page_generator.env.get_template(
                "README_template.md.jinja"
            )
            readme_content = readme_template.render(template_data)

            # Write the README.md file
            readme_path = output_dir / "README.md"
            readme_path.write_text(readme_content, encoding="utf-8")

            logger.info(f"Generated README.md documentation at {readme_path}")
            return str(readme_path)

        except Exception as e:
            logger.warning(f"Failed to generate README.md: {e}")
            return None

    async def generate_help_page(
        self, output_dir: Path, template_data: Dict[str, Any], uncompress: bool = False
    ) -> Optional[str]:
        """Generate the help.html page."""
        try:
            # Load the help template
            help_template = self.page_generator.env.get_template("help.html.jinja")
            help_content = help_template.render(template_data)

            # Minify HTML content to reduce whitespace if not in uncompress mode
            if not uncompress:
                help_content = self.page_generator.html_utils.minify_html(
                    help_content, minify_js=False
                )

            # Write the help.html file
            help_path = output_dir / "help.html"
            help_path.write_text(help_content, encoding="utf-8")

            logger.info(f"Generated help.html page at {help_path}")
            return str(help_path)

        except Exception as e:
            logger.warning(f"Failed to generate help.html: {e}")
            return None

    async def generate_index_page(
        self, output_dir: Path, template_data: Dict[str, Any], uncompress: bool = False
    ) -> Optional[str]:
        """Generate the index.html landing page."""
        try:
            # Load the index template
            index_template = self.page_generator.env.get_template("index.html.jinja")
            index_content = index_template.render(template_data)

            # Minify HTML content to reduce whitespace if not in uncompress mode
            if not uncompress:
                index_content = self.page_generator.html_utils.minify_html(
                    index_content, minify_js=False
                )

            # Write the index.html file
            index_path = output_dir / "index.html"
            index_path.write_text(index_content, encoding="utf-8")

            logger.info(f"Generated index.html landing page at {index_path}")
            return str(index_path)

        except Exception as e:
            logger.warning(f"Failed to generate index.html: {e}")
            return None

    def calculate_totals(
        self, index_data: List[Dict[str, Any]], cached_data_lazy=None
    ) -> Dict[str, int]:
        """Calculate total neurons and synapses across all types."""
        total_neurons = sum(entry.get("total_count", 0) for entry in index_data)
        total_synapses = 0

        # Calculate total synapses from cached synapse stats
        if cached_data_lazy:
            for entry in index_data:
                entry_name = entry.get("name")
                if entry_name and entry_name in cached_data_lazy:
                    cache_entry = cached_data_lazy[entry_name]
                    if (
                        cache_entry
                        and hasattr(cache_entry, "synapse_stats")
                        and cache_entry.synapse_stats
                    ):
                        # Try to get avg_total, fallback to calculating it from avg_pre + avg_post
                        avg_total = cache_entry.synapse_stats.get("avg_total", 0)
                        if avg_total == 0:
                            avg_pre = cache_entry.synapse_stats.get("avg_pre", 0)
                            avg_post = cache_entry.synapse_stats.get("avg_post", 0)
                            avg_total = avg_pre + avg_post

                        neuron_count = entry.get("total_count", 0)
                        if avg_total > 0 and neuron_count > 0:
                            total_synapses += int(avg_total * neuron_count)

        return {"total_neurons": total_neurons, "total_synapses": total_synapses}

    def get_database_metadata(self, connector) -> Dict[str, str]:
        """Get database metadata including lastDatabaseEdit."""
        metadata = {}
        try:
            db_metadata = connector.get_database_metadata()
            logger.debug(f"Database metadata retrieved: {db_metadata}")
            metadata = {
                "version": db_metadata.get("uuid", "Unknown"),
                "uuid": db_metadata.get("uuid", "Unknown"),
                "lastDatabaseEdit": db_metadata.get("lastDatabaseEdit", "Unknown"),
            }
            logger.debug(f"Final metadata for template: {metadata}")
        except Exception as e:
            logger.warning(f"Failed to get database metadata: {e}")
            metadata = {
                "version": "Unknown",
                "uuid": "Unknown",
                "lastDatabaseEdit": "Unknown",
            }

        return metadata
