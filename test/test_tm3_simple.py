"""
Simple test to verify Tm3 neuron type exists in the database.

This is a focused test that specifically checks for the presence of the Tm3
neuron type in the NeuPrint database. Tm3 is a well-known visual system neuron
type that should be present in the hemibrain dataset.
"""

import pytest
import sys
import os

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from quickpage.config import Config
from quickpage.neuprint_connector import NeuPrintConnector


@pytest.mark.integration
def test_tm3_neuron_type_exists():
    """
    Test that the Tm3 neuron type exists in the database.

    This test:
    1. Connects to the NeuPrint database
    2. Retrieves all available neuron types
    3. Confirms that 'Tm3' is in the list
    """
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")

    if os.path.exists(config_path):
        try:
            config = Config.load(config_path)
        except Exception:
            config = Config.create_minimal_for_testing()
    else:
        config = Config.create_minimal_for_testing()

    # Create connector and test
    connector = NeuPrintConnector(config)

    try:
        # Get all available neuron types
        available_types = connector.get_available_types()

        # Verify we got a valid response
        assert isinstance(available_types, list), "Expected list of neuron types"
        assert len(available_types) > 0, "Expected non-empty list of neuron types"

        # Check for Tm3 specifically
        assert "Tm3" in available_types, (
            f"Tm3 not found in {len(available_types)} available neuron types"
        )

        print(
            f"SUCCESS: Tm3 found in database with {len(available_types)} total neuron types"
        )

    except ConnectionError as e:
        pytest.skip(f"Could not connect to NeuPrint database: {e}")
    except Exception as e:
        pytest.fail(f"Test failed: {e}")


if __name__ == "__main__":
    # Allow running this test directly
    test_tm3_neuron_type_exists()
    print("✓ Test passed - Tm3 neuron type exists in database")
