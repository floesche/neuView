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
            
            # Get available soma sides for this neuron type if auto-discovering
            soma_sides_to_generate = [soma_side]  # Default to user-specified side
            
            if not neuron_type and soma_side == 'both':
                # For auto-discovered types, check what soma sides are actually available
                if verbose:
                    click.echo(f"  Checking available soma sides for {nt}...")
                try:
                    types_with_sides = connector.get_types_with_soma_sides()
                    if nt in types_with_sides and types_with_sides[nt]:
                        available_sides = types_with_sides[nt]
                        if len(available_sides) == 1:
                            # Only one side available, generate for that specific side
                            side_name = 'left' if available_sides[0] == 'L' else 'right'
                            soma_sides_to_generate = [side_name]
                            if verbose:
                                click.echo(f"  Found only {side_name} side available")
                        else:
                            # Multiple sides available, generate for both
                            soma_sides_to_generate = ['left', 'right']
                            if verbose:
                                click.echo(f"  Found both sides available")
                    else:
                        # No soma side info, use 'both' as fallback
                        soma_sides_to_generate = ['both']
                        if verbose:
                            click.echo(f"  No specific soma side info, using both")
                except Exception as e:
                    if verbose:
                        click.echo(f"  Warning: Could not get soma side info: {e}")
                    soma_sides_to_generate = ['both']
            
            # Generate pages for each soma side
            for current_soma_side in soma_sides_to_generate:
                if len(soma_sides_to_generate) > 1 and verbose:
                    click.echo(f"  Generating {current_soma_side} side...")
                
                # Create NeuronType instance
                neuron_type_obj = NeuronType(nt, nt_config, connector, current_soma_side)
                
                # Check if the neuron type has any data
                if not neuron_type_obj.has_data():
                    if verbose:
                        side_msg = f" ({current_soma_side} side)" if len(soma_sides_to_generate) > 1 else ""
                        click.echo(f"  Skipping {nt}{side_msg}: No neurons found in dataset")
                    elif len(soma_sides_to_generate) == 1:
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
@click.option('--show-soma-sides', is_flag=True, help='Show available soma sides for each neuron type')
@click.option('--summary', is_flag=True, help='Show summary statistics for discovered types')
@click.pass_context
def list_types(ctx, sorted, show_soma_sides, summary):
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
        
        # Get soma side information if requested or for summary
        types_with_sides = {}
        if show_soma_sides or summary:
            if verbose:
                click.echo("Fetching soma side information...")
            types_with_sides = connector.get_types_with_soma_sides()
        
        if summary:
            # Show summary statistics
            total_types = len(discovered_types)
            bilateral_count = 0
            unilateral_count = 0
            unknown_count = 0
            
            for nt in discovered_types:
                if nt in types_with_sides:
                    sides = types_with_sides[nt]
                    if len(sides) >= 2:
                        bilateral_count += 1
                    elif len(sides) == 1:
                        unilateral_count += 1
                    else:
                        unknown_count += 1
                else:
                    unknown_count += 1
            
            click.echo(f"\nSummary:")
            click.echo(f"  Total types: {total_types}")
            click.echo(f"  Bilateral (L&R): {bilateral_count}")
            click.echo(f"  Unilateral: {unilateral_count}")
            click.echo(f"  Unknown sides: {unknown_count}")
        
        click.echo("\nSelected neuron types:")
        for i, nt in enumerate(discovered_types, 1):
            if show_soma_sides and nt in types_with_sides:
                sides = types_with_sides[nt]
                if sides:
                    sides_str = f" (soma sides: {', '.join(sides)})"
                else:
                    sides_str = " (soma sides: unknown)"
                click.echo(f"  {i}. {nt}{sides_str}")
            else:
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
