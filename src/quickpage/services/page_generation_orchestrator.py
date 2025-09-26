"""
Page Generation Orchestrator Service

This service orchestrates the complete page generation workflow, consolidating
the logic from the two generate_page methods in PageGenerator and providing
a unified interface for page generation.
"""

import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional

from ..models.page_generation import (
    PageGenerationRequest,
    PageGenerationResponse,
    PageGenerationContext,
    AnalysisResults,
    URLCollection,
    AnalysisConfiguration,
)
from ..visualization.constants import DEFAULT_HEX_SIZE, DEFAULT_SPACING_FACTOR

logger = logging.getLogger(__name__)


class PageGenerationOrchestrator:
    """Orchestrates the complete page generation workflow."""

    def __init__(self, page_generator):
        """Initialize the orchestrator with a PageGenerator instance.

        Args:
            page_generator: PageGenerator instance providing services and utilities
        """
        self.page_generator = page_generator

    @property
    def env(self):
        """Get Jinja environment from page generator."""
        return self.page_generator.env

    @property
    def template_context_service(self):
        """Get template context service from page generator."""
        return self.page_generator.template_context_service

    @property
    def neuron_selection_service(self):
        """Get neuron selection service from page generator."""
        return self.page_generator.neuron_selection_service

    @property
    def html_utils(self):
        """Get HTML utils from page generator."""
        return self.page_generator.html_utils

    @property
    def types_dir(self):
        """Get types directory from page generator."""
        return self.page_generator.types_dir

    def generate_page(self, request: PageGenerationRequest) -> PageGenerationResponse:
        """
        Generate an HTML page using the unified workflow.

        Args:
            request: PageGenerationRequest containing all generation parameters

        Returns:
            PageGenerationResponse with the result
        """
        start_time = time.time()

        try:
            # Validate request
            if not request.validate():
                return PageGenerationResponse.error_response(
                    "Invalid page generation request: missing required data"
                )

            # Create analysis configuration
            analysis_config = AnalysisConfiguration.from_request(request)

            # Prepare generation context
            context = self._prepare_generation_context(request, analysis_config)

            # Render the page
            html_content = self._render_page(context)

            # Post-process HTML
            if request.minify:
                html_content = self.html_utils.minify_html(html_content, minify_js=True)

            # Save the page
            output_path = self._save_page(html_content, request)

            # Generate auxiliary files
            self._generate_auxiliary_files()

            # Calculate generation time and file size
            generation_time = (time.time() - start_time) * 1000
            file_size = (
                Path(output_path).stat().st_size if Path(output_path).exists() else None
            )

            return PageGenerationResponse.success_response(
                output_path=str(output_path),
                generation_time_ms=generation_time,
                file_size_bytes=file_size,
            )

        except Exception as e:
            logger.error(f"Error generating page for {request.get_neuron_name()}: {e}")
            return PageGenerationResponse.error_response(
                f"Page generation failed: {str(e)}"
            )

    def _prepare_generation_context(
        self, request: PageGenerationRequest, analysis_config: AnalysisConfiguration
    ) -> PageGenerationContext:
        """
        Prepare the complete context for page generation.

        Args:
            request: Page generation request
            analysis_config: Analysis configuration

        Returns:
            Complete PageGenerationContext
        """
        # Run analyses
        analysis_results = self._run_analyses(request, analysis_config)

        # Generate URLs
        urls = self._generate_urls(request)

        # Get additional context
        type_region = self._get_type_region(request)

        # Get neuroglancer variables
        neuroglancer_vars = self._extract_neuroglancer_vars(urls)

        return PageGenerationContext(
            request=request,
            analysis_results=analysis_results,
            urls=urls,
            neuroglancer_vars=neuroglancer_vars,
            type_region=type_region,
        )

    def _run_analyses(
        self, request: PageGenerationRequest, analysis_config: AnalysisConfiguration
    ) -> AnalysisResults:
        """
        Run all configured analyses for the neuron type.

        Args:
            request: Page generation request
            analysis_config: Analysis configuration

        Returns:
            AnalysisResults containing all analysis data
        """
        results = AnalysisResults()
        neuron_data = request.get_neuron_data()
        neuron_name = request.get_neuron_name()
        soma_side = request.get_soma_side()

        try:
            # ROI analysis (both modes)
            if analysis_config.run_roi_analysis:
                try:
                    results.roi_summary = self.page_generator._aggregate_roi_data(
                        neuron_data.get("roi_counts"),
                        neuron_data.get("neurons"),
                        soma_side,
                        request.connector,
                    )
                except Exception as e:
                    logger.warning(f"ROI analysis failed for {neuron_name}: {e}")
                    results.roi_summary = None

            # Layer analysis (both modes)
            if analysis_config.run_layer_analysis:
                try:
                    results.layer_analysis = (
                        self.page_generator._analyze_layer_roi_data(
                            neuron_data.get("roi_counts"),
                            neuron_data.get("neurons"),
                            soma_side,
                            neuron_name,
                            request.connector,
                        )
                    )
                except Exception as e:
                    logger.warning(f"Layer analysis failed for {neuron_name}: {e}")
                    results.layer_analysis = None

            # Column analysis (both modes)
            if analysis_config.run_column_analysis:
                try:
                    results.column_analysis = (
                        self.page_generator._analyze_column_roi_data(
                            neuron_data.get("roi_counts"),
                            neuron_data.get("neurons"),
                            soma_side,
                            neuron_name,
                            request.connector,
                            file_type=analysis_config.column_analysis_options.get(
                                "file_type", "svg"
                            ),
                            save_to_files=analysis_config.column_analysis_options.get(
                                "save_to_files", True
                            ),
                            hex_size=getattr(request, "hex_size", DEFAULT_HEX_SIZE),
                            spacing_factor=getattr(
                                request, "spacing_factor", DEFAULT_SPACING_FACTOR
                            ),
                        )
                    )
                except Exception as e:
                    logger.warning(f"Column analysis failed for {neuron_name}: {e}")
                    results.column_analysis = None

        except Exception as e:
            logger.warning(f"Error during analysis for {neuron_name}: {e}")
            # Continue with empty results rather than failing completely

        return results

    def _generate_urls(self, request: PageGenerationRequest) -> URLCollection:
        """
        Generate all URLs needed for the page.

        Args:
            request: Page generation request

        Returns:
            URLCollection with all generated URLs
        """
        neuron_name = request.get_neuron_name()
        soma_side = request.get_soma_side()
        neuron_data = request.get_neuron_data()

        urls = URLCollection()

        try:
            # Generate Neuroglancer URL
            try:
                # Always pass connector regardless of mode
                neuroglancer_url, neuroglancer_vars = (
                    self.page_generator._generate_neuroglancer_url(
                        neuron_name, neuron_data, soma_side, request.connector
                    )
                )

                urls.neuroglancer_url = neuroglancer_url
                # Store neuroglancer_vars for later use
                self._neuroglancer_vars = neuroglancer_vars
            except Exception as e:
                logger.warning(f"Failed to generate neuroglancer URL: {e}")
                urls.neuroglancer_url = None
                self._neuroglancer_vars = None

            # Generate NeuPrint URL
            try:
                urls.neuprint_url = self.page_generator._generate_neuprint_url(
                    neuron_name, neuron_data
                )
            except Exception as e:
                logger.warning(f"Failed to generate neuprint URL: {e}")
                urls.neuprint_url = None

            # Get soma side links
            try:
                urls.soma_side_links = (
                    self.neuron_selection_service.get_available_soma_sides(
                        neuron_name, request.connector
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to get soma side links: {e}")
                urls.soma_side_links = {}

        except Exception as e:
            logger.warning(f"Error generating URLs for {neuron_name}: {e}")

        return urls

    def _extract_neuroglancer_vars(
        self, urls: URLCollection
    ) -> Optional[Dict[str, Any]]:
        """Extract neuroglancer variables from URL generation."""
        return getattr(self, "_neuroglancer_vars", None)

    def _get_type_region(self, request: PageGenerationRequest) -> Optional[str]:
        """Get the type's assigned region for setting the NG view."""
        try:
            return self.page_generator._get_region_for_type(
                request.get_neuron_name(), request.connector
            )
        except Exception as e:
            logger.warning(f"Error getting type region: {e}")
            return None

    def _render_page(self, context: PageGenerationContext) -> str:
        """
        Render the HTML page using the template.

        Args:
            context: Complete generation context

        Returns:
            Rendered HTML content
        """
        # Load template
        template = self.env.get_template("neuron_page.html.jinja")

        # Prepare template context using the service
        template_context = self.template_context_service.prepare_neuron_page_context(
            context.request.get_neuron_name(),
            context.request.get_neuron_data(),
            context.request.get_soma_side(),
            connectivity_data=context.request.get_neuron_data().get("connectivity", {}),
            analysis_results=context.analysis_results.to_dict(),
            urls=context.urls.to_dict(),
            additional_context={"type_region": context.type_region},
        )

        # Add neuroglancer variables if available
        if context.neuroglancer_vars:
            template_context = self.template_context_service.add_neuroglancer_variables(
                template_context, context.neuroglancer_vars
            )

        # Render template
        return template.render(**template_context)

    def _save_page(self, html_content: str, request: PageGenerationRequest) -> str:
        """
        Save the HTML page to disk.

        Args:
            html_content: Rendered HTML content
            request: Page generation request

        Returns:
            Path to the saved file
        """
        # Generate output filename
        from .file_service import FileService

        output_filename = FileService.generate_filename(
            request.get_neuron_name(), request.get_soma_side()
        )
        output_path = self.types_dir / output_filename

        # Write HTML file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return str(output_path)

    def _generate_auxiliary_files(self):
        """Generate auxiliary files like neuron-search.js if needed."""
        try:
            self.page_generator._generate_neuron_search_js()
        except Exception as e:
            logger.warning(f"Error generating auxiliary files: {e}")
