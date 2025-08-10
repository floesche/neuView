"""
New CLI for QuickPage using Domain-Driven Design architecture.

This CLI uses the new DDD architecture with proper separation of concerns,
explicit error handling, and dependency injection.
"""

import asyncio
import click
import sys
from pathlib import Path
from typing import Optional
import logging

from .config import Config
from .application.commands import (
    GeneratePageCommand, GenerateBulkPagesCommand, DiscoverNeuronTypesCommand,
    TestConnectionCommand
)
from .application.services import (
    PageGenerationService, NeuronDiscoveryService, ConnectionTestService
)
from .application.queries import (
    ListNeuronTypesQuery, GetNeuronTypeQuery
)
from .neuprint_connector import NeuPrintConnector
from .page_generator import PageGenerator
from .core.value_objects import NeuronTypeName, SomaSide
from .shared.container import Container
from .shared.result import Result


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ApplicationBootstrap:
    """Bootstrap the application and set up dependencies."""

    def __init__(self, config: Config):
        self.config = config
        # Use legacy components temporarily
        self.neuprint_connector = NeuPrintConnector(config)
        self.page_generator = PageGenerator(config, config.output.directory)

    def get_page_service(self) -> PageGenerationService:
        """Get page generation service (stub for now)."""
        # Return a minimal service that uses legacy components
        class LegacyPageService:
            def __init__(self, connector, generator, config):
                self.connector = connector
                self.generator = generator
                self.config = config

            async def generate_page(self, command):
                try:
                    from .neuron_type import NeuronType
                    from .config import NeuronTypeConfig

                    # Get or create neuron type config
                    nt_config = self.config.get_neuron_type_config(str(command.neuron_type))
                    if not nt_config:
                        nt_config = NeuronTypeConfig(name=str(command.neuron_type))

                    neuron_type_obj = NeuronType(
                        str(command.neuron_type),
                        nt_config,
                        self.connector,
                        str(command.soma_side)
                    )

                    if not neuron_type_obj.has_data():
                        from .shared.result import Err
                        return Err(f"No neurons found for type {command.neuron_type}")

                    output_file = self.generator.generate_page_from_neuron_type(neuron_type_obj)
                    from .shared.result import Ok
                    return Ok(output_file)
                except Exception as e:
                    from .shared.result import Err
                    return Err(str(e))

        return LegacyPageService(self.neuprint_connector, self.page_generator, self.config)

    def get_discovery_service(self) -> NeuronDiscoveryService:
        """Get discovery service (stub for now)."""
        class LegacyDiscoveryService:
            def __init__(self, connector, config):
                self.connector = connector
                self.config = config

            async def discover_neuron_types(self, command):
                try:
                    from .core.value_objects import NeuronTypeName
                    discovered_types = self.connector.discover_neuron_types(self.config.discovery)
                    type_names = [NeuronTypeName(t) for t in discovered_types]
                    from .shared.result import Ok
                    return Ok(type_names)
                except Exception as e:
                    from .shared.result import Err
                    return Err(str(e))

        return LegacyDiscoveryService(self.neuprint_connector, self.config)

    def get_connection_service(self) -> ConnectionTestService:
        """Get connection service (stub for now)."""
        class LegacyConnectionService:
            def __init__(self, connector):
                self.connector = connector

            async def test_connection(self, command):
                try:
                    info = self.connector.test_connection()
                    from .application.queries import DatasetInfo, GetDatasetInfoQueryResult
                    dataset_info = DatasetInfo(
                        name=info.get('dataset', 'Unknown'),
                        version=info.get('version', 'Unknown'),
                        server_url=info.get('server', 'Unknown'),
                        connection_status='Connected'
                    )
                    result = GetDatasetInfoQueryResult(dataset_info=dataset_info)
                    from .shared.result import Ok
                    return Ok(result)
                except Exception as e:
                    from .shared.result import Err
                    return Err(str(e))

        return LegacyConnectionService(self.neuprint_connector)


class CLIContext:
    """Context object to hold shared CLI state."""

    def __init__(self, config: Config, verbose: bool = False):
        self.config = config
        self.verbose = verbose
        self.bootstrap = ApplicationBootstrap(config)

        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Verbose mode enabled")

    def get_page_service(self):
        return self.bootstrap.get_page_service()

    def get_discovery_service(self):
        return self.bootstrap.get_discovery_service()

    def get_connection_service(self):
        return self.bootstrap.get_connection_service()


def handle_result(result, success_msg: str = None, error_prefix: str = "Error"):
    """Handle a Result, printing success or error and exiting on failure."""
    if result.is_ok():
        if success_msg:
            click.echo(success_msg)
        return result.unwrap()
    else:
        click.echo(f"{error_prefix}: {result.error}", err=True)
        sys.exit(1)


@click.group()
@click.option('--config', '-c', default='config.yaml', help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, config, verbose):
    """QuickPage - Generate HTML pages for neuron types using modern DDD architecture."""
    ctx.ensure_object(dict)

    # Load configuration
    try:
        app_config = Config.load(config)
        ctx.obj['cli_context'] = CLIContext(app_config, verbose)

        if verbose:
            click.echo(f"✓ Loaded configuration from {config}")
            click.echo(f"✓ Connected to {app_config.neuprint.server}/{app_config.neuprint.dataset}")

    except FileNotFoundError:
        click.echo(f"Error: Configuration file '{config}' not found.", err=True)
        click.echo("Try running: cp config.example.yaml config.yaml", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--neuron-type', '-n', help='Specific neuron type to generate page for')
@click.option('--soma-side', '-s',
              type=click.Choice(['L', 'R', 'M', 'all', 'left', 'right', 'middle']),
              default='all', help='Soma side to include')
@click.option('--output-dir', '-o', help='Output directory (overrides config)')
@click.option('--template', '-t', default='default', help='Template to use')
@click.option('--min-synapses', type=int, default=0, help='Minimum synapse count filter')
@click.option('--no-connectivity', is_flag=True, help='Skip connectivity data')
@click.option('--no-3d', is_flag=True, help='Skip 3D view generation')
@click.option('--max-concurrent', type=int, default=5, help='Max concurrent generations (bulk mode)')
@click.pass_context
def generate(ctx, neuron_type, soma_side, output_dir, template, min_synapses,
             no_connectivity, no_3d, max_concurrent):
    """Generate HTML pages for neuron types."""
    cli_context: CLIContext = ctx.obj['cli_context']

    async def run_generation():
        service = cli_context.get_page_service()

        if neuron_type:
            # Single neuron type generation
            command = GeneratePageCommand(
                neuron_type=NeuronTypeName(neuron_type),
                soma_side=SomaSide(soma_side),
                output_directory=output_dir or cli_context.config.output.directory,
                template_name=template,
                include_connectivity=not no_connectivity,
                include_3d_view=not no_3d,
                min_synapse_count=min_synapses
            )

            if cli_context.verbose:
                click.echo(f"Generating page for {neuron_type} ({soma_side} side)...")

            result = await service.generate_page(command)
            if result.is_ok():
                output_path = result.unwrap()
                click.echo(f"✓ Generated: {output_path}")
            else:
                click.echo(f"Error: {result.error}", err=True)
                sys.exit(1)

        else:
            # Bulk generation - discover types first
            discovery_service = cli_context.get_discovery_service()

            discovery_command = DiscoverNeuronTypesCommand(
                max_types=cli_context.config.discovery.max_types,
                type_filter_pattern=cli_context.config.discovery.type_filter,
                exclude_types=cli_context.config.discovery.exclude_types,
                include_only=cli_context.config.discovery.include_only,
                randomize=cli_context.config.discovery.randomize
            )

            if cli_context.verbose:
                click.echo("Discovering available neuron types...")

            discovery_result = await discovery_service.discover_neuron_types(discovery_command)
            discovered_types = handle_result(discovery_result, "Discovery completed")

            if not discovered_types:
                click.echo("No neuron types found matching criteria")
                return

            click.echo(f"Found {len(discovered_types)} neuron types to process")

            # Bulk generation
            bulk_command = GenerateBulkPagesCommand(
                neuron_types=discovered_types,
                soma_side=SomaSide(soma_side),
                output_directory=output_dir or cli_context.config.output.directory,
                template_name=template,
                include_connectivity=not no_connectivity,
                include_3d_view=not no_3d,
                min_synapse_count=min_synapses,
                max_concurrent=max_concurrent
            )

            with click.progressbar(length=len(discovered_types),
                                   label='Generating pages') as bar:
                result = await service.generate_bulk_pages(bulk_command)
                bar.update(len(discovered_types))

            generated_paths = handle_result(result, "Bulk generation completed")

            click.echo(f"Successfully generated {len(generated_paths)} pages:")
            for path in generated_paths:
                click.echo(f"  • {path}")

    try:
        asyncio.run(run_generation())
    except KeyboardInterrupt:
        click.echo("\nGeneration cancelled by user")
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        if cli_context.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--sorted', is_flag=True, help='Use alphabetical order instead of random')
@click.option('--show-soma-sides', is_flag=True, help='Show available soma sides')
@click.option('--show-statistics', is_flag=True, help='Show neuron count statistics')
@click.option('--filter-pattern', help='Filter types by pattern')
@click.option('--max-results', type=int, default=50, help='Maximum results to show')
@click.pass_context
def list_types(ctx, sorted, show_soma_sides, show_statistics, filter_pattern, max_results):
    """List available neuron types with metadata."""
    cli_context: CLIContext = ctx.obj['cli_context']

    async def run_listing():
        service = cli_context.get_discovery_service()

        # Use discovery command for now since list_neuron_types isn't implemented
        discovery_command = DiscoverNeuronTypesCommand(
            max_types=max_results,
            type_filter_pattern=filter_pattern,
            randomize=not sorted
        )

        if cli_context.verbose:
            click.echo("Discovering available neuron types...")

        result = await service.discover_neuron_types(discovery_command)
        discovered_types = handle_result(result, "Discovery completed")

        # Display results
        selection_method = "alphabetically ordered" if sorted else "randomly selected"
        click.echo(f"\nFound {len(discovered_types)} neuron types ({selection_method}):")

        if filter_pattern:
            click.echo(f"Filtered by pattern: {filter_pattern}")

        for i, neuron_type in enumerate(discovered_types, 1):
            type_display = f"  {i:2d}. {neuron_type}"

            if show_soma_sides:
                type_display += " (sides: L, R)"  # Placeholder

            if show_statistics:
                type_display += " (neurons: N/A)"  # Placeholder

            click.echo(type_display)

        if show_statistics:
            click.echo(f"\nSummary: Statistics not available in this version")

    try:
        asyncio.run(run_listing())
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if cli_context.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--timeout', type=int, default=30, help='Connection timeout in seconds')
@click.option('--detailed', is_flag=True, help='Show detailed dataset information')
@click.pass_context
def test_connection(ctx, timeout, detailed):
    """Test connection to the NeuPrint server."""
    cli_context: CLIContext = ctx.obj['cli_context']

    async def run_test():
        service = cli_context.get_connection_service()

        command = TestConnectionCommand(
            timeout_seconds=timeout,
            include_dataset_info=detailed
        )

        if cli_context.verbose:
            click.echo(f"Testing connection to {cli_context.config.neuprint.server}...")

        result = await service.test_connection(command)
        dataset_info = handle_result(result, "Connection test completed").dataset_info

        # Display results
        click.echo("✓ Connection successful!")
        click.echo(f"  Server: {dataset_info.server_url}")
        click.echo(f"  Dataset: {dataset_info.name}")
        click.echo(f"  Version: {dataset_info.version}")
        click.echo(f"  Status: {dataset_info.connection_status}")

        if detailed and dataset_info.available_neuron_types:
            click.echo(f"  Available neuron types: {dataset_info.available_neuron_types}")

    try:
        asyncio.run(run_test())
    except Exception as e:
        click.echo(f"✗ Connection failed: {e}", err=True)
        if cli_context.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument('neuron_type')
@click.option('--soma-side', '-s', default='all', help='Soma side filter')
@click.option('--min-synapses', type=int, default=0, help='Minimum synapse count')
@click.pass_context
def inspect(ctx, neuron_type, soma_side, min_synapses):
    """Inspect detailed information about a specific neuron type."""
    cli_context: CLIContext = ctx.obj['cli_context']

    async def run_inspection():
        service = cli_context.get_discovery_service()

        # Use legacy neuron type inspection for now
        try:
            from .neuron_type import NeuronType
            connector = cli_context.bootstrap.neuprint_connector
            config = cli_context.config

            # Get neuron type config or create default
            nt_config = config.get_neuron_type_config(neuron_type)
            if not nt_config:
                from .config import NeuronTypeConfig
                nt_config = NeuronTypeConfig(name=neuron_type)

            # Create neuron type object
            neuron_type_obj = NeuronType(neuron_type, nt_config, connector, soma_side)

            if not neuron_type_obj.has_data():
                click.echo(f"No neurons found for {neuron_type}")
                return

            # Get summary data
            summary = neuron_type_obj.summary

            click.echo(f"\n=== {neuron_type} Analysis ===")
            click.echo(f"Total neurons: {summary.total_count}")
            click.echo(f"Left hemisphere: {summary.left_count}")
            click.echo(f"Right hemisphere: {summary.right_count}")
            click.echo(f"Soma side filter: {soma_side}")

            click.echo(f"\nSynapse Statistics:")
            click.echo(f"  Pre-synapses (total): {summary.total_pre_synapses}")
            click.echo(f"  Post-synapses (total): {summary.total_post_synapses}")
            click.echo(f"  Pre-synapses (avg): {summary.avg_pre_synapses:.1f}")
            click.echo(f"  Post-synapses (avg): {summary.avg_post_synapses:.1f}")

            if summary.total_post_synapses > 0:
                ratio = summary.total_pre_synapses / summary.total_post_synapses
                click.echo(f"  Pre/Post ratio: {ratio:.2f}")

            if summary.left_count > 0 and summary.right_count > 0:
                lr_ratio = summary.left_count / summary.right_count
                click.echo(f"  Left/Right ratio: {lr_ratio:.2f}")

        except Exception as e:
            click.echo(f"Error inspecting {neuron_type}: {e}", err=True)
            return

    try:
        asyncio.run(run_inspection())
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if cli_context.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """Entry point for the new CLI."""
    cli()


if __name__ == '__main__':
    main()
