"""
Presentation layer for QuickPage.

The presentation layer handles user interface concerns, including the CLI.
It translates user input into application commands and presents results
back to the user.

This module imports all presentation classes from their separate files and exports
them for use throughout the application.
"""

import asyncio
import click
import sys
from pathlib import Path
from typing import Optional
import logging

from .cli_context import CLIContext
from ..config import Config
from ..application.commands import (
    GeneratePageCommand, GenerateBulkPagesCommand, DiscoverNeuronTypesCommand,
    TestConnectionCommand
)
from ..application.services import (
    PageGenerationService, NeuronDiscoveryService, ConnectionTestService
)
from ..infrastructure.repositories import (
    NeuPrintNeuronRepository, NeuPrintConnectivityRepository
)
from ..core.value_objects import NeuronTypeName, SomaSide
from ..shared.container import get_container, setup_container


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.option('--config', '-c', default='config.yaml', help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, config, verbose):
    """QuickPage - Generate HTML pages for neuron types from neuprint data."""
    ctx.ensure_object(dict)

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load configuration
    try:
        app_config = Config.load(config)
        ctx.obj['cli_context'] = CLIContext(app_config, verbose)

        if verbose:
            click.echo(f"Loaded configuration from {config}")

    except FileNotFoundError:
        click.echo(f"Error: Configuration file '{config}' not found.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--neuron-type', '-n', help='Specific neuron type to generate page for')
@click.option('--soma-side', '-s', type=click.Choice(['L', 'R', 'M', 'all']),
              default='all', help='Soma side to include')
@click.option('--output-dir', '-o', help='Output directory (overrides config)')
@click.option('--template', '-t', default='default', help='Template to use')
@click.option('--min-synapses', type=int, default=0, help='Minimum synapse count')
@click.option('--no-connectivity', is_flag=True, help='Skip connectivity data')
@click.pass_context
def generate(ctx, neuron_type, soma_side, output_dir, template, min_synapses, no_connectivity):
    """Generate HTML pages for neuron types."""
    cli_context: CLIContext = ctx.obj['cli_context']

    async def run_generation():
        try:
            service = cli_context.get_page_generation_service()

            if neuron_type:
                # Generate for specific neuron type
                command = GeneratePageCommand(
                    neuron_type=NeuronTypeName(neuron_type),
                    soma_side=SomaSide(soma_side),
                    output_directory=output_dir,
                    template_name=template,
                    include_connectivity=not no_connectivity,
                    min_synapse_count=min_synapses
                )

                if cli_context.verbose:
                    click.echo(f"Generating page for {neuron_type}...")

                result = await service.generate_page(command)

                if result.is_ok():
                    click.echo(f"Generated: {result.value}")
                else:
                    click.echo(f"Error: {result.error}", err=True)
                    sys.exit(1)
            else:
                # Discover types and generate for all
                discovery_service = cli_context.get_discovery_service()

                discovery_command = DiscoverNeuronTypesCommand(
                    max_types=cli_context.config.discovery.max_types,
                    type_filter_pattern=cli_context.config.discovery.type_filter,
                    exclude_types=cli_context.config.discovery.exclude_types,
                    include_only=cli_context.config.discovery.include_only,
                    randomize=cli_context.config.discovery.randomize
                )

                discovery_result = await discovery_service.discover_neuron_types(discovery_command)

                if discovery_result.is_err():
                    click.echo(f"Error discovering types: {discovery_result.error}", err=True)
                    sys.exit(1)

                discovered_types = discovery_result.value

                if not discovered_types:
                    click.echo("No neuron types found to generate")
                    return

                # Generate bulk pages
                bulk_command = GenerateBulkPagesCommand(
                    neuron_types=discovered_types,
                    soma_side=SomaSide(soma_side),
                    output_directory=output_dir,
                    template_name=template,
                    include_connectivity=not no_connectivity,
                    min_synapse_count=min_synapses
                )

                if cli_context.verbose:
                    click.echo(f"Generating pages for {len(discovered_types)} neuron types...")

                result = await service.generate_bulk_pages(bulk_command)

                if result.is_ok():
                    for path in result.value:
                        click.echo(f"Generated: {path}")
                else:
                    click.echo(f"Error: {result.error}", err=True)
                    sys.exit(1)

        except Exception as e:
            click.echo(f"Unexpected error: {e}", err=True)
            if cli_context.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)

    # Run the async function
    asyncio.run(run_generation())


@cli.command()
@click.option('--sorted', is_flag=True, help='Use alphabetical order instead of random selection')
@click.option('--show-soma-sides', is_flag=True, help='Show available soma sides')
@click.option('--summary', is_flag=True, help='Show summary statistics')
@click.pass_context
def list_types(ctx, sorted, show_soma_sides, summary):
    """List available neuron types."""
    cli_context: CLIContext = ctx.obj['cli_context']

    async def run_listing():
        try:
            service = cli_context.get_discovery_service()

            command = DiscoverNeuronTypesCommand(
                max_types=cli_context.config.discovery.max_types,
                type_filter_pattern=cli_context.config.discovery.type_filter,
                exclude_types=cli_context.config.discovery.exclude_types,
                include_only=cli_context.config.discovery.include_only,
                randomize=not sorted  # Invert the sorted flag
            )

            result = await service.discover_neuron_types(command)

            if result.is_err():
                click.echo(f"Error: {result.error}", err=True)
                sys.exit(1)

            discovered_types = result.value

            selection_method = "alphabetically ordered" if sorted else "randomly selected"
            click.echo(f"\nFound {len(discovered_types)} neuron types ({selection_method}):")

            for i, neuron_type in enumerate(discovered_types, 1):
                type_info = f"  {i}. {neuron_type}"

                if show_soma_sides:
                    # TODO: Get soma sides from repository
                    type_info += " (soma sides: L, R)"

                click.echo(type_info)

            if summary:
                click.echo(f"\nSummary:")
                click.echo(f"  Total types: {len(discovered_types)}")

        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            if cli_context.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)

    asyncio.run(run_listing())


@cli.command()
@click.pass_context
def test_connection(ctx):
    """Test connection to neuprint server."""
    cli_context: CLIContext = ctx.obj['cli_context']

    async def run_test():
        try:
            service = cli_context.get_connection_service()

            command = TestConnectionCommand(
                timeout_seconds=30,
                include_dataset_info=True
            )

            if cli_context.verbose:
                click.echo("Testing connection...")

            result = await service.test_connection(command)

            if result.is_ok():
                dataset_info = result.value.dataset_info
                click.echo("✓ Connection successful!")
                click.echo(f"Dataset: {dataset_info.name}")
                click.echo(f"Version: {dataset_info.version}")
                click.echo(f"Server: {dataset_info.server_url}")
            else:
                click.echo(f"✗ Connection failed: {result.error}", err=True)
                sys.exit(1)

        except Exception as e:
            click.echo(f"✗ Connection failed: {e}", err=True)
            if cli_context.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)

    asyncio.run(run_test())


def main():
    """Entry point for the CLI."""
    cli()


# Export all presentation components
__all__ = [
    'CLIContext',
    'cli',
    'main'
]


if __name__ == '__main__':
    main()
