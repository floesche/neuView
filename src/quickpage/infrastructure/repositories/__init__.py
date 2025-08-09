"""
Infrastructure repositories for QuickPage.

These repositories implement the domain ports using external data sources
like NeuPrint. They handle the technical details of data access and
translate between external data formats and domain models.
"""

import os
import pandas as pd
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from neuprint import Client, NeuronCriteria, fetch_neurons

from ...core.ports import NeuronRepository, ConnectivityRepository
from ...core.entities import (
    Neuron, NeuronCollection, NeuronTypeConnectivity, ConnectivityPartner
)
from ...core.value_objects import (
    BodyId, SynapseCount, NeuronTypeName, SomaSide, RoiName, SynapseStatistics
)
from ...dataset_adapters import get_dataset_adapter
from ...config import Config

logger = logging.getLogger(__name__)


class NeuPrintNeuronRepository(NeuronRepository):
    """
    Repository implementation for accessing neuron data from NeuPrint.

    This adapter translates between the NeuPrint API and our domain model,
    handling data conversion and error management.
    """

    def __init__(self, config: Config):
        self.config = config
        self.client = None
        self.dataset_adapter = get_dataset_adapter(config.neuprint.dataset)
        self._connect()

    def _connect(self):
        """Establish connection to NeuPrint server."""
        server = self.config.neuprint.server
        dataset = self.config.neuprint.dataset

        # Get token from config or environment
        token = self.config.neuprint.token or os.getenv('NEUPRINT_TOKEN')

        if not token:
            raise ValueError(
                "NeuPrint token not found. Set it in one of these ways:\n"
                "1. Create a .env file with NEUPRINT_TOKEN=your_token\n"
                "2. Set NEUPRINT_TOKEN environment variable\n"
                "3. Add token to config.yaml"
            )

        try:
            self.client = Client(server, dataset=dataset, token=token)
            logger.info(f"Connected to NeuPrint: {server}/{dataset}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to NeuPrint: {e}")

    async def find_by_type(self, neuron_type: NeuronTypeName) -> NeuronCollection:
        """Find all neurons of a specific type."""
        if not self.client:
            raise ConnectionError("Not connected to NeuPrint")

        try:
            # Build criteria for neuron search
            criteria = NeuronCriteria(type=str(neuron_type))

            # Fetch neuron data
            neurons_df, roi_df = fetch_neurons(criteria)

            # Process data using dataset adapter
            if not neurons_df.empty:
                neurons_df = self.dataset_adapter.normalize_columns(neurons_df)
                neurons_df = self.dataset_adapter.extract_soma_side(neurons_df)

            # Convert to domain entities
            neurons = self._convert_dataframe_to_neurons(neurons_df, roi_df, neuron_type)

            collection = NeuronCollection(
                type_name=neuron_type,
                neurons=neurons,
                fetched_from=f"{self.config.neuprint.server}/{self.config.neuprint.dataset}"
            )

            logger.info(f"Found {len(neurons)} neurons for type {neuron_type}")
            return collection

        except Exception as e:
            logger.error(f"Failed to fetch neurons for type {neuron_type}: {e}")
            raise

    async def find_by_type_and_side(
        self,
        neuron_type: NeuronTypeName,
        soma_side: SomaSide
    ) -> NeuronCollection:
        """Find neurons of a specific type and soma side."""
        # First get all neurons of the type
        collection = await self.find_by_type(neuron_type)

        # Filter by soma side if not 'all'
        if soma_side.value and soma_side.value != 'all':
            filtered_collection = collection.filter_by_soma_side(soma_side)
            return filtered_collection

        return collection

    async def find_by_body_id(self, body_id: BodyId) -> Optional[Neuron]:
        """Find a neuron by its body ID."""
        if not self.client:
            raise ConnectionError("Not connected to NeuPrint")

        try:
            # Build criteria for specific body ID
            criteria = NeuronCriteria(bodyId=body_id.value)

            # Fetch neuron data
            neurons_df, roi_df = fetch_neurons(criteria)

            if neurons_df.empty:
                return None

            # Process data using dataset adapter
            neurons_df = self.dataset_adapter.normalize_columns(neurons_df)
            neurons_df = self.dataset_adapter.extract_soma_side(neurons_df)

            # Convert to domain entity (should be only one)
            neurons = self._convert_dataframe_to_neurons(neurons_df, roi_df)

            return neurons[0] if neurons else None

        except Exception as e:
            logger.error(f"Failed to fetch neuron {body_id}: {e}")
            raise

    async def get_available_types(self) -> List[NeuronTypeName]:
        """Get all available neuron types in the dataset."""
        if not self.client:
            raise ConnectionError("Not connected to NeuPrint")

        try:
            # Query for distinct neuron types
            query = """
                MATCH (n :Neuron)
                WHERE n.type IS NOT NULL AND n.type <> ""
                RETURN DISTINCT n.type as type
                ORDER BY n.type
            """

            result = self.client.fetch_custom(query)

            types = [NeuronTypeName(row['type']) for _, row in result.iterrows()]

            logger.info(f"Found {len(types)} available neuron types")
            return types

        except Exception as e:
            logger.error(f"Failed to get available types: {e}")
            raise

    async def get_types_with_soma_sides(self) -> Dict[NeuronTypeName, List[str]]:
        """Get neuron types with their available soma sides."""
        if not self.client:
            raise ConnectionError("Not connected to NeuPrint")

        try:
            # Query for types with soma side information
            query = """
                MATCH (n :Neuron)
                WHERE n.type IS NOT NULL AND n.type <> ""
                WITH n.type as type,
                     CASE
                         WHEN n.somaLocation IS NOT NULL
                         THEN n.somaLocation
                         ELSE "unknown"
                     END as soma_side
                RETURN type, collect(DISTINCT soma_side) as soma_sides
                ORDER BY type
            """

            result = self.client.fetch_custom(query)

            types_with_sides = {}
            for _, row in result.iterrows():
                neuron_type = NeuronTypeName(row['type'])
                # Filter out 'unknown' sides and normalize
                sides = [
                    side for side in row['soma_sides']
                    if side != 'unknown' and side is not None
                ]
                types_with_sides[neuron_type] = sides

            logger.info(f"Got soma side info for {len(types_with_sides)} types")
            return types_with_sides

        except Exception as e:
            logger.error(f"Failed to get types with soma sides: {e}")
            raise

    async def test_connection(self) -> Dict[str, Any]:
        """Test the connection to the data source."""
        if not self.client:
            raise ConnectionError("Not connected to NeuPrint")

        try:
            # Try to get dataset info
            info = self.client.fetch_database()

            return {
                'dataset': self.config.neuprint.dataset,
                'version': info.get('version', 'Unknown'),
                'server': self.config.neuprint.server,
                'status': 'connected'
            }
        except Exception as e:
            raise ConnectionError(f"Connection test failed: {e}")

    def _convert_dataframe_to_neurons(
        self,
        neurons_df: pd.DataFrame,
        roi_df: pd.DataFrame,
        expected_type: Optional[NeuronTypeName] = None
    ) -> List[Neuron]:
        """Convert pandas DataFrame to domain Neuron entities."""
        neurons = []

        for _, neuron_row in neurons_df.iterrows():
            try:
                # Extract basic neuron information
                body_id = BodyId(int(neuron_row['bodyId']))

                # Use expected type or extract from data
                if expected_type:
                    neuron_type = expected_type
                else:
                    type_value = neuron_row.get('type', 'Unknown')
                    neuron_type = NeuronTypeName(str(type_value))

                # Extract soma side
                soma_side_value = neuron_row.get('somaLocation')
                soma_side = SomaSide(soma_side_value)

                # Extract synapse counts
                pre_count = int(neuron_row.get('pre', 0))
                post_count = int(neuron_row.get('post', 0))

                synapse_stats = SynapseStatistics(
                    pre_synapses=SynapseCount(pre_count),
                    post_synapses=SynapseCount(post_count)
                )

                # Extract ROI information if available
                roi_counts = {}
                if not roi_df.empty:
                    neuron_roi_data = roi_df[roi_df['bodyId'] == body_id.value]
                    for _, roi_row in neuron_roi_data.iterrows():
                        roi_name = RoiName(str(roi_row['roi']))
                        roi_count = int(roi_row.get('pre', 0) + roi_row.get('post', 0))
                        if roi_count > 0:
                            roi_counts[roi_name] = SynapseCount(roi_count)

                # Create neuron entity
                neuron = Neuron(
                    body_id=body_id,
                    neuron_type=neuron_type,
                    soma_side=soma_side,
                    synapse_stats=synapse_stats,
                    roi_counts=roi_counts
                )

                neurons.append(neuron)

            except Exception as e:
                logger.warning(f"Skipping invalid neuron data: {e}")
                continue

        return neurons


class NeuPrintConnectivityRepository(ConnectivityRepository):
    """
    Repository implementation for accessing connectivity data from NeuPrint.
    """

    def __init__(self, config: Config):
        self.config = config
        self.client = None
        self._connect()

    def _connect(self):
        """Establish connection to NeuPrint server."""
        server = self.config.neuprint.server
        dataset = self.config.neuprint.dataset

        # Get token from config or environment
        token = self.config.neuprint.token or os.getenv('NEUPRINT_TOKEN')

        if not token:
            raise ValueError("NeuPrint token not found")

        try:
            self.client = Client(server, dataset=dataset, token=token)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to NeuPrint: {e}")

    async def get_connectivity_for_type(
        self,
        neuron_type: NeuronTypeName
    ) -> NeuronTypeConnectivity:
        """Get connectivity information for a neuron type."""
        if not self.client:
            raise ConnectionError("Not connected to NeuPrint")

        try:
            # Get upstream partners
            upstream_query = f"""
                MATCH (upstream)-[c:ConnectsTo]->(downstream :Neuron)
                WHERE downstream.type = "{neuron_type}"
                WITH upstream.type as partner_type, sum(c.weight) as synapse_count
                WHERE partner_type IS NOT NULL AND partner_type <> ""
                RETURN partner_type, synapse_count
                ORDER BY synapse_count DESC
                LIMIT 50
            """

            upstream_result = self.client.fetch_custom(upstream_query)
            upstream_partners = []

            for _, row in upstream_result.iterrows():
                partner = ConnectivityPartner(
                    partner_type=NeuronTypeName(row['partner_type']),
                    synapse_count=SynapseCount(int(row['synapse_count']))
                )
                upstream_partners.append(partner)

            # Get downstream partners
            downstream_query = f"""
                MATCH (upstream :Neuron)-[c:ConnectsTo]->(downstream)
                WHERE upstream.type = "{neuron_type}"
                WITH downstream.type as partner_type, sum(c.weight) as synapse_count
                WHERE partner_type IS NOT NULL AND partner_type <> ""
                RETURN partner_type, synapse_count
                ORDER BY synapse_count DESC
                LIMIT 50
            """

            downstream_result = self.client.fetch_custom(downstream_query)
            downstream_partners = []

            for _, row in downstream_result.iterrows():
                partner = ConnectivityPartner(
                    partner_type=NeuronTypeName(row['partner_type']),
                    synapse_count=SynapseCount(int(row['synapse_count']))
                )
                downstream_partners.append(partner)

            connectivity = NeuronTypeConnectivity(
                type_name=neuron_type,
                upstream_partners=upstream_partners,
                downstream_partners=downstream_partners
            )

            logger.info(f"Got connectivity for {neuron_type}: {len(upstream_partners)} upstream, {len(downstream_partners)} downstream")
            return connectivity

        except Exception as e:
            logger.error(f"Failed to get connectivity for {neuron_type}: {e}")
            raise

    async def get_connectivity_between_types(
        self,
        source_type: NeuronTypeName,
        target_type: NeuronTypeName
    ) -> Optional[int]:
        """Get synapse count between two neuron types."""
        if not self.client:
            raise ConnectionError("Not connected to NeuPrint")

        try:
            query = f"""
                MATCH (source :Neuron)-[c:ConnectsTo]->(target :Neuron)
                WHERE source.type = "{source_type}" AND target.type = "{target_type}"
                RETURN sum(c.weight) as total_synapses
            """

            result = self.client.fetch_custom(query)

            if result.empty or result.iloc[0]['total_synapses'] is None:
                return None

            return int(result.iloc[0]['total_synapses'])

        except Exception as e:
            logger.error(f"Failed to get connectivity between {source_type} and {target_type}: {e}")
            raise


# Export repository implementations
__all__ = [
    'NeuPrintNeuronRepository',
    'NeuPrintConnectivityRepository'
]
