"""
NeuPrint connectivity repository implementation for the infrastructure layer.

This repository implements the ConnectivityRepository port using the NeuPrint API
to access synaptic connectivity data from connectome datasets.
"""

import os
from typing import Optional
import logging

from neuprint import Client

from ...core.ports import ConnectivityRepository
from ...core.entities import NeuronTypeConnectivity, ConnectivityPartner
from ...core.value_objects import NeuronTypeName, SynapseCount
from ...config import Config

logger = logging.getLogger(__name__)


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
                partner_type_value = row['partner_type']
                synapse_count_value = row['synapse_count']

                # Handle pandas Series/numpy types
                if hasattr(partner_type_value, 'iloc'):
                    partner_type_value = partner_type_value.iloc[0] if len(partner_type_value) > 0 else 'Unknown'
                if hasattr(synapse_count_value, 'iloc'):
                    synapse_count_value = synapse_count_value.iloc[0] if len(synapse_count_value) > 0 else 0

                partner = ConnectivityPartner(
                    partner_type=NeuronTypeName(str(partner_type_value)),
                    synapse_count=SynapseCount(int(synapse_count_value or 0))
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
                partner_type_value = row['partner_type']
                synapse_count_value = row['synapse_count']

                # Handle pandas Series/numpy types
                if hasattr(partner_type_value, 'iloc'):
                    partner_type_value = partner_type_value.iloc[0] if len(partner_type_value) > 0 else 'Unknown'
                if hasattr(synapse_count_value, 'iloc'):
                    synapse_count_value = synapse_count_value.iloc[0] if len(synapse_count_value) > 0 else 0

                partner = ConnectivityPartner(
                    partner_type=NeuronTypeName(str(partner_type_value)),
                    synapse_count=SynapseCount(int(synapse_count_value or 0))
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
