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
    soma_side: SomaSide = SomaSide.COMBINED

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
class CreateListCommand:
    """Command to create an index page listing all neuron types."""
    output_directory: Optional[str] = None
    index_filename: str = "types.html"
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
            if command.soma_side == SomaSide.COMBINED:
                legacy_soma_side = 'combined'
            elif command.soma_side == SomaSide.LEFT:
                legacy_soma_side = 'left'
            elif command.soma_side == SomaSide.RIGHT:
                legacy_soma_side = 'right'
            elif command.soma_side == SomaSide.MIDDLE:
                legacy_soma_side = 'middle'
            else:
                legacy_soma_side = 'combined'

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
                        roi_counts_df, neurons_df, 'combined', self.connector
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

            # Extract column data from PageGenerator if available
            columns_data = None
            region_columns_map = None
            try:
                if hasattr(self, 'generator') and hasattr(self.generator, '_neuron_type_columns_cache'):
                    cache_key = f"columns_{neuron_type_name}"
                    if cache_key in self.generator._neuron_type_columns_cache:
                        type_columns, type_region_map = self.generator._neuron_type_columns_cache[cache_key]
                        columns_data = type_columns
                        # Convert sets to lists for JSON serialization
                        region_columns_map = {}
                        for region, coords_set in type_region_map.items():
                            region_columns_map[region] = list(coords_set)
                        logger.debug(f"Extracted column data for {neuron_type_name}: {len(columns_data)} columns")
            except Exception as e:
                logger.debug(f"Failed to extract column data for {neuron_type_name}: {e}")

            # Create enhanced cache data with connectivity and distribution information
            cache_data = NeuronTypeCacheData.from_neuron_collection(
                neuron_collection=neuron_collection,
                roi_summary=roi_summary,
                parent_roi=parent_roi,
                connectivity_data=connectivity_data,
                neuron_data_df=neurons_df,
                columns_data=columns_data,
                region_columns_map=region_columns_map
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

            # First, check what data is available with 'combined'
            neuron_type_obj = NeuronType(
                neuron_type_name,
                config,
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

                # Save to persistent cache for index generation (use 'combined' data for comprehensive info)
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
                        neuron_type_obj = NeuronType(type_name, config, self.connector, soma_side='combined')

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
            if command.soma_side in [SomaSide.ALL, SomaSide.COMBINED]:
                legacy_soma_side = 'combined'
            elif command.soma_side == SomaSide.LEFT:
                legacy_soma_side = 'left'
            elif command.soma_side == SomaSide.RIGHT:
                legacy_soma_side = 'right'
            elif command.soma_side == SomaSide.MIDDLE:
                legacy_soma_side = 'middle'
            else:
                legacy_soma_side = 'combined'

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

        # Import PageGenerator for static filename generation
        from .page_generator import PageGenerator

        # Convert soma_side enum to string for filename generation
        soma_side_str = command.soma_side.value
        if command.soma_side == SomaSide.COMBINED:
            soma_side_str = 'combined'
        elif command.soma_side == SomaSide.ALL:
            soma_side_str = 'all'

        # Generate the HTML filename that would be created
        html_filename = PageGenerator.generate_filename(
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

        # Import PageGenerator for static filename generation
        from .page_generator import PageGenerator

        # Convert soma_side enum to string for filename generation
        soma_side_str = command.soma_side.value
        if command.soma_side == SomaSide.COMBINED:
            soma_side_str = 'combined'
        elif command.soma_side == SomaSide.ALL:
            soma_side_str = 'all'

        # Generate the HTML filename that would be created
        html_filename = PageGenerator.generate_filename(
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
                from .cache import create_cache_manager
                cache_manager = create_cache_manager(config.output.directory)
                generator = PageGenerator(config, config.output.directory, queue_service, cache_manager)
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


# Import the new modular IndexService from the specialized_services package
# Note: Import moved to method level to avoid circular imports

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
        self._cache_manager = None
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
                self.queue_service,
                self.cache_manager
            )
        return self._page_generator

    @property
    def cache_manager(self):
        """Get or create cache manager."""
        if self._cache_manager is None:
            from .cache import create_cache_manager
            self._cache_manager = create_cache_manager(self.config.output.directory)
        return self._cache_manager

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
    def index_service(self):
        """Get or create index service."""
        if self._index_service is None:
            from .services import IndexService
            self._index_service = IndexService(self.config, self.page_generator)
        return self._index_service
