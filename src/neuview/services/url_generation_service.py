"""
URL Generation Service for neuView.

This service handles URL generation logic that was previously part of the
PageGenerator class. It provides methods for generating Neuroglancer and
NeuPrint URLs with proper templating and error handling.
"""

import json
import urllib.parse
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class URLGenerationService:
    """Service for generating URLs for external tools like Neuroglancer and NeuPrint."""

    def __init__(
        self,
        config,
        jinja_env,
        neuron_selection_service=None,
        database_query_service=None,
    ):
        """Initialize URL generation service.

        Args:
            config: Configuration object containing server settings
            jinja_env: Jinja2 environment for template rendering
            neuron_selection_service: Service for neuron selection operations
            database_query_service: Service for database query operations
        """
        self.config = config
        self.env = jinja_env
        self.neuron_selection_service = neuron_selection_service
        self.database_query_service = database_query_service

    def generate_neuroglancer_url(
        self,
        neuron_type: str,
        neuron_data: Dict[str, Any],
        soma_side: Optional[str] = None,
        connector=None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate Neuroglancer URL from template with substituted variables.

        Args:
            neuron_type: The neuron type name
            neuron_data: Data containing neuron information including bodyIDs
            soma_side: Soma side filter ('left', 'right', 'combined', etc.)
            connector: NeuPrint connector instance

        Returns:
            Tuple of (URL-encoded Neuroglancer URL, template variables dict)
        """
        # Initialize variables to ensure they're defined in exception handler
        visible_rois = []
        conn_bids = {"upstream": {}, "downstream": {}}

        try:
            # Load appropriate neuroglancer template based on dataset
            if "fafb" in self.config.neuprint.dataset.lower():
                template_name = "neuroglancer-fafb.js.jinja"
            else:
                template_name = "neuroglancer.js.jinja"

            logger.debug(
                f"Using Neuroglancer template: {template_name} for dataset: {self.config.neuprint.dataset}"
            )
            neuroglancer_template = self.env.get_template(template_name)

            # Get bodyID(s) closest to 95th percentile of synapse count
            neurons_df = neuron_data.get("neurons")
            visible_neurons = []
            if neurons_df is not None and not neurons_df.empty:
                bodyids = (
                    neurons_df["bodyId"].tolist()
                    if "bodyId" in neurons_df.columns
                    else []
                )
                if bodyids and self.neuron_selection_service:
                    selected_bodyids = (
                        self.neuron_selection_service.select_bodyids_by_soma_side(
                            neuron_type, neurons_df, soma_side, 95
                        )
                    )
                    visible_neurons = [str(bodyid) for bodyid in selected_bodyids]

            # Get bodyIds of the top cell from each type that connected with the 'visible_neuron'
            if self.database_query_service:
                conn_bids = self.database_query_service.get_connected_bodyids(
                    [int(bid) for bid in visible_neurons], connector
                )

            # Prepare template variables
            template_vars = {
                "website_title": neuron_type,
                "visible_neurons": visible_neurons,
                "neuron_query": neuron_type,
                "visible_rois": visible_rois,
                "connected_bids": conn_bids,
            }

            # Render the template
            neuroglancer_json = neuroglancer_template.render(**template_vars)

            # Parse as JSON to validate and then convert back to string
            neuroglancer_state = json.loads(neuroglancer_json)
            neuroglancer_json_string = json.dumps(
                neuroglancer_state, separators=(",", ":")
            )

            # URL encode the JSON string
            encoded_state = urllib.parse.quote(neuroglancer_json_string, safe="")

            # Create the full Neuroglancer URL
            neuroglancer_url = f"https://clio-ng.janelia.org/#!{encoded_state}"

            return neuroglancer_url, template_vars

        except Exception as e:
            # Return a fallback URL if template processing fails
            logger.warning(
                f"Failed to generate Neuroglancer URL for {neuron_type}: {e}"
            )
            fallback_vars = {
                "website_title": neuron_type,
                "visible_neurons": [],
                "neuron_query": neuron_type,
                "visible_rois": visible_rois,
                "connected_bids": conn_bids,
            }
            return "https://clio-ng.janelia.org/", fallback_vars

    def generate_neuprint_url(
        self, neuron_type: str, neuron_data: Dict[str, Any]
    ) -> str:
        """
        Generate NeuPrint URL from template with substituted variables.

        Args:
            neuron_type: The neuron type name
            neuron_data: Data containing neuron information

        Returns:
            NeuPrint URL for searching this neuron type
        """
        try:
            # Build NeuPrint URL with query parameters
            neuprint_url = (
                f"https://{self.config.neuprint.server}"
                f"/results?dataset={self.config.neuprint.dataset}"
                f"&qt=findneurons"
                f"&qr[0][code]=fn"
                f"&qr[0][ds]={self.config.neuprint.dataset}"
                f"&qr[0][pm][dataset]={self.config.neuprint.dataset}"
                f"&qr[0][pm][all_segments]=false"
                f"&qr[0][pm][enable_contains]=true"
                f"&qr[0][visProps][rowsPerPage]=50"
                f"&tab=0"
                f"&qr[0][pm][neuron_name]={urllib.parse.quote(neuron_type)}"
            )

            # Add soma side suffix if applicable
            if neuron_data.get("soma_side", None) in ["left", "right"]:
                soma_side = neuron_data.get("soma_side", "")
                neuprint_url += f"_{soma_side[:1].upper()}"

            return neuprint_url

        except Exception as e:
            # Return a fallback URL if URL generation fails
            logger.warning(f"Failed to generate NeuPrint URL for {neuron_type}: {e}")
            return f"https://{self.config.neuprint.server}/?dataset={self.config.neuprint.dataset}"

    def generate_dataset_url(self, dataset_name: str) -> str:
        """
        Generate a basic dataset URL for the given dataset.

        Args:
            dataset_name: Name of the dataset

        Returns:
            URL for accessing the dataset
        """
        try:
            return f"https://{self.config.neuprint.server}/?dataset={dataset_name}"
        except Exception as e:
            logger.warning(f"Failed to generate dataset URL for {dataset_name}: {e}")
            return "https://neuprint.janelia.org/"

    def generate_body_url(
        self, body_id: int, dataset_name: Optional[str] = None
    ) -> str:
        """
        Generate a URL for viewing a specific body/neuron.

        Args:
            body_id: The body ID to view
            dataset_name: Optional dataset name, uses config default if not provided

        Returns:
            URL for viewing the specific body
        """
        try:
            dataset = dataset_name or self.config.neuprint.dataset
            return (
                f"https://{self.config.neuprint.server}"
                f"/view?dataset={dataset}&bodyId={body_id}"
            )
        except Exception as e:
            logger.warning(f"Failed to generate body URL for {body_id}: {e}")
            return f"https://{self.config.neuprint.server}/"

    def generate_roi_url(
        self, roi_name: str, dataset_name: Optional[str] = None
    ) -> str:
        """
        Generate a URL for viewing a specific ROI.

        Args:
            roi_name: The ROI name to view
            dataset_name: Optional dataset name, uses config default if not provided

        Returns:
            URL for viewing the specific ROI
        """
        try:
            dataset = dataset_name or self.config.neuprint.dataset
            encoded_roi = urllib.parse.quote(roi_name)
            return (
                f"https://{self.config.neuprint.server}"
                f"/view?dataset={dataset}&roi={encoded_roi}"
            )
        except Exception as e:
            logger.warning(f"Failed to generate ROI URL for {roi_name}: {e}")
            return f"https://{self.config.neuprint.server}/"

    def generate_query_url(
        self,
        query_type: str,
        parameters: Dict[str, Any],
        dataset_name: Optional[str] = None,
    ) -> str:
        """
        Generate a URL for executing a specific query.

        Args:
            query_type: Type of query (e.g., 'findneurons', 'findconnections')
            parameters: Query parameters
            dataset_name: Optional dataset name, uses config default if not provided

        Returns:
            URL for executing the query
        """
        try:
            dataset = dataset_name or self.config.neuprint.dataset
            base_url = (
                f"https://{self.config.neuprint.server}/results?dataset={dataset}"
            )

            # Build query string from parameters
            query_params = []
            for key, value in parameters.items():
                encoded_value = urllib.parse.quote(str(value))
                query_params.append(f"{key}={encoded_value}")

            if query_params:
                return f"{base_url}&{'&'.join(query_params)}"
            else:
                return base_url

        except Exception as e:
            logger.warning(f"Failed to generate query URL for {query_type}: {e}")
            return f"https://{self.config.neuprint.server}/"

    def validate_url(self, url: str) -> bool:
        """
        Validate if a URL is properly formatted.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid, False otherwise
        """
        try:
            result = urllib.parse.urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def encode_url_parameter(self, value: str) -> str:
        """
        Safely encode a parameter for use in URLs.

        Args:
            value: Value to encode

        Returns:
            URL-encoded value
        """
        try:
            return urllib.parse.quote(str(value), safe="")
        except Exception as e:
            logger.warning(f"Failed to encode URL parameter '{value}': {e}")
            return ""
