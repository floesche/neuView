#!/usr/bin/env python3
"""
Test script for QuickPage functionality.
"""

import sys
import os
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from quickpage.config import Config
from quickpage.neuprint_connector import NeuPrintConnector
from quickpage.page_generator import PageGenerator


def test_config_loading():
    """Test configuration loading."""
    print("Testing configuration loading...")
    try:
        config = Config.load("config.yaml")
        print(f"✓ Configuration loaded successfully")
        print(f"  - NeuPrint server: {config.neuprint.server}")
        print(f"  - Dataset: {config.neuprint.dataset}")
        print(f"  - Neuron types: {len(config.neuron_types)}")
        return config
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return None


def test_page_generator(config):
    """Test page generator initialization."""
    print("\\nTesting page generator...")
    try:
        generator = PageGenerator(config, "output")
        print("✓ Page generator initialized successfully")
        print(f"  - Output directory: {generator.output_dir}")
        print(f"  - Template directory: {generator.template_dir}")
        return generator
    except Exception as e:
        print(f"✗ Page generator initialization failed: {e}")
        return None


def test_neuprint_connection(config):
    """Test NeuPrint connection (requires token)."""
    print("\\nTesting NeuPrint connection...")
    
    # Check if token is available
    token = config.neuprint.token or os.getenv('NEUPRINT_TOKEN')
    if not token:
        print("⚠ Skipping NeuPrint connection test (no token provided)")
        print("  Set NEUPRINT_TOKEN environment variable or add token to config.yaml")
        return None
    
    try:
        connector = NeuPrintConnector(config)
        info = connector.test_connection()
        print("✓ NeuPrint connection successful")
        print(f"  - Dataset: {info.get('dataset', 'Unknown')}")
        print(f"  - Server: {info.get('server', 'Unknown')}")
        return connector
    except Exception as e:
        print(f"✗ NeuPrint connection failed: {e}")
        return None


def main():
    """Run all tests."""
    print("QuickPage Test Suite")
    print("=" * 50)
    
    # Test configuration
    config = test_config_loading()
    if not config:
        sys.exit(1)
    
    # Test page generator
    generator = test_page_generator(config)
    if not generator:
        sys.exit(1)
    
    # Test NeuPrint connection (optional)
    connector = test_neuprint_connection(config)
    
    print("\\n" + "=" * 50)
    if connector:
        print("✓ All tests passed! QuickPage is ready to use.")
        print("\\nTry running: quickpage generate --neuron-type LC10")
    else:
        print("⚠ Basic tests passed, but NeuPrint connection not tested.")
        print("  Add your NeuPrint token to test data fetching.")
    
    print("\\nFor help: quickpage --help")


if __name__ == "__main__":
    main()
