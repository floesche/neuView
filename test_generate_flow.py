#!/usr/bin/env python3
"""
Test script to validate the generate command flow with the new services.

This script simulates the generate command flow without requiring a database connection
to ensure the refactoring didn't introduce any issues in the page generation process.
"""

import sys
import os
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, MagicMock
import tempfile

# Add src to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def create_mock_config():
    """Create a mock configuration object."""
    config = Mock()

    # Mock neuprint config
    config.neuprint = Mock()
    config.neuprint.server = "neuprint.janelia.org"
    config.neuprint.dataset = "hemibrain:v1.2.1"
    config.neuprint.token = "mock_token"

    # Mock output config
    config.output = Mock()
    config.output.directory = "/tmp/quickpage_test"
    config.output.template_dir = "templates"

    return config

def create_mock_neuron_data():
    """Create mock neuron data for testing."""
    neurons_df = pd.DataFrame({
        'bodyId': [12345, 23456, 34567, 45678, 56789],
        'pre': [100, 200, 150, 300, 250],
        'post': [50, 100, 75, 150, 125],
        'somaSide': ['L', 'R', 'L', 'R', 'M'],
        'type': ['SAD103', 'SAD103', 'SAD103', 'SAD103', 'SAD103']
    })

    roi_counts_df = pd.DataFrame({
        'bodyId': [12345, 23
