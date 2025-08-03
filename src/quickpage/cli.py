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
@click.pass_context
def generate(ctx, neuron_type, soma_side, output_dir):
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
        # Generate for all configured neuron types
        neuron_types = [nt.name for nt in config.neuron_types]
    
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
            
            # Generate HTML page using the new method
            output_file = generator.generate_page_from_neuron_type(neuron_type_obj)
            
            click.echo(f"Generated: {output_file}")
            
        except Exception as e:
            click.echo(f"Error generating page for {nt}: {e}", err=True)
            if verbose:
                import traceback
                traceback.print_exc()


@cli.command()
@click.pass_context
def list_types(ctx):
    """List available neuron types from configuration."""
    config = ctx.obj['config']
    
    click.echo("Configured neuron types:")
    for nt in config.neuron_types:
        click.echo(f"  - {nt.name}: {nt.description or 'No description'}")


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
