"""
Soma Detection Service for QuickPage.

This service handles auto-detection of soma sides and multi-page generation
that was previously part of the PageGenerationService.
"""

import logging
from ..result import Result, Ok, Err
from ..commands import GeneratePageCommand

logger = logging.getLogger(__name__)


class SomaDetectionService:
    """Service for handling soma side auto-detection and multi-page generation."""

    def __init__(self, neuprint_connector, page_generator, cache_service, neuron_statistics_service=None):
        """Initialize soma detection service.

        Args:
            neuprint_connector: NeuPrint connector instance
            page_generator: Page generator instance
            cache_service: Cache service for saving data
            neuron_statistics_service: Optional modern statistics service
        """
        self.connector = neuprint_connector
        self.generator = page_generator
        self.cache_service = cache_service
        self.neuron_statistics_service = neuron_statistics_service

    async def generate_pages_with_auto_detection(self, command: GeneratePageCommand) -> Result[str, str]:
        """Generate multiple pages based on available soma sides with shared data optimization."""
        try:
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
                # Fallback to legacy method
                from ..neuron_type import NeuronType
                from ..config import NeuronTypeConfig

                # Pre-fetch raw neuron data to be shared across all soma sides
                try:
                    # This will cache the raw data in the connector
                    self.connector._get_or_fetch_raw_neuron_data(neuron_type_name)
                except Exception as e:
                    return Err(f"Failed to fetch neuron data for {neuron_type_name}: {str(e)}")

                # Create a NeuronTypeConfig for this neuron type
                neuron_type_config = NeuronTypeConfig(
                    name=neuron_type_name,
                    description=f"Neuron type: {neuron_type_name}",
                    query_type="type",
                    soma_side="combined"
                )

                # First, check what data is available with 'combined'
                neuron_type_obj = NeuronType(
                    neuron_type_name,
                    neuron_type_config,
                    self.connector,
                    soma_side='combined'
                )

                if not neuron_type_obj.has_data():
                    # Clear cache on failure to avoid stale data
                    self.connector.clear_neuron_data_cache(neuron_type_name)
                    return Err(f"No neurons found for type {command.neuron_type}")

                # Check available soma sides
                left_count = neuron_type_obj.get_neuron_count('left')
                right_count = neuron_type_obj.get_neuron_count('right')
                middle_count = neuron_type_obj.get_neuron_count('middle')
                total_count = neuron_type_obj.get_neuron_count()

            generated_files = []

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
                    general_output = self.generator.generate_page_from_neuron_type(
                        neuron_type_obj,
                        self.connector,
                        image_format=command.image_format,
                        embed_images=command.embed_images,
                        uncompress=command.uncompress,
                        hex_size=command.hex_size,
                        spacing_factor=command.spacing_factor
                    )
                    generated_files.append(general_output)

                # Generate left-specific page if there are left-side neurons
                if left_count > 0:
                    left_config = NeuronTypeConfig(
                        name=neuron_type_name,
                        description=f"Neuron type: {neuron_type_name}",
                        query_type="type",
                        soma_side="left"
                    )
                    left_neuron_type = NeuronType(
                        neuron_type_name,
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

                # Generate right-specific page if there are right-side neurons
                if right_count > 0:
                    right_config = NeuronTypeConfig(
                        name=neuron_type_name,
                        description=f"Neuron type: {neuron_type_name}",
                        query_type="type",
                        soma_side="right"
                    )
                    right_neuron_type = NeuronType(
                        neuron_type_name,
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

                # Generate middle-specific page if there are middle-side neurons
                if middle_count > 0:
                    middle_config = NeuronTypeConfig(
                        name=neuron_type_name,
                        description=f"Neuron type: {neuron_type_name}",
                        query_type="type",
                        soma_side="middle"
                    )
                    middle_neuron_type = NeuronType(
                        neuron_type_name,
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

                # Save to persistent cache for index generation (use 'combined' data for comprehensive info)
                if neuron_type_obj:
                    await self.cache_service.save_neuron_type_to_cache(neuron_type_name, neuron_type_obj, command, self.connector)

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

    async def analyze_soma_sides(self, neuron_type_name, neuron_type_obj=None):
        """Analyze available soma sides for a neuron type.

        Args:
            neuron_type_name: The neuron type name
            neuron_type_obj: Optional legacy neuron type object (for backward compatibility)

        Returns:
            dict: Analysis of soma side counts and recommendations
        """
        left_count = 0
        right_count = 0
        middle_count = 0
        total_count = 0

        if self.neuron_statistics_service:
            # Use modern statistics service
            soma_dist_result = await self.neuron_statistics_service.get_soma_side_distribution(neuron_type_name)
            if soma_dist_result.is_ok():
                soma_counts = soma_dist_result.unwrap()
                left_count = soma_counts.get('left', 0)
                right_count = soma_counts.get('right', 0)
                middle_count = soma_counts.get('middle', 0)
                total_count = soma_counts.get('total', 0)
        elif neuron_type_obj:
            # Fallback to legacy method
            left_count = neuron_type_obj.get_neuron_count('left')
            right_count = neuron_type_obj.get_neuron_count('right')
            middle_count = neuron_type_obj.get_neuron_count('middle')
            total_count = neuron_type_obj.get_neuron_count()

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
