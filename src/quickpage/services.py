"""
Simplified services for QuickPage application layer.

This module consolidates the application services into manageable classes
that orchestrate business logic without excessive abstraction.
"""

import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
import logging
import yaml

from .models import (
    NeuronTypeName, SomaSide, NeuronCollection,
    NeuronTypeStatistics, NeuronTypeConnectivity
)
from .result import Result, Ok, Err

logger = logging.getLogger(__name__)


@dataclass
class GeneratePageCommand:
    """Command to generate an HTML page for a neuron type."""
    neuron_type: NeuronTypeName
    soma_side: SomaSide = SomaSide.ALL
    output_directory: Optional[str] = None
    include_3d_view: bool = False
    image_format: str = 'svg'
    embed_images: bool = False
    uncompress: bool = False
    requested_at: Optional[datetime] = None

    def __post_init__(self):
        if self.requested_at is None:
            self.requested_at = datetime.now()

        # Ensure neuron_type is a NeuronTypeName instance
        if not isinstance(self.neuron_type, NeuronTypeName):
            self.neuron_type = NeuronTypeName(str(self.neuron_type))

        # Ensure soma_side is a SomaSide instance
        if not isinstance(self.soma_side, SomaSide):
            self.soma_side = SomaSide.from_string(str(self.soma_side))


@dataclass
class ListNeuronTypesCommand:
    """Command to list available neuron types."""
    max_results: int = 10
    all_results: bool = False
    sorted_results: bool = False
    show_soma_sides: bool = False
    show_statistics: bool = False
    filter_pattern: Optional[str] = None
    exclude_empty: bool = True


@dataclass
class InspectNeuronTypeCommand:
    """Command to inspect detailed neuron type information."""
    neuron_type: NeuronTypeName
    soma_side: SomaSide = SomaSide.BOTH

    def __post_init__(self):
        if not isinstance(self.neuron_type, NeuronTypeName):
            self.neuron_type = NeuronTypeName(str(self.neuron_type))
        if not isinstance(self.soma_side, SomaSide):
            self.soma_side = SomaSide.from_string(str(self.soma_side))


@dataclass
class TestConnectionCommand:
    """Command to test NeuPrint connection."""
    detailed: bool = False
    timeout: int = 30


@dataclass
class FillQueueCommand:
    """Command to create a queue YAML file with generate options."""
    neuron_type: Optional[NeuronTypeName] = None
    soma_side: SomaSide = SomaSide.ALL
    output_directory: Optional[str] = None
    include_3d_view: bool = False
    image_format: str = 'svg'
    embed_images: bool = False
    all_types: bool = False
    max_types: int = 10
    config_file: Optional[str] = None
    requested_at: Optional[datetime] = None

    def __post_init__(self):
        if self.requested_at is None:
            self.requested_at = datetime.now()

        # Ensure neuron_type is a NeuronTypeName instance if provided
        if self.neuron_type is not None and not isinstance(self.neuron_type, NeuronTypeName):
            self.neuron_type = NeuronTypeName(str(self.neuron_type))

        # Ensure soma_side is a SomaSide instance
        if not isinstance(self.soma_side, SomaSide):
            self.soma_side = SomaSide.from_string(str(self.soma_side))


@dataclass
class PopCommand:
    """Command to pop and process a queue file."""
    output_directory: Optional[str] = None
    uncompress: bool = False
    requested_at: Optional[datetime] = None

    def __post_init__(self):
        if self.requested_at is None:
            self.requested_at = datetime.now()


@dataclass
class CreateIndexCommand:
    """Command to create an index page listing all neuron types."""
    output_directory: Optional[str] = None
    index_filename: str = "index.html"
    include_roi_analysis: bool = True  # Always include ROI analysis for comprehensive data
    uncompress: bool = False
    requested_at: Optional[datetime] = None

    def __post_init__(self):
        if self.requested_at is None:
            self.requested_at = datetime.now()


@dataclass
class NeuronTypeInfo:
    """Information about a neuron type."""
    name: str
    count: int = 0
    soma_sides: Optional[Dict[str, int]] = None
    avg_synapses: float = 0.0

    def __post_init__(self):
        if self.soma_sides is None:
            self.soma_sides = {}


@dataclass
class DatasetInfo:
    """Information about the dataset."""
    name: str
    version: str = "Unknown"
    server_url: str = "Unknown"
    connection_status: str = "Unknown"


class PageGenerationService:
    """Service for generating HTML pages."""

    def __init__(self, neuprint_connector, page_generator, config=None):
        self.connector = neuprint_connector
        self.generator = page_generator
        self.config = config

        # Initialize cache manager if config is available
        self.cache_manager = None
        if config and hasattr(config, 'output') and hasattr(config.output, 'directory'):
            from .cache import create_cache_manager
            self.cache_manager = create_cache_manager(config.output.directory)

    async def generate_page(self, command: GeneratePageCommand) -> Result[str, str]:
        """Generate an HTML page for a neuron type with optimized data sharing."""
        try:
            # Import the legacy NeuronType class
            from .neuron_type import NeuronType
            from .config import NeuronTypeConfig

            # Create NeuronType instance
            config = NeuronTypeConfig(
                name=command.neuron_type.value,
                description=f"{command.neuron_type.value} neurons"
            )

            # Handle auto-detection for SomaSide.ALL
            if command.soma_side == SomaSide.ALL:
                return await self._generate_pages_with_auto_detection(command, config)

            # Pre-fetch raw neuron data for single page generation (enables caching for future calls)
            neuron_type_name = command.neuron_type.value
            try:
                self.connector._get_or_fetch_raw_neuron_data(neuron_type_name)
            except Exception as e:
                return Err(f"Failed to fetch neuron data for {neuron_type_name}: {str(e)}")

            # Convert SomaSide enum to legacy format for specific sides
            if command.soma_side == SomaSide.BOTH:
                legacy_soma_side = 'both'
            elif command.soma_side == SomaSide.LEFT:
                legacy_soma_side = 'left'
            elif command.soma_side == SomaSide.RIGHT:
                legacy_soma_side = 'right'
            elif command.soma_side == SomaSide.MIDDLE:
                legacy_soma_side = 'middle'
            else:
                legacy_soma_side = 'both'

            neuron_type_obj = NeuronType(
                neuron_type_name,
                config,
                self.connector,
                soma_side=legacy_soma_side
            )

            # Check if we have data
            if not neuron_type_obj.has_data():
                # Clear cache on failure to avoid stale data
                self.connector.clear_neuron_data_cache(neuron_type_name)
                return Err(f"No neurons found for type {command.neuron_type}")

            try:
                # Generate the page using legacy generator (pass connector for primary ROI fetching)
                output_file = self.generator.generate_page_from_neuron_type(
                    neuron_type_obj,
                    self.connector,
                    image_format=command.image_format,
                    embed_images=command.embed_images,
                    uncompress=command.uncompress
                )

                # Save to persistent cache for index generation
                await self._save_neuron_type_to_cache(neuron_type_name, neuron_type_obj, command)

                # Log cache performance for single pages too
                if command.soma_side != SomaSide.ALL:
                    self.connector.log_cache_performance()
                    self.connector.clear_neuron_data_cache(neuron_type_name)

                return Ok(output_file)
            except Exception as e:
                # Clear cache on error to avoid stale data
                self.connector.clear_neuron_data_cache(neuron_type_name)
                raise e

        except Exception as e:
            return Err(f"Failed to generate page: {str(e)}")

    async def _save_neuron_type_to_cache(self, neuron_type_name: str, neuron_type_obj, command: GeneratePageCommand):
        """Save neuron type data to persistent cache for later index generation."""
        if not self.cache_manager:
            return  # No cache manager available

        try:
            import pandas as pd
            from .cache import NeuronTypeCacheData
            from .models import NeuronCollection, NeuronTypeName, Neuron, BodyId, SynapseCount, SomaSide

            # Save ROI hierarchy during generation to avoid queries during index creation
            await self._save_roi_hierarchy_to_cache()

            # Get full neuron data from the neuron type object
            neuron_data_dict = neuron_type_obj.to_dict()
            neurons_df = neuron_data_dict.get('neurons')
            connectivity_data = neuron_data_dict.get('connectivity', {})
            summary_data = neuron_data_dict.get('summary', {})

            # Convert DataFrame to NeuronCollection for enhanced cache processing
            neuron_collection = NeuronCollection(type_name=NeuronTypeName(neuron_type_name))

            if neurons_df is not None and not neurons_df.empty:
                for _, row in neurons_df.iterrows():
                    # Extract soma side
                    soma_side = None
                    if 'somaSide' in row and pd.notna(row['somaSide']):
                        soma_side_val = row['somaSide']
                        if soma_side_val == 'L':
                            soma_side = SomaSide.LEFT
                        elif soma_side_val == 'R':
                            soma_side = SomaSide.RIGHT
                        elif soma_side_val == 'M':
                            soma_side = SomaSide.MIDDLE

                    # Create Neuron object
                    neuron = Neuron(
                        body_id=BodyId(int(row['bodyId'])),
                        type_name=NeuronTypeName(neuron_type_name),
                        instance=row.get('instance'),
                        status=row.get('status'),
                        soma_side=soma_side,
                        soma_x=row.get('somaLocation', {}).get('x') if isinstance(row.get('somaLocation'), dict) else None,
                        soma_y=row.get('somaLocation', {}).get('y') if isinstance(row.get('somaLocation'), dict) else None,
                        soma_z=row.get('somaLocation', {}).get('z') if isinstance(row.get('somaLocation'), dict) else None,
                        synapse_count=SynapseCount(
                            pre=int(row.get('pre', 0)),
                            post=int(row.get('post', 0))
                        ),
                        cell_class=row.get('cellClass'),
                        cell_subclass=row.get('cellSubclass'),
                        cell_superclass=row.get('cellSuperclass')
                    )
                    neuron_collection.add_neuron(neuron)

            # Extract ROI summary and parent ROI from neuron type data
            roi_summary = []
            parent_roi = ""

            # Get ROI data if available in the neuron data
            roi_counts_df = neuron_data_dict.get('roi_counts')
            if roi_counts_df is not None and not roi_counts_df.empty and self.generator:
                try:
                    # Use the page generator's ROI aggregation method with existing connector
                    roi_summary_full = self.generator._aggregate_roi_data(
                        roi_counts_df, neurons_df, 'both', self.connector
                    )

                    # Filter ROIs by threshold and clean names (same logic as IndexService)
                    threshold = 1.5
                    cleaned_roi_summary = []
                    seen_names = set()

                    for roi in roi_summary_full:
                        if roi['pre_percentage'] >= threshold or roi['post_percentage'] >= threshold:
                            cleaned_name = self._clean_roi_name(roi['name'])
                            if cleaned_name and cleaned_name not in seen_names:
                                cleaned_roi_summary.append({
                                    'name': cleaned_name,
                                    'total': roi['total'],
                                    'pre_percentage': roi['pre_percentage'],
                                    'post_percentage': roi['post_percentage']
                                })
                                seen_names.add(cleaned_name)

                                if len(cleaned_roi_summary) >= 5:
                                    break

                    roi_summary = cleaned_roi_summary

                    # Get parent ROI for the highest ranking (first) ROI
                    if roi_summary:
                        highest_roi = roi_summary[0]['name']
                        parent_roi = self._get_roi_hierarchy_parent(highest_roi, self.connector)

                    logger.debug(f"Extracted ROI data for {neuron_type_name}: {len(roi_summary)} ROIs, parent: {parent_roi}")

                except Exception as e:
                    logger.debug(f"Failed to extract ROI data for {neuron_type_name}: {e}")
                    roi_summary = []
                    parent_roi = ""

            # Create enhanced cache data with connectivity and distribution information
            cache_data = NeuronTypeCacheData.from_neuron_collection(
                neuron_collection=neuron_collection,
                roi_summary=roi_summary,
                parent_roi=parent_roi,
                connectivity_data=connectivity_data,
                neuron_data_df=neurons_df
            )

            # Save to cache
            success = self.cache_manager.save_neuron_type_cache(cache_data)
            if success:
                logger.debug(f"Saved enhanced cache data for neuron type {neuron_type_name}")
            else:
                logger.warning(f"Failed to save cache data for neuron type {neuron_type_name}")

        except Exception as e:
            logger.warning(f"Error saving cache for {neuron_type_name}: {e}")
            import traceback
            logger.debug(f"Cache save error details: {traceback.format_exc()}")

    async def _save_roi_hierarchy_to_cache(self):
        """Save ROI hierarchy to cache during generation to avoid queries during index creation."""
        try:
            # Check if ROI hierarchy is already cached
            if self.cache_manager and self.cache_manager.load_roi_hierarchy():
                logger.debug("ROI hierarchy already cached, skipping fetch")
                return

            logger.debug("Fetching ROI hierarchy from database for caching")
            # Use the existing connector's method to fetch ROI hierarchy
            hierarchy_data = self.connector._get_roi_hierarchy()

            # Save to cache
            if hierarchy_data and self.cache_manager:
                success = self.cache_manager.save_roi_hierarchy(hierarchy_data)
                if success:
                    logger.info("✅ Saved ROI hierarchy to cache during generation - will speed up index creation")
                else:
                    logger.warning("Failed to save ROI hierarchy to cache")

        except Exception as e:
            logger.debug(f"Failed to cache ROI hierarchy during generation: {e}")

    def _clean_roi_name(self, roi_name: str) -> str:
        """Remove (R) and (L) suffixes from ROI names."""
        import re
        # Remove (R), (L), or (M) suffixes from ROI names
        cleaned = re.sub(r'\s*\([RLM]\)$', '', roi_name)
        return cleaned.strip()

    def _get_roi_hierarchy_parent(self, roi_name: str, connector) -> str:
        """Get the parent ROI of the given ROI from the hierarchy."""
        try:
            # Load ROI hierarchy from cache or fetch if needed
            hierarchy_data = None
            if self.cache_manager:
                hierarchy_data = self.cache_manager.load_roi_hierarchy()

            if not hierarchy_data:
                # Fallback to fetching from database using existing connector
                hierarchy_data = connector._get_roi_hierarchy()

            if not hierarchy_data:
                return ""

            # Clean the ROI name first (remove (R), (L), (M) suffixes)
            cleaned_roi = self._clean_roi_name(roi_name)

            # Search recursively for the ROI and its parent
            parent = self._find_roi_parent_recursive(cleaned_roi, hierarchy_data)
            return parent if parent else ""

        except Exception as e:
            logger.debug(f"Failed to get parent ROI for {roi_name}: {e}")
            return ""

    def _find_roi_parent_recursive(self, roi_name: str, hierarchy: dict, parent_name: str = "") -> str:
        """Recursively search for ROI in hierarchy and return its parent."""
        for key, value in hierarchy.items():
            # Direct match
            if key == roi_name:
                return parent_name

            # Handle ROI naming variations:
            # - Remove side suffixes: "AOTU(L)*" -> "AOTU"
            # - Remove asterisks: "AOTU*" -> "AOTU"
            cleaned_key = key.replace('(L)', '').replace('(R)', '').replace('(M)', '').replace('*', '').strip()
            if cleaned_key == roi_name:
                return parent_name

            # Also check if the ROI name matches the beginning of the key
            if key.startswith(roi_name) and (len(key) == len(roi_name) or key[len(roi_name)] in '(*'):
                return parent_name

            # Recursive search
            if isinstance(value, dict):
                result = self._find_roi_parent_recursive(roi_name, value, key)
                if result:
                    return result
        return ""

    async def _generate_pages_with_auto_detection(self, command: GeneratePageCommand, config) -> Result[str, str]:
        """Generate multiple pages based on available soma sides with shared data optimization."""
        try:
            from .neuron_type import NeuronType

            # Pre-fetch raw neuron data to be shared across all soma sides
            neuron_type_name = command.neuron_type.value
            try:
                # This will cache the raw data in the connector
                self.connector._get_or_fetch_raw_neuron_data(neuron_type_name)
            except Exception as e:
                return Err(f"Failed to fetch neuron data for {neuron_type_name}: {str(e)}")

            # First, check what data is available with 'both'
            neuron_type_obj = NeuronType(
                neuron_type_name,
                config,
                self.connector,
                soma_side='both'
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

            try:
                # Generate general page if multiple sides have data OR if no soma side data exists but neurons are present
                if sides_with_data > 1 or (sides_with_data == 0 and total_count > 0):
                    general_output = self.generator.generate_page_from_neuron_type(
                        neuron_type_obj,
                        self.connector,
                        image_format=command.image_format,
                        embed_images=command.embed_images,
                        uncompress=command.uncompress
                    )
                    generated_files.append(general_output)

                # Generate left-specific page if there are left-side neurons
                if left_count > 0:
                    left_neuron_type = NeuronType(
                        neuron_type_name,
                        config,
                        self.connector,
                        soma_side='left'
                    )
                    left_output = self.generator.generate_page_from_neuron_type(
                        left_neuron_type,
                        self.connector,
                        image_format=command.image_format,
                        embed_images=command.embed_images,
                        uncompress=command.uncompress
                    )
                    generated_files.append(left_output)

                # Generate right-specific page if there are right-side neurons
                if right_count > 0:
                    right_neuron_type = NeuronType(
                        neuron_type_name,
                        config,
                        self.connector,
                        soma_side='right'
                    )
                    right_output = self.generator.generate_page_from_neuron_type(
                        right_neuron_type,
                        self.connector,
                        image_format=command.image_format,
                        embed_images=command.embed_images,
                        uncompress=command.uncompress
                    )
                    generated_files.append(right_output)

                # Generate middle-specific page if there are middle-side neurons
                if middle_count > 0:
                    middle_neuron_type = NeuronType(
                        neuron_type_name,
                        config,
                        self.connector,
                        soma_side='middle'
                    )
                    middle_output = self.generator.generate_page_from_neuron_type(
                        middle_neuron_type,
                        self.connector,
                        image_format=command.image_format,
                        embed_images=command.embed_images,
                        uncompress=command.uncompress
                    )
                    generated_files.append(middle_output)

                # Save to persistent cache for index generation (use 'both' data for comprehensive info)
                await self._save_neuron_type_to_cache(neuron_type_name, neuron_type_obj, command)

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


class NeuronDiscoveryService:
    """Service for discovering available neuron types."""

    def __init__(self, neuprint_connector, config):
        self.connector = neuprint_connector
        self.config = config

    async def list_neuron_types(self, command: ListNeuronTypesCommand) -> Result[List[NeuronTypeInfo], str]:
        """List available neuron types."""
        try:
            # Use the discovery configuration from config, but override max_types if --all is specified
            discovery_config = self.config.discovery
            if command.all_results:
                from dataclasses import replace
                discovery_config = replace(discovery_config, max_types=999999)

            discovered_types = self.connector.discover_neuron_types(discovery_config)
            # Convert to NeuronTypeInfo objects
            type_infos = []
            for type_name in discovered_types:
                info = NeuronTypeInfo(name=type_name)

                # If statistics are requested, get them (but don't fail if we can't)
                if command.show_statistics:
                    try:
                        # Try to get basic neuron count using the legacy method
                        from .neuron_type import NeuronType
                        from .config import NeuronTypeConfig

                        config = NeuronTypeConfig(name=type_name, description=f"{type_name} neurons")
                        neuron_type_obj = NeuronType(type_name, config, self.connector, soma_side='both')

                        if neuron_type_obj.has_data():
                            info.count = neuron_type_obj.get_neuron_count()
                            synapse_stats = neuron_type_obj.get_synapse_stats()
                            info.avg_synapses = synapse_stats.get('avg_pre', 0.0) + synapse_stats.get('avg_post', 0.0)
                    except Exception:
                        # If we can't get stats, skip this type when show_statistics is requested
                        continue

                # If soma sides are requested, get them
                if command.show_soma_sides:
                    try:
                        soma_data = self.connector.get_soma_side_distribution(type_name)
                        if soma_data:
                            info.soma_sides = soma_data
                    except Exception:
                        pass  # Skip if we can't get soma data

                type_infos.append(info)

            # Filter by pattern if specified
            if command.filter_pattern:
                import re
                pattern = re.compile(command.filter_pattern, re.IGNORECASE)
                type_infos = [info for info in type_infos if pattern.search(info.name)]

            # Exclude empty types if requested (only if we have count data)
            if command.exclude_empty and command.show_statistics:
                type_infos = [info for info in type_infos if info.count > 0]

            # Sort if requested
            if command.sorted_results:
                type_infos.sort(key=lambda x: x.name)

            # Limit results (unless --all is specified)
            if not command.all_results and command.max_results > 0:
                type_infos = type_infos[:command.max_results]
            return Ok(type_infos)

        except Exception as e:
            return Err(f"Failed to list neuron types: {str(e)}")

    async def inspect_neuron_type(self, command: InspectNeuronTypeCommand) -> Result[NeuronTypeStatistics, str]:
        """Inspect detailed information about a neuron type."""
        try:
            # Import legacy components
            from .neuron_type import NeuronType
            from .config import NeuronTypeConfig

            # Create NeuronType instance
            config = NeuronTypeConfig(
                name=command.neuron_type.value,
                description=f"{command.neuron_type.value} neurons"
            )

            # Convert SomaSide enum to legacy format
            if command.soma_side in [SomaSide.ALL, SomaSide.BOTH]:
                legacy_soma_side = 'both'
            elif command.soma_side == SomaSide.LEFT:
                legacy_soma_side = 'left'
            elif command.soma_side == SomaSide.RIGHT:
                legacy_soma_side = 'right'
            elif command.soma_side == SomaSide.MIDDLE:
                legacy_soma_side = 'middle'
            else:
                legacy_soma_side = 'both'

            neuron_type_obj = NeuronType(
                command.neuron_type.value,
                config,
                self.connector,
                soma_side=legacy_soma_side
            )

            # Check if we have data
            if not neuron_type_obj.has_data():
                return Err(f"No neurons found for type {command.neuron_type}")

            # Gather statistics
            neuron_count = neuron_type_obj.get_neuron_count()
            soma_counts = {
                "left": neuron_type_obj.get_neuron_count('left'),
                "right": neuron_type_obj.get_neuron_count('right'),
                "middle": neuron_type_obj.get_neuron_count('middle')
            }
            synapse_stats = neuron_type_obj.get_synapse_stats()

            # Create statistics object
            stats = NeuronTypeStatistics(
                type_name=command.neuron_type,
                total_count=neuron_count,
                soma_side_counts=soma_counts,
                synapse_stats=synapse_stats
            )

            return Ok(stats)

        except Exception as e:
            return Err(f"Failed to inspect neuron type: {str(e)}")


class ConnectionTestService:
    """Service for testing NeuPrint connection."""

    def __init__(self, neuprint_connector):
        self.connector = neuprint_connector

    async def test_connection(self, command: TestConnectionCommand) -> Result[DatasetInfo, str]:
        """Test connection to NeuPrint server."""
        try:
            info = self.connector.test_connection()

            dataset_info = DatasetInfo(
                name=info.get('dataset', 'Unknown'),
                version=info.get('version', 'Unknown'),
                server_url=info.get('server', 'Unknown'),
                connection_status='Connected'
            )

            return Ok(dataset_info)

        except Exception as e:
            return Err(f"Connection test failed: {str(e)}")


class QueueService:
    """Service for managing queue files."""

    def __init__(self, config):
        self.config = config
        # Load queued neuron types once during initialization
        self._queued_types: List[str] = self._load_queued_neuron_types()

    async def fill_queue(self, command: FillQueueCommand) -> Result[str, str]:
        """Create a YAML queue file with generate command options."""
        try:
            if command.neuron_type is not None:
                # Single neuron type mode
                return await self._create_single_queue_file(command)
            else:
                # Batch mode - discover neuron types
                return await self._create_batch_queue_files(command)

        except Exception as e:
            return Err(f"Failed to create queue file: {str(e)}")

    async def _create_single_queue_file(self, command: FillQueueCommand) -> Result[str, str]:
        """Create a single queue file for a specific neuron type."""
        if command.neuron_type is None:
            return Err("Neuron type is required for single queue file creation")

        # Import PageGenerator to use filename generation logic
        from .page_generator import PageGenerator

        # Create a temporary page generator to get the filename logic
        temp_generator = PageGenerator(self.config, self.config.output.directory, None)

        # Convert soma_side enum to string for filename generation
        soma_side_str = command.soma_side.value
        if command.soma_side == SomaSide.BOTH:
            soma_side_str = 'both'
        elif command.soma_side == SomaSide.ALL:
            soma_side_str = 'all'

        # Generate the HTML filename that would be created
        html_filename = temp_generator._generate_filename(
            command.neuron_type.value,
            soma_side_str
        )

        # Create YAML filename by replacing .html with .yaml
        yaml_filename = html_filename.replace('.html', '.yaml')

        # Create the queue directory if it doesn't exist
        queue_dir = Path(self.config.output.directory) / '.queue'
        queue_dir.mkdir(parents=True, exist_ok=True)

        # Full path to the YAML file
        yaml_path = queue_dir / yaml_filename

        # Prepare the generate command options
        queue_data = {
            'command': 'generate',
            'config_file': command.config_file,
            'options': {
                'neuron-type': command.neuron_type.value,
                'soma-side': command.soma_side.value,
                'output-dir': command.output_directory,
                'image-format': command.image_format,
                'embed': command.embed_images,
                'include-3d-view': command.include_3d_view,
            },
            'created_at': (command.requested_at or datetime.now()).isoformat()
        }

        # Remove None values to keep the YAML clean
        queue_data['options'] = {
            k: v for k, v in queue_data['options'].items()
            if v is not None
        }

        # Remove config_file if None
        if queue_data['config_file'] is None:
            del queue_data['config_file']

        # Write the YAML file
        with open(yaml_path, 'w') as f:
            yaml.dump(queue_data, f, default_flow_style=False, indent=2)

        # Update the central queue.yaml file (only in single mode)
        await self._update_queue_manifest([command.neuron_type.value])

        return Ok(str(yaml_path))

    async def _create_batch_queue_files(self, command: FillQueueCommand) -> Result[str, str]:
        """Create queue files for multiple neuron types."""
        from .neuprint_connector import NeuPrintConnector

        # Create connector for type discovery (optimized)
        connector = NeuPrintConnector(self.config)

        try:
            if command.all_types:
                # Optimized path: directly get all types without discovery service overhead
                type_names = connector.get_available_types()
                types = [NeuronTypeInfo(name=name) for name in type_names]
            else:
                # Use discovery service for filtered results
                discovery_service = NeuronDiscoveryService(connector, self.config)
                max_results = command.max_types

                list_command = ListNeuronTypesCommand(
                    max_results=max_results,
                    exclude_empty=False,  # Skip expensive empty filtering for queue creation
                    all_results=False,
                    show_statistics=False,  # No need for stats when creating queue files
                    sorted_results=False   # No need to sort for queue creation
                )

                list_result = await discovery_service.list_neuron_types(list_command)
                if list_result.is_err():
                    return Err(f"Failed to discover neuron types: {list_result.unwrap_err()}")
                types = list_result.unwrap()

            if not types:
                return Err("No neuron types found")
        except Exception as e:
            return Err(f"Failed to get neuron types: {str(e)}")

        # Create queue files for each type (optimized concurrent batch processing)
        created_files = []

        # Create queue directory once
        queue_dir = Path(self.config.output.directory) / '.queue'
        queue_dir.mkdir(parents=True, exist_ok=True)

        # Create all commands for concurrent processing
        batch_commands = []
        for type_info in types:
            # Create a command for this specific type
            single_command = FillQueueCommand(
                neuron_type=NeuronTypeName(type_info.name),
                soma_side=command.soma_side,
                output_directory=command.output_directory,
                include_3d_view=command.include_3d_view,
                image_format=command.image_format,
                embed_images=command.embed_images,
                config_file=command.config_file,
                requested_at=command.requested_at
            )
            batch_commands.append(single_command)

        # Process all commands concurrently with limited concurrency
        semaphore = asyncio.Semaphore(100)  # Limit concurrent file operations

        async def process_single_command(cmd):
            async with semaphore:
                return await self._create_single_queue_file_batch(cmd, queue_dir)

        results = await asyncio.gather(
            *[process_single_command(cmd) for cmd in batch_commands],
            return_exceptions=True
        )

        # Collect successful results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to create queue file for {batch_commands[i].neuron_type}: {result}")
            elif result.is_ok():
                created_files.append(batch_commands[i].neuron_type.value)

        if created_files:
            # Update the central queue.yaml file ONCE at the end
            await self._update_queue_manifest(created_files)
            return Ok(f"Created {len(created_files)} queue files")
        else:
            return Err("Failed to create any queue files")

    async def _create_single_queue_file_batch(self, command: FillQueueCommand, queue_dir: Path) -> Result[str, str]:
        """Create a single queue file for batch processing (no manifest update)."""
        if command.neuron_type is None:
            return Err("Neuron type is required for single queue file creation")

        # Import PageGenerator to use filename generation logic
        from .page_generator import PageGenerator

        # Create a temporary page generator to get the filename logic
        temp_generator = PageGenerator(self.config, self.config.output.directory, None)

        # Convert soma_side enum to string for filename generation
        soma_side_str = command.soma_side.value
        if command.soma_side == SomaSide.BOTH:
            soma_side_str = 'both'
        elif command.soma_side == SomaSide.ALL:
            soma_side_str = 'all'

        # Generate the HTML filename that would be created
        html_filename = temp_generator._generate_filename(
            command.neuron_type.value,
            soma_side_str
        )

        # Create YAML filename by replacing .html with .yaml
        yaml_filename = html_filename.replace('.html', '.yaml')

        # Full path to the YAML file (use pre-created queue_dir)
        yaml_path = queue_dir / yaml_filename

        # Prepare the generate command options
        queue_data = {
            'command': 'generate',
            'config_file': command.config_file,
            'options': {
                'neuron-type': command.neuron_type.value,
                'soma-side': command.soma_side.value,
                'output-dir': command.output_directory,
                'image-format': command.image_format,
                'embed': command.embed_images,
                'include-3d-view': command.include_3d_view,
            },
            'created_at': (command.requested_at or datetime.now()).isoformat()
        }

        # Remove None values to keep the YAML clean
        queue_data['options'] = {
            k: v for k, v in queue_data['options'].items()
            if v is not None
        }

        # Remove config_file if None
        if queue_data['config_file'] is None:
            del queue_data['config_file']

        # Write the YAML file synchronously (no manifest update in batch mode)
        try:
            with open(yaml_path, 'w') as f:
                yaml.dump(queue_data, f, default_flow_style=False, indent=2)
        except Exception as e:
            return Err(f"Failed to write queue file {yaml_path}: {str(e)}")

        return Ok(str(yaml_path))

    async def _update_queue_manifest(self, neuron_types: List[str]):
        """Update the central queue.yaml file with neuron types."""
        queue_dir = Path(self.config.output.directory) / '.queue'
        queue_manifest_path = queue_dir / 'queue.yaml'

        # Load existing manifest or create new one
        if queue_manifest_path.exists():
            with open(queue_manifest_path, 'r') as f:
                manifest_data = yaml.safe_load(f) or {}
        else:
            manifest_data = {}

        # Get existing neuron types or initialize empty list
        existing_types = set(manifest_data.get('neuron_types', []))

        # Add new neuron types (batch update)
        existing_types.update(neuron_types)

        # Update manifest data
        manifest_data.update({
            'neuron_types': sorted(list(existing_types)),
            'updated_at': datetime.now().isoformat(),
            'count': len(existing_types)
        })

        # Create created_at if it doesn't exist
        if 'created_at' not in manifest_data:
            manifest_data['created_at'] = datetime.now().isoformat()

        # Write updated manifest
        with open(queue_manifest_path, 'w') as f:
            yaml.dump(manifest_data, f, default_flow_style=False, indent=2)

        # Reload queued types since we just updated the manifest
        self._queued_types = self._load_queued_neuron_types()

    def _load_queued_neuron_types(self) -> List[str]:
        """Load queued neuron types from the queue manifest file."""
        queue_dir = Path(self.config.output.directory) / '.queue'
        queue_manifest_path = queue_dir / 'queue.yaml'

        if not queue_manifest_path.exists():
            logger.debug("Queue manifest file does not exist")
            return []

        try:
            logger.debug(f"Loading queued types from {queue_manifest_path}")
            with open(queue_manifest_path, 'r') as f:
                manifest_data = yaml.safe_load(f) or {}

            neuron_types = manifest_data.get('neuron_types', [])
            logger.debug(f"Loaded {len(neuron_types)} queued neuron types")
            return neuron_types

        except Exception as e:
            logger.warning(f"Failed to load queued types: {e}")
            return []

    def get_queued_neuron_types(self) -> List[str]:
        """Get list of neuron types in the queue manifest."""
        return self._queued_types

    async def pop_queue(self, command: PopCommand) -> Result[str, str]:
        """Pop and process a queue file."""
        try:
            # Get the queue directory
            queue_dir = Path(self.config.output.directory) / '.queue'

            # Check if queue directory exists
            if not queue_dir.exists():
                return Err("Queue directory does not exist")

            # Try to claim a file - keep trying until we succeed or run out of files
            while True:
                # Find all .yaml files in queue directory (refresh the list each time)
                # Exclude queue.yaml as it's a summary file, not a processable queue file
                yaml_files = [f for f in queue_dir.glob('*.yaml') if f.name != 'queue.yaml']

                if not yaml_files:
                    return Ok("No more queue files to process.")

                # Try to claim the first yaml file
                yaml_file = yaml_files[0]
                lock_file = yaml_file.with_suffix('.lock')

                try:
                    # Attempt to rename to .lock to claim it
                    yaml_file.rename(lock_file)
                    # Success! We claimed this file, break out of the loop
                    break
                except FileNotFoundError:
                    # File was deleted/renamed by another process, try next file
                    continue

            try:
                # Read the YAML content
                with open(lock_file, 'r') as f:
                    queue_data = yaml.safe_load(f)

                if not queue_data or 'options' not in queue_data:
                    raise ValueError("Invalid queue file format")

                options = queue_data['options']
                stored_config_file = queue_data.get('config_file')

                # Convert YAML options back to GeneratePageCommand
                generate_command = GeneratePageCommand(
                    neuron_type=NeuronTypeName(options['neuron-type']),
                    soma_side=SomaSide.from_string(options['soma-side']),
                    output_directory=command.output_directory or options.get('output-dir'),
                    image_format=options.get('image-format', 'svg'),
                    embed_images=options.get('embed', True),
                    include_3d_view=options.get('include-3d-view', False),
                    uncompress=command.uncompress
                )

                # Get page service from container (we need access to it)
                from .page_generator import PageGenerator
                from .neuprint_connector import NeuPrintConnector
                from .config import Config

                # Use the stored config file if available, otherwise use current config
                if stored_config_file:
                    config = Config.load(stored_config_file)
                else:
                    config = self.config

                # Create services with the appropriate config
                connector = NeuPrintConnector(config)

                # Create queue service to check for queued neuron types
                queue_service = QueueService(config)
                generator = PageGenerator(config, config.output.directory, queue_service)
                page_service = PageGenerationService(connector, generator, config)

                # Generate the page
                result = await page_service.generate_page(generate_command)

                if result.is_ok():
                    # Success - delete the lock file
                    lock_file.unlink()
                    return Ok(f"Generated {result.unwrap()} from queue file {yaml_file.name}")
                else:
                    # Failure - rename back to .yaml
                    lock_file.rename(yaml_file)
                    return Err(f"Generation failed: {result.unwrap_err()}")

            except Exception as e:
                # Any error during processing - rename back to .yaml
                if lock_file.exists():
                    lock_file.rename(yaml_file)
                raise e

        except Exception as e:
            return Err(f"Failed to pop queue: {str(e)}")


class IndexService:
    """Service for creating index pages that list all available neuron types."""

    def __init__(self, config, page_generator):
        self.config = config
        self.page_generator = page_generator
        self._roi_hierarchy_cache = None
        self._roi_parent_cache = {}
        self._batch_neuron_cache = {}
        self._persistent_roi_cache_path = None  # Will be set dynamically based on output directory

        # Initialize cache manager for neuron type data
        self.cache_manager = None
        if config and hasattr(config, 'output') and hasattr(config.output, 'directory'):
            from .cache import create_cache_manager
            self.cache_manager = create_cache_manager(config.output.directory)

    def _clean_roi_name(self, roi_name: str) -> str:
        """Remove (R) and (L) suffixes from ROI names."""
        import re
        # Remove (R), (L), or (M) suffixes from ROI names
        cleaned = re.sub(r'\s*\([RLM]\)$', '', roi_name)
        return cleaned.strip()

    def _neuron_name_to_filename(self, neuron_name: str) -> str:
        """Convert neuron name to filename format (same logic as PageGenerator._generate_filename)."""
        return neuron_name.replace('/', '_').replace(' ', '_')

    def _get_neuron_name_from_cache_or_db(self, filename: str, connector=None) -> str:
        """Get original neuron name from cache first, then fallback to database lookup."""
        # First try to find the original neuron name in cached data
        if self.cache_manager:
            cached_data = self.cache_manager.get_all_cached_data()
            for neuron_type, cache_data in cached_data.items():
                # Check if the cached neuron type would generate this filename
                if cache_data.original_neuron_name:
                    generated_filename = self._neuron_name_to_filename(cache_data.original_neuron_name)
                    if generated_filename == filename:
                        logger.debug(f"Found original neuron name from cache: {filename} -> {cache_data.original_neuron_name}")
                        return cache_data.original_neuron_name

        # Fallback to database lookup
        logger.debug(f"Cache miss for filename {filename}, falling back to database lookup")
        return self._filename_to_neuron_name(filename, connector)

    def _filename_to_neuron_name(self, filename: str, connector=None) -> str:
        """Convert filename back to original neuron name using database lookup."""
        # Since filename conversion is not reliably reversible (both '/' and ' ' become '_'),
        # we use a database lookup approach to find the correct neuron name

        if not connector:
            # Fallback to simple heuristic if no connector available
            return self._filename_to_neuron_name_heuristic(filename)

        try:
            # First, try the filename as-is (case where neuron name has no spaces/slashes)
            test_names = [filename]

            # Generate possible original names by trying different combinations of
            # replacing underscores with spaces and slashes
            import re

            # Handle special case: "Word._Word" -> "Word. Word"
            if re.search(r'\w+\._\w+', filename):
                test_names.append(re.sub(r'(\w+)\._(\w+)', r'\1. \2', filename))

            # Try replacing all underscores with spaces
            if '_' in filename:
                test_names.append(filename.replace('_', ' '))

            # Try combinations of slashes and spaces
            if '_' in filename:
                # Replace first underscore with slash, rest with spaces
                parts = filename.split('_')
                if len(parts) >= 2:
                    test_names.append(parts[0] + '/' + ' '.join(parts[1:]))

                # Try replacing some underscores with slashes (for cases like "A/B C")
                for i in range(1, len(parts)):
                    # Try slash at position i, spaces elsewhere
                    result_parts = parts.copy()
                    test_name = '/'.join(result_parts[:i+1]) + ' ' + ' '.join(result_parts[i+1:])
                    test_names.append(test_name.strip())

            # Test each candidate name against the database
            for candidate_name in test_names:
                if not candidate_name.strip():
                    continue

                try:
                    # Quick test: try to fetch neuron data for this name
                    neuron_data = connector.get_neuron_data(candidate_name, soma_side='both')
                    if neuron_data and neuron_data.get('neurons') is not None:
                        neurons_df = neuron_data['neurons']
                        if not neurons_df.empty:
                            # Found a match!
                            return candidate_name
                except:
                    # This candidate doesn't exist, try next one
                    continue

            # If no database match found, fall back to heuristic
            return self._filename_to_neuron_name_heuristic(filename)

        except Exception as e:
            # If anything goes wrong, fall back to heuristic
            logger.debug(f"Database lookup failed for filename '{filename}': {e}")
            return self._filename_to_neuron_name_heuristic(filename)

    def _filename_to_neuron_name_heuristic(self, filename: str) -> str:
        """Heuristic fallback for filename to neuron name conversion."""
        import re

        # Handle the "Tergotr._MN" -> "Tergotr. MN" pattern
        dot_underscore_pattern = r'(\w+)\._(\w+)'
        if re.search(dot_underscore_pattern, filename):
            # Replace the first ._  with '. ' (dot space)
            result = re.sub(r'(\w+)\._(\w+)', r'\1. \2', filename)
            # Replace remaining underscores with spaces
            return result.replace('_', ' ')

        # For names that already have underscores as part of the name (like PEN_b, AN05B054_a),
        # we need to be more careful. If the filename has no clear space markers,
        # assume underscores are part of the original name.

        # If filename contains parentheses or looks like a code, keep underscores
        if re.search(r'[()]|\w+\d+_[a-z]|\w+_[a-z]\(', filename):
            return filename

        # Otherwise, replace underscores with spaces
        return filename.replace('_', ' ')

    def _find_roi_parent_recursive(self, target_roi: str, current_dict: dict, parent_name: str = "") -> str:
        """Recursively search for ROI in hierarchy and return its parent."""
        for key, value in current_dict.items():
            cleaned_key = self._clean_roi_name(key.rstrip('*'))  # Remove stars too

            # If we found our target ROI, return the parent
            if cleaned_key == target_roi:
                return parent_name

            # If this is a dictionary, search recursively
            if isinstance(value, dict):
                result = self._find_roi_parent_recursive(target_roi, value, cleaned_key)
                if result:
                    return result

        return ""

    def _get_roi_hierarchy_cached(self, connector, output_dir=None):
        """Get ROI hierarchy with persistent caching to avoid repeated expensive fetches."""
        if self._roi_hierarchy_cache is None:
            # Try to load from cache manager first
            if self.cache_manager:
                self._roi_hierarchy_cache = self.cache_manager.load_roi_hierarchy()
                if self._roi_hierarchy_cache:
                    logger.info("Loaded ROI hierarchy from cache manager")
                    return self._roi_hierarchy_cache

            # Fallback to old persistent cache system
            # Set cache path based on output directory
            if output_dir and not self._persistent_roi_cache_path:
                cache_dir = Path(output_dir) / ".cache"
                cache_dir.mkdir(exist_ok=True)
                self._persistent_roi_cache_path = cache_dir / "roi_hierarchy.json"
            elif not self._persistent_roi_cache_path:
                # Fallback to default output directory
                cache_dir = Path(self.config.output.directory) / ".cache"
                cache_dir.mkdir(exist_ok=True)
                self._persistent_roi_cache_path = cache_dir / "roi_hierarchy.json"

            # Try to load from persistent cache first
            self._roi_hierarchy_cache = self._load_persistent_roi_cache()

            if not self._roi_hierarchy_cache:
                # Cache miss - fetch from database
                logger.warning("ROI hierarchy not found in cache, fetching from database")
                try:
                    from neuprint.queries import fetch_roi_hierarchy
                    import neuprint

                    original_client = neuprint.default_client
                    neuprint.default_client = connector.client
                    self._roi_hierarchy_cache = fetch_roi_hierarchy()
                    neuprint.default_client = original_client

                    # Save to both cache systems
                    self._save_persistent_roi_cache(self._roi_hierarchy_cache)
                    if self.cache_manager:
                        self.cache_manager.save_roi_hierarchy(self._roi_hierarchy_cache)

                except Exception:
                    self._roi_hierarchy_cache = {}
            else:
                logger.info("Loaded ROI hierarchy from persistent cache")

        return self._roi_hierarchy_cache

    def _get_roi_hierarchy_parent(self, roi_name: str, connector) -> str:
        """Get the parent ROI of the given ROI from the hierarchy."""
        # Check cache first
        if roi_name in self._roi_parent_cache:
            return self._roi_parent_cache[roi_name]

        try:
            hierarchy = self._get_roi_hierarchy_cached(connector)
            if not hierarchy:
                self._roi_parent_cache[roi_name] = ""
                return ""

            # Clean the ROI name first (remove (R), (L), (M) suffixes)
            cleaned_roi = self._clean_roi_name(roi_name)

            # Search recursively for the ROI and its parent
            parent = self._find_roi_parent_recursive(cleaned_roi, hierarchy)
            result = parent if parent else ""

            # Cache the result
            self._roi_parent_cache[roi_name] = result
            return result
        except Exception:
            # If any error occurs, cache empty result and return
            self._roi_parent_cache[roi_name] = ""
            return ""

    def _get_roi_summary_for_neuron_type(self, neuron_type: str, connector, skip_roi_analysis=False) -> tuple:
        """Get ROI summary for a specific neuron type."""
        # Skip expensive ROI analysis if requested for faster indexing
        if skip_roi_analysis:
            return [], ""

        try:
            # Get neuron data for both sides
            neuron_data = connector.get_neuron_data(neuron_type, soma_side='both')

            roi_counts = neuron_data.get('roi_counts')
            neurons = neuron_data.get('neurons')

            if (not neuron_data or
                roi_counts is None or roi_counts.empty or
                neurons is None or neurons.empty):
                return [], ""

            # Use the page generator's ROI aggregation method
            roi_summary = self.page_generator._aggregate_roi_data(
                neuron_data.get('roi_counts'),
                neuron_data.get('neurons'),
                'both',
                connector
            )

            # Filter ROIs by threshold and clean names
            # Only show ROIs with ≥1.5% of either input (post) or output (pre) connections
            # This ensures only significant innervation targets are displayed
            threshold = 1.5  # Percentage threshold for ROI significance
            cleaned_roi_summary = []
            seen_names = set()

            for roi in roi_summary:
                # Only include ROIs that pass the 1.5% threshold for input OR output
                if roi['pre_percentage'] >= threshold or roi['post_percentage'] >= threshold:
                    cleaned_name = self._clean_roi_name(roi['name'])
                    if cleaned_name and cleaned_name not in seen_names:
                        cleaned_roi_summary.append({
                            'name': cleaned_name,
                            'total': roi['total'],
                            'pre_percentage': roi['pre_percentage'],
                            'post_percentage': roi['post_percentage']
                        })
                        seen_names.add(cleaned_name)

                        if len(cleaned_roi_summary) >= 5:  # Limit to top 5
                            break

            # Get parent ROI for the highest ranking (first) ROI
            parent_roi = ""
            if cleaned_roi_summary:
                highest_roi = cleaned_roi_summary[0]['name']
                parent_roi = self._get_roi_hierarchy_parent(highest_roi, connector)

            return cleaned_roi_summary, parent_roi

        except Exception as e:
            # If there's any error fetching ROI data, return empty list and parent
            logger.warning(f"Failed to get ROI summary for {neuron_type}: {e}")
            return [], ""

    async def create_index(self, command: CreateIndexCommand) -> Result[str, str]:
        """Create an index page listing all neuron types found in the output directory."""
        try:
            from pathlib import Path
            import re
            from collections import defaultdict
            import time

            logger.info("Starting index creation using cached data")
            start_time = time.time()

            # Determine output directory
            output_dir = Path(command.output_directory or self.config.output.directory)
            if not output_dir.exists():
                return Err(f"Output directory does not exist: {output_dir}")

            # First try to use cached data, then fall back to scanning
            cached_data = {}
            if self.cache_manager:
                cached_data = self.cache_manager.get_all_cached_data()
                if cached_data:
                    logger.info(f"Found cached data for {len(cached_data)} neuron types")

            if cached_data:
                # Use cached data for fast index generation
                logger.info(f"Using cached data for {len(cached_data)} neuron types (fast mode)")
                neuron_types = defaultdict(set)

                for neuron_type, cache_data in cached_data.items():
                    # If no soma sides are available (e.g., all unknown), still include the neuron type
                    if not cache_data.soma_sides_available:
                        neuron_types[neuron_type].add('both')  # Default to 'both' for unknown sides
                    else:
                        for side in cache_data.soma_sides_available:
                            if side == "both":
                                neuron_types[neuron_type].add('both')
                            elif side == "left":
                                neuron_types[neuron_type].add('L')
                            elif side == "right":
                                neuron_types[neuron_type].add('R')
                            elif side == "middle":
                                neuron_types[neuron_type].add('M')

                scan_time = 0.0
            else:
                # Scan for HTML files and extract neuron types with soma sides
                scan_start = time.time()
                neuron_types = defaultdict(set)
                html_pattern = re.compile(r'^([A-Za-z0-9_+\-\.,&()\']+?)(?:_([LRM]))?\.html$')

                for html_file in output_dir.glob('*.html'):
                    match = html_pattern.match(html_file.name)
                    if match:
                        base_name = match.group(1)
                        soma_side = match.group(2)  # L, R, M, or None for both

                        # Skip if this looks like an index file
                        if base_name.lower() in ['index', 'main']:
                            continue

                        # Convert filename back to original neuron type name
                        # We'll pass the connector later for database lookup
                        original_name = base_name  # Temporarily use filename, will fix after connector is available

                        # For files like "NeuronType_L.html", extract just "NeuronType"
                        if soma_side:
                            neuron_types[original_name].add(soma_side)
                        else:
                            neuron_types[original_name].add('both')

                scan_time = time.time() - scan_start
                logger.info(f"File scanning completed in {scan_time:.3f}s, found {len(neuron_types)} neuron types")

            if not neuron_types:
                return Err("No neuron type HTML files found in output directory")

            # Create a single connector instance only if needed for fallback queries
            from .neuprint_connector import NeuPrintConnector
            connector = None

            # Pre-load ROI hierarchy from cache (no database queries if cached)
            roi_hierarchy_loaded = False
            if self.cache_manager:
                self._roi_hierarchy_cache = self.cache_manager.load_roi_hierarchy()
                if self._roi_hierarchy_cache:
                    logger.info("Loaded ROI hierarchy from cache - no database queries needed")
                    roi_hierarchy_loaded = True

            # Determine if we need neuron name correction based on data source
            if cached_data:
                # Fast mode: neuron_types already contains correct neuron names from cache
                logger.info("Using cached neuron names directly - no filename conversion needed")
                corrected_neuron_types = dict(neuron_types)
                names_needing_db_lookup = []
                neuron_name_cache_hits = len(neuron_types)
            else:
                # Scan mode: neuron_types contains filenames that need to be converted to neuron names
                logger.info("Converting filenames to neuron names using cache/database lookup")
                corrected_neuron_types = {}
                names_needing_db_lookup = []
                neuron_name_cache_hits = 0

                # Build a reverse lookup map for efficient filename-to-neuron-name mapping
                filename_to_neuron_map = {}
                if self.cache_manager:
                    cached_data_for_lookup = self.cache_manager.get_all_cached_data()
                    for neuron_type, cache_data in cached_data_for_lookup.items():
                        if cache_data.original_neuron_name:
                            generated_filename = self._neuron_name_to_filename(cache_data.original_neuron_name)
                            filename_to_neuron_map[generated_filename] = cache_data.original_neuron_name

                for filename_based_name, sides in neuron_types.items():
                    # Try to get correct name from cache first
                    if filename_based_name in filename_to_neuron_map:
                        original_name = filename_to_neuron_map[filename_based_name]
                        corrected_neuron_types[original_name] = sides
                        logger.debug(f"Found original neuron name from cache: {filename_based_name} -> {original_name}")
                        neuron_name_cache_hits += 1
                    else:
                        # Need database lookup for this name
                        names_needing_db_lookup.append((filename_based_name, sides))

            # Only initialize connector if we need database lookups
            if names_needing_db_lookup or not roi_hierarchy_loaded:
                try:
                    init_start = time.time()
                    connector = NeuPrintConnector(self.config)

                    # Load ROI hierarchy if not already cached
                    if not roi_hierarchy_loaded:
                        self._get_roi_hierarchy_cached(connector, output_dir)
                        logger.warning("ROI hierarchy not found in cache, had to fetch from database")

                    init_time = time.time() - init_start
                    logger.info(f"Database connector initialized in {init_time:.3f}s")

                    # Handle names that need database lookup
                    if names_needing_db_lookup:
                        logger.warning(f"Cache miss for {len(names_needing_db_lookup)} neuron name(s), using database lookup")
                        for filename_based_name, sides in names_needing_db_lookup:
                            correct_name = self._filename_to_neuron_name(filename_based_name, connector)
                            corrected_neuron_types[correct_name] = sides

                except Exception as e:
                    logger.warning(f"Failed to initialize connector: {e}")
                    # Use original names as fallback
                    for filename_based_name, sides in names_needing_db_lookup:
                        corrected_neuron_types[filename_based_name] = sides
            else:
                logger.info("✅ All meta information loaded from cache - no database queries needed!")

            neuron_types = corrected_neuron_types

            # Log cache performance for neuron name lookups
            total_names = len(neuron_types) + len(names_needing_db_lookup)
            if total_names > 0:
                cache_hit_rate = (neuron_name_cache_hits / total_names) * 100
                logger.info(f"Neuron name cache performance: {neuron_name_cache_hits}/{total_names} hits ({cache_hit_rate:.1f}%)")

            # Always use cached data - no batch processing or database queries needed
            index_data = []
            cached_count = 0
            missing_cache_count = 0

            for neuron_type, sides in neuron_types.items():
                # Check if we have cached data for this neuron type
                cache_data = cached_data.get(neuron_type) if cached_data else None

                has_both = 'both' in sides
                has_left = 'L' in sides
                has_right = 'R' in sides
                has_middle = 'M' in sides

                # Clean neuron type name for URLs
                clean_type = self._neuron_name_to_filename(neuron_type)

                entry = {
                    'name': neuron_type,
                    'has_both': has_both,
                    'has_left': has_left,
                    'has_right': has_right,
                    'has_middle': has_middle,
                    'both_url': f'{clean_type}.html' if has_both else None,
                    'left_url': f'{clean_type}_L.html' if has_left else None,
                    'right_url': f'{clean_type}_R.html' if has_right else None,
                    'middle_url': f'{clean_type}_M.html' if has_middle else None,
                    'roi_summary': [],
                    'parent_roi': '',
                    'total_count': 0,
                    'left_count': 0,
                    'right_count': 0,
                    'middle_count': 0,
                    'consensus_nt': None,
                    'celltype_predicted_nt': None,
                    'celltype_predicted_nt_confidence': None,
                    'celltype_total_nt_predictions': None,
                    'cell_class': None,
                    'cell_subclass': None,
                    'cell_superclass': None,
                }

                # Use cached data if available (NO DATABASE QUERIES!)
                if cache_data:
                    entry['roi_summary'] = cache_data.roi_summary
                    entry['parent_roi'] = cache_data.parent_roi
                    entry['total_count'] = cache_data.total_count
                    entry['left_count'] = cache_data.soma_side_counts.get('left', 0)
                    entry['right_count'] = cache_data.soma_side_counts.get('right', 0)
                    entry['middle_count'] = cache_data.soma_side_counts.get('middle', 0)
                    entry['consensus_nt'] = cache_data.consensus_nt
                    entry['celltype_predicted_nt'] = cache_data.celltype_predicted_nt
                    entry['celltype_predicted_nt_confidence'] = cache_data.celltype_predicted_nt_confidence
                    entry['celltype_total_nt_predictions'] = cache_data.celltype_total_nt_predictions
                    entry['cell_class'] = cache_data.cell_class
                    entry['cell_subclass'] = cache_data.cell_subclass
                    entry['cell_superclass'] = cache_data.cell_superclass
                    logger.debug(f"Used cached data for {neuron_type}")
                    cached_count += 1
                else:
                    # No cached data available - skip this neuron type or use minimal defaults
                    logger.warning(f"No cached data available for {neuron_type}, using minimal defaults")
                    missing_cache_count += 1

                index_data.append(entry)

            # Sort results
            index_data.sort(key=lambda x: x['name'])

            # Log cache usage summary
            total_types = len(neuron_types)
            logger.info(f"Index creation summary: {cached_count}/{total_types} neuron types used cached data, "
                       f"{missing_cache_count} types had no cache (used defaults)")
            # Log comprehensive cache performance summary
            total_efficiency_score = 0
            max_efficiency_score = 3  # ROI hierarchy + neuron names + neuron data

            if roi_hierarchy_loaded:
                total_efficiency_score += 1
            if not names_needing_db_lookup:
                total_efficiency_score += 1
            if cached_count == total_types:
                total_efficiency_score += 1

            if total_efficiency_score == max_efficiency_score:
                logger.info("✅ PERFECT: Complete cache-only index creation - no database queries performed!")
            else:
                logger.info(f"Cache efficiency: {total_efficiency_score}/{max_efficiency_score} components cached")

                if missing_cache_count > 0:
                    logger.warning(f"⚠️  {missing_cache_count} neuron types missing cache data - consider regenerating cache")
                if names_needing_db_lookup:
                    logger.warning(f"⚠️  {len(names_needing_db_lookup)} neuron names required database lookup - consider regenerating cache")
                if not roi_hierarchy_loaded:
                    logger.warning("⚠️  ROI hierarchy not cached - consider running generate to cache this data")



            # Group neuron types by parent ROI
            grouped_data = {}
            for entry in index_data:
                parent_roi = entry['parent_roi'] if entry['parent_roi'] else 'Other'
                if parent_roi not in grouped_data:
                    grouped_data[parent_roi] = []
                grouped_data[parent_roi].append(entry)

            # Sort groups by parent ROI name, but put 'Other' last
            sorted_groups = []
            for parent_roi in sorted(grouped_data.keys()):
                if parent_roi != 'Other':
                    sorted_groups.append({
                        'parent_roi': parent_roi,
                        'neuron_types': sorted(grouped_data[parent_roi], key=lambda x: x['name'])
                    })

            # Add 'Other' group last if it exists
            if 'Other' in grouped_data:
                sorted_groups.append({
                    'parent_roi': 'Other',
                    'neuron_types': sorted(grouped_data['Other'], key=lambda x: x['name'])
                })

            # Collect filter options from neuron data
            roi_options = set()
            region_options = set()
            nt_options = set()
            superclass_options = set()
            class_options = set()
            subclass_options = set()

            for entry in index_data:
                # Collect ROIs from roi_summary
                if entry.get('roi_summary'):
                    for roi_info in entry['roi_summary']:
                        if isinstance(roi_info, dict) and 'name' in roi_info:
                            roi_name = roi_info['name']
                            if roi_name and roi_name.strip():
                                roi_options.add(roi_name.strip())

                # Collect regions from parent_roi
                if entry.get('parent_roi') and entry['parent_roi'].strip():
                    region_options.add(entry['parent_roi'].strip())

                # Collect neurotransmitters
                if entry.get('consensus_nt') and entry['consensus_nt'].strip():
                    nt_options.add(entry['consensus_nt'].strip())
                elif entry.get('celltype_predicted_nt') and entry['celltype_predicted_nt'].strip():
                    nt_options.add(entry['celltype_predicted_nt'].strip())

                # Collect class hierarchy
                if entry.get('cell_superclass') and entry['cell_superclass'].strip():
                    superclass_options.add(entry['cell_superclass'].strip())
                if entry.get('cell_class') and entry['cell_class'].strip():
                    class_options.add(entry['cell_class'].strip())
                if entry.get('cell_subclass') and entry['cell_subclass'].strip():
                    subclass_options.add(entry['cell_subclass'].strip())

            # Sort filter options
            sorted_roi_options = sorted(roi_options)
            sorted_region_options = sorted(region_options)
            # Put 'Other' at the end if it exists
            if 'Other' in sorted_region_options:
                sorted_region_options.remove('Other')
                sorted_region_options.append('Other')

            sorted_nt_options = sorted(nt_options)
            sorted_superclass_options = sorted(superclass_options)
            sorted_class_options = sorted(class_options)
            sorted_subclass_options = sorted(subclass_options)

            # Calculate cell count ranges using fixed values
            cell_count_ranges = []
            if index_data:
                # Extract all cell counts
                cell_counts = [entry['total_count'] for entry in index_data if entry.get('total_count', 0) > 0]

                if cell_counts:
                    # Define fixed ranges: 1, 2, 3, 4, 5, 6-10, 10-50, 50-100, 100-500, 500-1000, 1000-2000, 2000-5000, >5000
                    fixed_ranges = [
                        {'lower': 1, 'upper': 1, 'label': '1', 'value': '1-1'},
                        {'lower': 2, 'upper': 2, 'label': '2', 'value': '2-2'},
                        {'lower': 3, 'upper': 3, 'label': '3', 'value': '3-3'},
                        {'lower': 4, 'upper': 4, 'label': '4', 'value': '4-4'},
                        {'lower': 5, 'upper': 5, 'label': '5', 'value': '5-5'},
                        {'lower': 6, 'upper': 10, 'label': '6-10', 'value': '6-10'},
                        {'lower': 10, 'upper': 50, 'label': '10-50', 'value': '10-50'},
                        {'lower': 50, 'upper': 100, 'label': '50-100', 'value': '50-100'},
                        {'lower': 100, 'upper': 500, 'label': '100-500', 'value': '100-500'},
                        {'lower': 500, 'upper': 1000, 'label': '500-1000', 'value': '500-1000'},
                        {'lower': 1000, 'upper': 2000, 'label': '1000-2000', 'value': '1000-2000'},
                        {'lower': 2000, 'upper': 5000, 'label': '2000-5000', 'value': '2000-5000'},
                        {'lower': 5001, 'upper': float('inf'), 'label': '>5000', 'value': '5001-999999'}
                    ]

                    # Only include ranges that contain actual data
                    for range_def in fixed_ranges:
                        has_data = any(
                            range_def['lower'] <= count <= range_def['upper']
                            for count in cell_counts
                        )
                        if has_data:
                            cell_count_ranges.append(range_def)


            # Generate the index page using Jinja2
            render_start = time.time()
            template_data = {
                'config': self.config,
                'neuron_types': index_data,  # Keep for JavaScript filtering
                'grouped_neuron_types': sorted_groups,
                'total_types': len(index_data),
                'generation_time': command.requested_at,
                'filter_options': {
                    'rois': sorted_roi_options,
                    'regions': sorted_region_options,
                    'neurotransmitters': sorted_nt_options,
                    'superclasses': sorted_superclass_options,
                    'classes': sorted_class_options,
                    'subclasses': sorted_subclass_options,
                    'cell_count_ranges': cell_count_ranges
                }
            }

            # Use the page generator's Jinja environment
            template = self.page_generator.env.get_template('index_page.html')
            html_content = template.render(template_data)

            # Minify HTML content to reduce whitespace (without JS minification for index page)
            if not command.uncompress:
                html_content = self.page_generator._minify_html(html_content, minify_js=True)

            # Write the index file
            index_path = output_dir / command.index_filename
            index_path.write_text(html_content, encoding='utf-8')

            # Generate neuron-search.js file with discovered neuron types
            await self._generate_neuron_search_js(output_dir, index_data, command.requested_at)

            render_time = time.time() - render_start
            total_time = time.time() - start_time

            logger.info(f"Template rendering completed in {render_time:.3f}s")
            logger.info(f"Total optimized index creation: {total_time:.3f}s")

            return Ok(str(index_path))

        except Exception as e:
            logger.error(f"Failed to create optimized index: {e}")
            return Err(f"Failed to create index: {str(e)}")

    async def _generate_neuron_search_js(self, output_dir: Path, neuron_data: list, generation_time) -> None:
        """Generate the neuron-search.js file with embedded neuron types data."""
        import json
        from datetime import datetime

        # Prepare neuron types data for JavaScript
        neuron_types_for_js = []

        for neuron in neuron_data:
            # Create an entry with the neuron name and available URLs
            neuron_entry = {
                'name': neuron['name'],
                'urls': {}
            }

            # Add available URLs for this neuron type
            if neuron['both_url']:
                neuron_entry['urls']['both'] = neuron['both_url']
            if neuron['left_url']:
                neuron_entry['urls']['left'] = neuron['left_url']
            if neuron['right_url']:
                neuron_entry['urls']['right'] = neuron['right_url']
            if neuron['middle_url']:
                neuron_entry['urls']['middle'] = neuron['middle_url']

            # Set primary URL (prefer 'both' if available, otherwise first available)
            if neuron['both_url']:
                neuron_entry['primary_url'] = neuron['both_url']
            elif neuron['left_url']:
                neuron_entry['primary_url'] = neuron['left_url']
            elif neuron['right_url']:
                neuron_entry['primary_url'] = neuron['right_url']
            elif neuron['middle_url']:
                neuron_entry['primary_url'] = neuron['middle_url']
            else:
                neuron_entry['primary_url'] = f"{neuron['name']}.html"  # fallback

            neuron_types_for_js.append(neuron_entry)

        # Sort neuron types alphabetically
        neuron_types_for_js.sort(key=lambda x: x['name'])

        # Extract just the names for the simple search functionality
        neuron_names = [neuron['name'] for neuron in neuron_types_for_js]

        # Prepare template data
        js_template_data = {
            'neuron_types_json': json.dumps(neuron_names, indent=2),
            'neuron_types_data_json': json.dumps(neuron_types_for_js, indent=2),
            'generation_timestamp': generation_time.strftime("%Y-%m-%d %H:%M:%S") if generation_time else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'neuron_types': neuron_types_for_js
        }

        # Load and render the neuron-search.js template
        js_template = self.page_generator.env.get_template('static/js/neuron-search.js.template')
        js_content = js_template.render(js_template_data)

        # Ensure static/js directory exists
        js_dir = output_dir / 'static' / 'js'
        js_dir.mkdir(parents=True, exist_ok=True)

        # Write the neuron-search.js file
        js_path = js_dir / 'neuron-search.js'
        js_path.write_text(js_content, encoding='utf-8')




    def _load_persistent_roi_cache(self):
        """Load ROI hierarchy from persistent cache file."""
        try:
            import json
            from pathlib import Path

            if not self._persistent_roi_cache_path:
                return {}

            cache_path = Path(self._persistent_roi_cache_path)
            if cache_path.exists():
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)

                # Check if cache is still valid (e.g., less than 24 hours old)
                import time
                cache_age = time.time() - cache_data.get('timestamp', 0)
                if cache_age < 24 * 3600:  # 24 hours
                    logger.info("Loaded ROI hierarchy from persistent cache")
                    return cache_data.get('hierarchy', {})
                else:
                    logger.info("Persistent ROI cache expired")

        except Exception as e:
            logger.debug(f"Failed to load persistent ROI cache: {e}")

        return {}

    def _save_persistent_roi_cache(self, hierarchy):
        """Save ROI hierarchy to persistent cache file."""
        try:
            import json
            import time
            from pathlib import Path

            if not self._persistent_roi_cache_path:
                return

            cache_path = Path(self._persistent_roi_cache_path)
            cache_path.parent.mkdir(parents=True, exist_ok=True)

            cache_data = {
                'hierarchy': hierarchy,
                'timestamp': time.time()
            }

            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)

            logger.info(f"Saved ROI hierarchy to persistent cache: {cache_path}")

        except Exception as e:
            logger.warning(f"Failed to save persistent ROI cache: {e}")

class ServiceContainer:
    """Simple service container for dependency management."""

    def __init__(self, config):
        self.config = config
        self._neuprint_connector = None
        self._page_generator = None
        self._page_service = None
        self._discovery_service = None
        self._connection_service = None
        self._queue_service = None
        self._index_service = None

    @property
    def neuprint_connector(self):
        """Get or create NeuPrint connector."""
        if self._neuprint_connector is None:
            from .neuprint_connector import NeuPrintConnector
            self._neuprint_connector = NeuPrintConnector(self.config)
        return self._neuprint_connector

    @property
    def page_generator(self):
        """Get or create page generator."""
        if self._page_generator is None:
            from .page_generator import PageGenerator
            self._page_generator = PageGenerator(
                self.config,
                self.config.output.directory,
                self.queue_service
            )
        return self._page_generator

    @property
    def page_service(self) -> PageGenerationService:
        """Get or create page generation service."""
        if self._page_service is None:
            self._page_service = PageGenerationService(
                self.neuprint_connector,
                self.page_generator,
                self.config
            )
        return self._page_service

    @property
    def discovery_service(self) -> NeuronDiscoveryService:
        """Get or create neuron discovery service."""
        if self._discovery_service is None:
            self._discovery_service = NeuronDiscoveryService(
                self.neuprint_connector,
                self.config
            )
        return self._discovery_service

    @property
    def connection_service(self) -> ConnectionTestService:
        """Get or create connection test service."""
        if self._connection_service is None:
            self._connection_service = ConnectionTestService(
                self.neuprint_connector
            )
        return self._connection_service

    @property
    def queue_service(self) -> QueueService:
        """Get or create queue service."""
        if self._queue_service is None:
            self._queue_service = QueueService(self.config)
        return self._queue_service

    @property
    def index_service(self) -> IndexService:
        """Get or create index service."""
        if self._index_service is None:
            self._index_service = IndexService(self.config, self.page_generator)
        return self._index_service
