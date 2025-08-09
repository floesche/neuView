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
from .infrastructure.repositories import (
    NeuPrintNeuronRepository, NeuPrintConnectivityRepository
)
from .infrastructure.adapters import (
    Jinja2TemplateEngine, LocalFileStorage, MemoryCacheRepository
)
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
        self.container = Container()
        self._setup_dependencies()

    def _setup_dependencies(self):
        """Set up all application dependencies."""
        # Infrastructure repositories
        neuron_repo = NeuPrintNeuronRepository(self.config)
        connectivity_repo = NeuPrintConnectivityRepository(self.config)
        cache_repo = MemoryCacheRepository()

        # Infrastructure adapters
        template_engine = Jinja2TemplateEngine(self.config.output.template_dir)
        file_storage = LocalFileStorage()

        # Register infrastructure
        self.container.register_singleton(NeuPrintNeuronRepository, neuron_repo)
        self.container.register_singleton(NeuPrintConnectivityRepository, connectivity_repo)
        self.container.register_singleton(MemoryCacheRepository, cache_repo)
        self.container.register_singleton(Jinja2TemplateEngine, template_engine)
        self.container.register_singleton(LocalFileStorage, file_storage)

        # Register application services
        self.container.register_factory(
            PageGenerationService,
            lambda: PageGenerationService(
                neuron_repo=self.container.resolve(NeuPrintNeuronRepository),
                connectivity_repo=self.container.resolve(NeuPrintConnectivityRepository),
                template_engine=self.container.resolve(Jinja2TemplateEngine),
                file_storage=self.container.resolve(LocalFileStorage),
                cache_repo=self.container.resolve(MemoryCacheRepository)
            )
        )

        self.container.register_factory(
            NeuronDiscoveryService,
            lambda: NeuronDiscoveryService(
                neuron_repo=self.container.resolve(NeuPrintNeuronRepository),
                cache_repo=self.container.resolve(MemoryCacheRepository)
            )
        )

        self.container.register_factory(
            ConnectionTestService,
            lambda: ConnectionTestService(
                neuron_repo=self.container.resolve(NeuPrintNeuronRepository)
            )
        )

    def get_service(self, service_type):
        """Get a service from the container."""
        return self.container.resolve(service_type)


class CLIContext:
    """Context object to hold shared CLI state."""

    def __init__(self, config: Config, verbose: bool = False):
        self.config = config
        self.verbose = verbose
        self.bootstrap = ApplicationBootstrap(config)

        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Verbose mode enabled")

    def get_page_service(self) -> PageGenerationService:
        return self.bootstrap.get_service(PageGenerationService)

    def get_discovery_service(self) -> NeuronDiscoveryService:
        return self.bootstrap.get_service(NeuronDiscoveryService)

    def get_connection_service(self) -> ConnectionTestService:
        return self.bootstrap.get_service(ConnectionTestService)


def handle_result(result: Result, success_msg: str = None, error_prefix: str = "Error"):
    """Handle a Result, printing success or error and exiting on failure."""
    if result.is_ok():
        if success_msg:
            click.echo(success_msg)
        return result.value
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
            output_path = handle_result(result, f"✓ Generated: {result.value if result.is_ok() else ''}")

            click.echo(f"Page saved to: {output_path}")

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

        query = ListNeuronTypesQuery(
            include_soma_sides=show_soma_sides,
            include_statistics=show_statistics,
            filter_pattern=filter_pattern,
            max_results=max_results,
            sort_by="name" if sorted else "random"
        )

        if cli_context.verbose:
            click.echo("Querying available neuron types...")

        result = await service.list_neuron_types(query)
        query_result = handle_result(result, "Query completed")

        # Display results
        selection_method = "alphabetically ordered" if sorted else "randomly selected"
        click.echo(f"\nFound {len(query_result.neuron_types)} neuron types "
                   f"({selection_method}, total available: {query_result.total_available}):")

        if filter_pattern:
            click.echo(f"Filtered by pattern: {filter_pattern}")

        for i, neuron_info in enumerate(query_result.neuron_types, 1):
            type_display = f"  {i:2d}. {neuron_info.name}"

            if show_soma_sides and neuron_info.available_soma_sides:
                sides_str = ', '.join(neuron_info.available_soma_sides)
                type_display += f" (sides: {sides_str})"

            if show_statistics and neuron_info.statistics:
                stats = neuron_info.statistics
                type_display += f" (neurons: {stats.total_count})"

            click.echo(type_display)

        if show_statistics:
            total_neurons = sum(
                info.statistics.total_count if info.statistics else 0
                for info in query_result.neuron_types
            )
            click.echo(f"\nSummary: {total_neurons} total neurons across displayed types")

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

        query = GetNeuronTypeQuery(
            neuron_type=NeuronTypeName(neuron_type),
            soma_side=SomaSide(soma_side),
            min_synapse_count=min_synapses,
            include_roi_data=True
        )

        if cli_context.verbose:
            click.echo(f"Inspecting {neuron_type}...")

        result = await service.get_neuron_type_details(query)
        details = handle_result(result, "Inspection completed")

        # Display detailed information
        stats = details.statistics
        collection = details.neuron_collection

        click.echo(f"\n=== {neuron_type} Analysis ===")
        click.echo(f"Total neurons: {stats.total_count}")
        click.echo(f"Left hemisphere: {stats.left_count}")
        click.echo(f"Right hemisphere: {stats.right_count}")
        click.echo(f"Middle: {stats.middle_count}")

        click.echo(f"\nSynapse Statistics:")
        click.echo(f"  Pre-synapses (total): {stats.total_pre_synapses}")
        click.echo(f"  Post-synapses (total): {stats.total_post_synapses}")
        click.echo(f"  Pre-synapses (avg): {stats.avg_pre_synapses:.1f}")
        click.echo(f"  Post-synapses (avg): {stats.avg_post_synapses:.1f}")
        click.echo(f"  Pre/Post ratio: {stats.pre_post_ratio():.2f}")

        if stats.is_bilateral():
            click.echo(f"  Left/Right ratio: {stats.left_right_ratio():.2f}")

        # Show ROI information
        unique_rois = collection.get_unique_rois()
        if unique_rois:
            click.echo(f"\nFound in {len(unique_rois)} ROIs:")
            for roi in unique_rois[:10]:  # Show first 10
                click.echo(f"  • {roi}")
            if len(unique_rois) > 10:
                click.echo(f"  ... and {len(unique_rois) - 10} more")

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
