"""
QuickPage CLI - Generate HTML pages for neuron types from neuprint data.
"""

import click
import yaml
import os
import sys
from pathlib import Path
from typing import Dict, Any

from .neuprint_connector import NeuPrintConnector
from .page_generator import PageGenerator
from .neuron_type import NeuronType
from .config import Config


@click.group()
@click.option('--config', '-c', default='config.yaml', help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, config, verbose):
    """QuickPage - Generate HTML pages for neuron types from neuprint data."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    # Load configuration
    try:
        ctx.obj['config'] = Config.load(config)
    except FileNotFoundError:
        click.echo(f"Error: Configuration file '{config}' not found.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--neuron-type', '-n', help='Specific neuron type to generate page for')
@click.option('--soma-side', '-s', type=click.Choice(['left', 'right', 'both']), 
              default='both', help='Soma side to include')
@click.option('--output-dir', '-o', help='Output directory (overrides config)')
@click.option('--sorted', is_flag=True, help='Use alphabetical order instead of random selection')
@click.pass_context
def generate(ctx, neuron_type, soma_side, output_dir, sorted):
    """Generate HTML pages for neuron types."""
    config = ctx.obj['config']
    verbose = ctx.obj['verbose']
    
    if verbose:
        click.echo("Starting page generation...")
    
    # Initialize neuprint connector
    try:
        connector = NeuPrintConnector(config)
        if verbose:
            click.echo("Connected to neuprint successfully")
    except Exception as e:
        click.echo(f"Error connecting to neuprint: {e}", err=True)
        sys.exit(1)
    
    # Initialize page generator
    output_directory = output_dir or config.output.directory
    generator = PageGenerator(config, output_directory)
    
    # Generate pages
    if neuron_type:
        # Generate for specific neuron type
        neuron_types = [neuron_type]
    else:
        # Auto-discover neuron types from the dataset
        if verbose:
            click.echo("Discovering neuron types from dataset...")
        try:
            # Override randomize setting if --sorted flag is used
            discovery_config = config.discovery
            if sorted:
                # Create a copy of the discovery config with randomize=False
                from dataclasses import replace
                discovery_config = replace(discovery_config, randomize=False)
            
            neuron_types = connector.discover_neuron_types(discovery_config)
            if verbose:
                click.echo(f"Found {len(neuron_types)} neuron types to process:")
                for nt in neuron_types:
                    click.echo(f"  - {nt}")
        except Exception as e:
            click.echo(f"Error discovering neuron types: {e}", err=True)
            sys.exit(1)
    
    for nt in neuron_types:
        if verbose:
            click.echo(f"Generating page for {nt}...")
        
        try:
            # Get neuron type configuration
            nt_config = config.get_neuron_type_config(nt)
            if not nt_config:
                # Create a default config if not found
                from .config import NeuronTypeConfig
                nt_config = NeuronTypeConfig(name=nt)
            
            # Create NeuronType instance
            neuron_type_obj = NeuronType(nt, nt_config, connector, soma_side)
            
            # Check if the neuron type has any data
            if not neuron_type_obj.has_data():
                if verbose:
                    click.echo(f"Skipping {nt}: No neurons found in dataset")
                else:
                    click.echo(f"Skipped {nt}: No neurons found")
                continue
            
            # Generate HTML page using the new method
            output_file = generator.generate_page_from_neuron_type(neuron_type_obj)
            
            click.echo(f"Generated: {output_file}")
            
        except Exception as e:
            click.echo(f"Error generating page for {nt}: {e}", err=True)
            if verbose:
                import traceback
                traceback.print_exc()


@cli.command()
@click.option('--sorted', is_flag=True, help='Use alphabetical order instead of random selection')
@click.pass_context
def list_types(ctx, sorted):
    """List available neuron types discovered from the dataset."""
    config = ctx.obj['config']
    verbose = ctx.obj['verbose']
    
    try:
        connector = NeuPrintConnector(config)
        
        click.echo("Discovering neuron types from dataset...")
        
        # Override randomize setting if --sorted flag is used
        discovery_config = config.discovery
        if sorted:
            # Create a copy of the discovery config with randomize=False
            from dataclasses import replace
            discovery_config = replace(discovery_config, randomize=False)
        
        discovered_types = connector.discover_neuron_types(discovery_config)
        
        selection_method = "alphabetically ordered" if not discovery_config.randomize else "randomly selected"
        click.echo(f"\nFound {len(discovered_types)} neuron types ({selection_method}, configured max: {config.discovery.max_types}):")
        
        if config.discovery.type_filter:
            click.echo(f"Type filter pattern: {config.discovery.type_filter}")
        if config.discovery.exclude_types:
            click.echo(f"Excluded types: {', '.join(config.discovery.exclude_types)}")
        if config.discovery.include_only:
            click.echo(f"Include only: {', '.join(config.discovery.include_only)}")
        
        click.echo("\nSelected neuron types:")
        for i, nt in enumerate(discovered_types, 1):
            click.echo(f"  {i}. {nt}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def test_connection(ctx):
    """Test connection to neuprint server."""
    config = ctx.obj['config']
    
    try:
        connector = NeuPrintConnector(config)
        info = connector.test_connection()
        click.echo("✓ Connection successful!")
        click.echo(f"Dataset: {info.get('dataset', 'Unknown')}")
        click.echo(f"Version: {info.get('version', 'Unknown')}")
    except Exception as e:
        click.echo(f"✗ Connection failed: {e}", err=True)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()
