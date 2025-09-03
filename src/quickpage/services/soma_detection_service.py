"""
Soma Detection Service for QuickPage.

This service handles auto-detection of soma sides and multi-page generation
that was previously part of the PageGenerationService.
"""

import logging
from ..result import Result, Ok, Err
from ..commands import GeneratePageCommand
from ..models import SomaSide

logger = logging.getLogger(__name__)


class SomaDetectionService:
    """Service for handling soma side auto-detection and multi-page generation."""

    def __init__(self, neuprint_connector, page_generator, cache_service, neuron_statistics_service):
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

    async def generate_pages_with_auto_detection(self, command: GeneratePageCommand) -> Result[str, str]:
        """Generate multiple pages based on available soma sides with shared data optimization."""
        try:
            # Import legacy classes at method level to avoid scoping issues
            from ..neuron_type import NeuronType
            from ..config import NeuronTypeConfig

            neuron_type_name = command.neuron_type.value
            neuron_type_obj = None  # Initialize for legacy fallback
            left_count = 0
            right_count = 0
            middle_count = 0
            total_count = 0

            if self.neuron_statistics_service:
                # Use modern statistics service
                # First check if data exists
                has_data_result = await self.neuron_statistics_service.has_data(neuron_type_name)
                if has_data_result.is_err():
                    return Err(has_data_result.unwrap_err())

                if not has_data_result.unwrap():
                    return Err(f"No neurons found for type {command.neuron_type}")

                # Get soma side distribution
                soma_dist_result = await self.neuron_statistics_service.get_soma_side_distribution(neuron_type_name)
                if soma_dist_result.is_err():
                    return Err(soma_dist_result.unwrap_err())

                soma_counts = soma_dist_result.unwrap()
                left_count = soma_counts.get('left', 0)
                right_count = soma_counts.get('right', 0)
                middle_count = soma_counts.get('middle', 0)
                total_count = soma_counts.get('total', 0)
            else:
                # Neuron statistics service is required for soma detection
                return Err("Neuron statistics service not available. Cannot perform soma side auto-detection.")

            generated_files = []
            combined_neuron_type = None  # Initialize for cache saving

            # Count how many sides have data
            sides_with_data = 0
            if left_count > 0:
                sides_with_data += 1
            if right_count > 0:
                sides_with_data += 1
            if middle_count > 0:
                sides_with_data += 1

            # Calculate unknown soma side count
            unknown_count = total_count - left_count - right_count - middle_count

            try:
                # Generate general page if:
                # 1. Multiple sides have data, OR
                # 2. No soma side data exists but neurons are present, OR
                # 3. Unknown soma sides exist alongside any assigned side
                if (sides_with_data > 1 or
                    (sides_with_data == 0 and total_count > 0) or
                    (unknown_count > 0 and sides_with_data > 0)):
                    # Generate general page using legacy method for now
                    neuron_type_config = NeuronTypeConfig(
                        name=command.neuron_type.value,
                        description=f"Neuron type: {command.neuron_type.value}",
                        query_type="type",
                        soma_side="combined"
                    )
                    combined_neuron_type = NeuronType(
                        command.neuron_type.value,
                        neuron_type_config,
                        self.connector,
                        soma_side='combined'
                    )
                    general_output = self.generator.generate_page_from_neuron_type(
                        combined_neuron_type,
                        self.connector,
                        image_format=command.image_format,
                        embed_images=command.embed_images,
                        uncompress=command.uncompress,
                        hex_size=command.hex_size,
                        spacing_factor=command.spacing_factor
                    )
                    generated_files.append(general_output)
                    logger.info(f"Generated general page: {general_output}")

                # Generate left-specific page if there are left-side neurons
                if left_count > 0:
                    left_config = NeuronTypeConfig(
                        name=command.neuron_type.value,
                        description=f"Neuron type: {command.neuron_type.value}",
                        query_type="type",
                        soma_side="left"
                    )
                    left_neuron_type = NeuronType(
                        command.neuron_type.value,
                        left_config,
                        self.connector,
                        soma_side='left'
                    )
                    left_output = self.generator.generate_page_from_neuron_type(
                        left_neuron_type,
                        self.connector,
                        image_format=command.image_format,
                        embed_images=command.embed_images,
                        uncompress=command.uncompress,
                        hex_size=command.hex_size,
                        spacing_factor=command.spacing_factor
                    )
                    generated_files.append(left_output)
                    logger.info(f"Generated LEFT page: {left_output}")

                # Generate right-specific page if there are right-side neurons
                if right_count > 0:
                    right_config = NeuronTypeConfig(
                        name=command.neuron_type.value,
                        description=f"Neuron type: {command.neuron_type.value}",
                        query_type="type",
                        soma_side="right"
                    )
                    right_neuron_type = NeuronType(
                        command.neuron_type.value,
                        right_config,
                        self.connector,
                        soma_side='right'
                    )
                    right_output = self.generator.generate_page_from_neuron_type(
                        right_neuron_type,
                        self.connector,
                        image_format=command.image_format,
                        embed_images=command.embed_images,
                        uncompress=command.uncompress,
                        hex_size=command.hex_size,
                        spacing_factor=command.spacing_factor
                    )
                    generated_files.append(right_output)
                    logger.info(f"Generated RIGHT page: {right_output}")

                # Generate middle-specific page if there are middle-side neurons
                if middle_count > 0:
                    middle_config = NeuronTypeConfig(
                        name=command.neuron_type.value,
                        description=f"Neuron type: {command.neuron_type.value}",
                        query_type="type",
                        soma_side="middle"
                    )
                    middle_neuron_type = NeuronType(
                        command.neuron_type.value,
                        middle_config,
                        self.connector,
                        soma_side='middle'
                    )
                    middle_output = self.generator.generate_page_from_neuron_type(
                        middle_neuron_type,
                        self.connector,
                        image_format=command.image_format,
                        embed_images=command.embed_images,
                        uncompress=command.uncompress,
                        hex_size=command.hex_size,
                        spacing_factor=command.spacing_factor
                    )
                    generated_files.append(middle_output)
                    logger.info(f"Generated MIDDLE page: {middle_output}")

                # Save to persistent cache for index generation
                # Create combined neuron type for cache if not already created
                if not combined_neuron_type:
                    neuron_type_config = NeuronTypeConfig(
                        name=command.neuron_type.value,
                        description=f"Neuron type: {command.neuron_type.value}",
                        query_type="type",
                        soma_side="combined"
                    )
                    combined_neuron_type = NeuronType(
                        command.neuron_type.value,
                        neuron_type_config,
                        self.connector,
                        soma_side='combined'
                    )

                await self.cache_service.save_neuron_type_to_cache(neuron_type_name, combined_neuron_type, command, self.connector)

                # Log cache performance before clearing
                self.connector.log_cache_performance()

                # Clear cache after successful generation to free memory
                self.connector.clear_neuron_data_cache(neuron_type_name)

                # Return summary of all generated files
                files_summary = ", ".join(generated_files)
                return Ok(files_summary)

            except Exception as e:
                # Clear cache on error to avoid stale data
                self.connector.clear_neuron_data_cache(neuron_type_name)
                raise e

        except Exception as e:
            return Err(f"Failed to generate pages with auto-detection: {str(e)}")

    async def analyze_soma_sides(self, neuron_type_name):
        """Analyze available soma sides for a neuron type.

        Args:
            neuron_type_name: The neuron type name

        Returns:
            dict: Analysis of soma side counts and recommendations
        """
        left_count = 0
        right_count = 0
        middle_count = 0
        total_count = 0

        # Use modern statistics service
        soma_dist_result = await self.neuron_statistics_service.get_soma_side_distribution(neuron_type_name)
        if soma_dist_result.is_ok():
            soma_counts = soma_dist_result.unwrap()
            left_count = soma_counts.get('left', 0)
            right_count = soma_counts.get('right', 0)
            middle_count = soma_counts.get('middle', 0)
            total_count = soma_counts.get('total', 0)
        else:
            logger.warning(f"Cannot analyze soma sides for {neuron_type_name}: failed to get distribution")
            return {}

        # Count how many sides have data
        sides_with_data = 0
        if left_count > 0:
            sides_with_data += 1
        if right_count > 0:
            sides_with_data += 1
        if middle_count > 0:
            sides_with_data += 1

        # Calculate unknown soma side count
        unknown_count = total_count - left_count - right_count - middle_count

        return {
            'total_count': total_count,
            'left_count': left_count,
            'right_count': right_count,
            'middle_count': middle_count,
            'unknown_count': unknown_count,
            'sides_with_data': sides_with_data,
            'should_generate_combined': (
                sides_with_data > 1 or
                (sides_with_data == 0 and total_count > 0) or
                (unknown_count > 0 and sides_with_data > 0)
            )
        }
