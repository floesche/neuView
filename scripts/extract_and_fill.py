#!/usr/bin/env python3
"""
Extract neuron types from config files and run fill-queue commands.

Usage:
    python scripts/extract_and_fill.py [config_file] [test_category]
"""

import yaml
import sys
import subprocess
import argparse
from pathlib import Path


def load_config(config_path: str) -> dict:
    """Load YAML config file."""
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing YAML file: {e}")
        sys.exit(1)


def extract_neuron_types(config: dict, test_category: str) -> list:
    """Extract neuron types from config for given test category."""
    test_neuron_types = config.get("test_neuron_types", {})

    if not test_neuron_types:
        print(f"❌ No 'test_neuron_types' section found in config")
        return []

    neuron_types = test_neuron_types.get(test_category, [])

    if not neuron_types:
        available_categories = list(test_neuron_types.keys())
        print(f"❌ No neuron types found for category '{test_category}'")
        if available_categories:
            print(f"Available categories: {', '.join(available_categories)}")
        return []

    return neuron_types


def run_fill_queue(neuron_type: str, config_file: str) -> bool:
    """Run neuview fill-queue command for a neuron type."""
    try:
        cmd = ["neuview", "fill-queue", "-n", neuron_type]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to process {neuron_type}: {e.stderr.strip()}")
        return False
    except FileNotFoundError:
        print("❌ 'neuview' command not found. Make sure it's installed and in PATH.")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Extract neuron types from config and run fill-queue"
    )
    parser.add_argument(
        "config_file",
        nargs="?",
        default="config.yaml",
        help="Path to config file (default: config.yaml)",
    )
    parser.add_argument(
        "test_category",
        nargs="?",
        default="normal-set",
        help="Test category to extract (default: normal-set)",
    )

    args = parser.parse_args()

    # Check if config file exists
    if not Path(args.config_file).exists():
        print(f"❌ Config file not found: {args.config_file}")
        sys.exit(1)

    # Load config
    config = load_config(args.config_file)

    # Extract neuron types
    neuron_types = extract_neuron_types(config, args.test_category)

    if not neuron_types:
        sys.exit(1)

    print(
        f"📋 Found {len(neuron_types)} neuron types for '{args.test_category}' in {args.config_file}"
    )

    # Show what will be processed
    for nt in neuron_types:
        print(f"  - {nt}")

    print(f"\n🚀 Processing neuron types...")

    success_count = 0
    for nt in neuron_types:
        if run_fill_queue(nt, args.config_file):
            print(f"✅ Processed: {nt}")
            success_count += 1
        # Error message is already printed in run_fill_queue

    print(
        f"\n🎉 Completed! Successfully processed {success_count}/{len(neuron_types)} neuron types"
    )

    if success_count < len(neuron_types):
        sys.exit(1)


if __name__ == "__main__":
    main()
