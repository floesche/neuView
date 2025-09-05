"""
Soma Detection Service for QuickPage.

This service handles auto-detection of soma sides and multi-page generation
using the modern PageGenerationRequest workflow.
"""

import logging
from ..result import Result, Ok, Err
from ..commands import GeneratePageCommand
from ..models.page_generation import PageGenerationRequest

logger = logging.getLogger(__name__)


class SomaDetectionService:
    """Service for handling soma side auto-detection and multi-page generation."""

    def __init__(
        self,
        neuprint_connector,
        page_generator,
        cache_service,
        neuron_statistics_service,
    ):
        """Initialize soma detection service.

        Args:
            neuprint_connector: NeuPrint connector instance
            page_generator: Page generator instance
            cache_service: Cache service for saving data
            neuron_statistics_service: Required modern statistics service
        """
        self.connector = neuprint_connector
        self.generator = page_generator
        self.cache_service = cache_service
        if not neuron_statistics_service:
            raise ValueError("Neuron statistics service is required")
        self.neuron_statistics_service = neuron_statistics_service

    async def generate_pages_with_auto_detection(
        self, command: GeneratePageCommand
    ) -> Result[str, str]:
        """Generate multiple pages based on available soma sides using modern workflow."""
        try:
            neuron_type_name = command.neuron_type.value

            # First check if data exists using modern statistics service
            has_data_result = await self.neuron_statistics_service.has_data(
                neuron_type_name
            )
            if has_data_result.is_err():
                return Err(has_data_result.unwrap_err())

            if not has_data_result.unwrap():
                return Err(f"No neurons found for type {command.neuron_type}")

            # Get soma side distribution
            soma_dist_result = (
                await self.neuron_statistics_service.get_soma_side_distribution(
                    neuron_type_name
                )
            )
            if soma_dist_result.is_err():
                return Err(soma_dist_result.unwrap_err())

            soma_counts = soma_dist_result.unwrap()
            left_count = soma_counts.get("left", 0)
            right_count = soma_counts.get("right", 0)
            middle_count = soma_counts.get("middle", 0)
            total_count = soma_counts.get("total", 0)

            # Count how many sides have data
            sides_with_data = sum(
                1 for count in [left_count, right_count, middle_count] if count > 0
            )

            # Calculate unknown soma side count
            unknown_count = total_count - left_count - right_count - middle_count

            generated_files = []

            try:
                # Generate general/combined page if:
                # 1. Multiple sides have data, OR
                # 2. No soma side data exists but neurons are present, OR
                # 3. Unknown soma sides exist alongside any assigned side
                should_generate_combined = (
                    sides_with_data > 1
                    or (sides_with_data == 0 and total_count > 0)
                    or (unknown_count > 0 and sides_with_data > 0)
                )

                if should_generate_combined:
                    combined_result = await self._generate_page_for_soma_side(
                        command, neuron_type_name, "combined", None
                    )
                    if combined_result.is_ok():
                        generated_files.append(combined_result.unwrap())
                        logger.info(
                            f"Generated general page: {combined_result.unwrap()}"
                        )
                    else:
                        logger.warning(
                            f"Failed to generate combined page: {combined_result.unwrap_err()}"
                        )

                # Generate side-specific pages
                for side, count in [
                    ("left", left_count),
                    ("right", right_count),
                    ("middle", middle_count),
                ]:
                    if count > 0:
                        side_result = await self._generate_page_for_soma_side(
                            command, neuron_type_name, side, None
                        )
                        if side_result.is_ok():
                            generated_files.append(side_result.unwrap())
                            logger.info(
                                f"Generated {side.upper()} page: {side_result.unwrap()}"
                            )
                        else:
                            logger.warning(
                                f"Failed to generate {side} page: {side_result.unwrap_err()}"
                            )

                # Save to persistent cache for index generation (using combined data)
                try:
                    combined_data = self.connector.get_neuron_data(
                        neuron_type_name, "combined"
                    )
                    await self._save_to_cache_modern(
                        neuron_type_name, combined_data, command
                    )
                except Exception as e:
                    logger.warning(f"Failed to save to cache: {e}")

                # Log cache performance before clearing
                self.connector.log_cache_performance()

                # Clear cache after successful generation to free memory
                self.connector.clear_neuron_data_cache(neuron_type_name)

                if not generated_files:
                    return Err(f"No pages could be generated for {neuron_type_name}")

                # Return summary of all generated files
                files_summary = ", ".join(generated_files)
                return Ok(files_summary)

            except Exception as e:
                # Clear cache on error to avoid stale data
                self.connector.clear_neuron_data_cache(neuron_type_name)
                raise e

        except Exception as e:
            return Err(f"Failed to generate pages with auto-detection: {str(e)}")

    async def _generate_page_for_soma_side(
        self,
        command: GeneratePageCommand,
        neuron_type_name: str,
        soma_side: str,
        neuron_data: dict,
    ) -> Result[str, str]:
        """Generate a single page for a specific soma side using modern workflow."""
        try:
            # Get neuron data for the specific soma side
            try:
                soma_side_data = self.connector.get_neuron_data(
                    neuron_type_name, soma_side
                )
            except Exception as e:
                return Err(
                    f"Failed to fetch neuron data for {neuron_type_name} ({soma_side}): {str(e)}"
                )

            # Check if we have data
            try:
                neurons_df = soma_side_data.get("neurons")
                if not soma_side_data or neurons_df is None or len(neurons_df) == 0:
                    return Err(f"No neurons found for {neuron_type_name} ({soma_side})")
            except Exception as e:
                logger.warning(
                    f"Error checking neuron data for {neuron_type_name} ({soma_side}): {e}"
                )
                return Err(
                    f"Data validation error for {neuron_type_name} ({soma_side}): {str(e)}"
                )

            # Create modern PageGenerationRequest
            request = PageGenerationRequest(
                neuron_type=neuron_type_name,
                soma_side=soma_side,
                neuron_data=soma_side_data,
                connector=self.connector,
                image_format=command.image_format,
                embed_images=command.embed_images,
                minify=command.minify,
                run_roi_analysis=True,
                run_layer_analysis=True,
                run_column_analysis=True,
            )

            # Validate request
            if not request.validate():
                return Err(
                    f"Invalid page generation request for {neuron_type_name} ({soma_side})"
                )

            # Generate the page using the modern unified workflow
            response = self.generator.generate_page_unified(request)

            if not response.success:
                return Err(
                    f"Page generation failed for {soma_side}: {response.error_message}"
                )

            return Ok(response.output_path)

        except Exception as e:
            return Err(f"Failed to generate {soma_side} page: {str(e)}")

    async def _save_to_cache_modern(
        self, neuron_type_name: str, neuron_data: dict, command: GeneratePageCommand
    ):
        """Save neuron data to cache using modern dictionary format."""
        try:
            if self.cache_service:
                await self.cache_service.save_neuron_data_to_cache(
                    neuron_type_name, neuron_data, command, self.connector
                )
        except Exception as e:
            logger.warning(f"Failed to save to cache for {neuron_type_name}: {e}")
            # Don't fail the whole operation for cache issues

    async def analyze_soma_sides(self, neuron_type_name):
        """Analyze available soma sides for a neuron type.

        Args:
            neuron_type_name: The neuron type name

        Returns:
            dict: Analysis of soma side counts and recommendations
        """
        # Use modern statistics service
        soma_dist_result = (
            await self.neuron_statistics_service.get_soma_side_distribution(
                neuron_type_name
            )
        )
        if soma_dist_result.is_err():
            logger.warning(
                f"Cannot analyze soma sides for {neuron_type_name}: {soma_dist_result.unwrap_err()}"
            )
            return {}

        soma_counts = soma_dist_result.unwrap()
        left_count = soma_counts.get("left", 0)
        right_count = soma_counts.get("right", 0)
        middle_count = soma_counts.get("middle", 0)
        total_count = soma_counts.get("total", 0)

        # Count how many sides have data
        sides_with_data = sum(
            1 for count in [left_count, right_count, middle_count] if count > 0
        )

        # Calculate unknown soma side count
        unknown_count = total_count - left_count - right_count - middle_count

        should_generate_combined = (
            sides_with_data > 1
            or (sides_with_data == 0 and total_count > 0)
            or (unknown_count > 0 and sides_with_data > 0)
        )

        return {
            "total_count": total_count,
            "left_count": left_count,
            "right_count": right_count,
            "middle_count": middle_count,
            "unknown_count": unknown_count,
            "sides_with_data": sides_with_data,
            "should_generate_combined": should_generate_combined,
        }
