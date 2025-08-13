"""
Simplified CLI for QuickPage with clean architecture.

This CLI preserves all existing commands and options while using a simplified
architecture that maintains the same functionality and output.
"""

import asyncio
import click
import sys
from pathlib import Path
from typing import Optional
import logging

from .services import (
    ServiceContainer,
    GeneratePageCommand,
    ListNeuronTypesCommand,
    InspectNeuronTypeCommand,
    TestConnectionCommand,
    FillQueueCommand,
    PopCommand
)
from .models import NeuronTypeName, SomaSide
from .result import Result


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_services(config_path: Optional[str] = None, verbose: bool = False) -> ServiceContainer:
    """Set up the service container with configuration."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Import config here to avoid circular imports
    from .config import Config

    # Load configuration
    config = Config.load(config_path or "config.yaml")

    return ServiceContainer(config)


@click.group()
@click.option('-c', '--config', help='Configuration file path')
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose output')
@click.pass_context
def main(ctx, config: Optional[str], verbose: bool):
    """QuickPage - Generate HTML pages for neuron types using modern DDD architecture."""
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config
    ctx.obj['verbose'] = verbose


@main.command('generate')
@click.option('--neuron-type', '-n', help='Neuron type to generate page for')
@click.option('--soma-side',
              type=click.Choice(['left', 'right', 'middle', 'both', 'all'], case_sensitive=False),
              default='all',
              help='Soma side filter')
@click.option('--output-dir', help='Output directory')
@click.option('--image-format',
              type=click.Choice(['svg', 'png'], case_sensitive=False),
              default='svg',
              help='Format for hexagon grid images (default: svg)')
@click.option('--embed/--no-embed', default=True,
              help='Embed images directly in HTML instead of saving to files')
@click.option('--min-synapses', type=int, default=0, help='Minimum synapse count')
@click.option('--no-connectivity', is_flag=True, help='Skip connectivity data')
@click.option('--max-concurrent', type=int, default=3, help='Maximum concurrent operations')
@click.pass_context
def generate(ctx, neuron_type: Optional[str], soma_side: str, output_dir: Optional[str],
            image_format: str, embed: bool, min_synapses: int, no_connectivity: bool, max_concurrent: int):
    """Generate HTML pages for neuron types."""
    services = setup_services(ctx.obj['config_path'], ctx.obj['verbose'])

    async def run_generate():
        if neuron_type:
            # Generate for specific neuron type
            command = GeneratePageCommand(
                neuron_type=NeuronTypeName(neuron_type),
                soma_side=SomaSide.from_string(soma_side),
                output_directory=output_dir,
                include_connectivity=not no_connectivity,
                min_synapse_count=min_synapses,
                image_format=image_format.lower(),
                embed_images=embed
            )

            result = await services.page_service.generate_page(command)

            if result.is_ok():
                click.echo(f"✅ Generated page: {result.unwrap()}")
            else:
                click.echo(f"❌ Error: {result.unwrap_err()}", err=True)
                sys.exit(1)
        else:
            # Auto-discover and generate for multiple types
            list_command = ListNeuronTypesCommand(
                max_results=20,
                exclude_empty=True
            )

            list_result = await services.discovery_service.list_neuron_types(list_command)

            if list_result.is_err():
                click.echo(f"❌ Error discovering types: {list_result.unwrap_err()}", err=True)
                sys.exit(1)

            types = list_result.unwrap()
            if not types:
                click.echo("No neuron types found.")
                return

            click.echo(f"Found {len(types)} neuron types. Generating pages...")

            # Generate pages with controlled concurrency
            semaphore = asyncio.Semaphore(max_concurrent)

            async def generate_single(type_info):
                async with semaphore:
                    command = GeneratePageCommand(
                        neuron_type=NeuronTypeName(type_info.name),
                        soma_side=SomaSide.from_string(soma_side),
                        output_directory=output_dir,
                        include_connectivity=not no_connectivity,
                        min_synapse_count=min_synapses,
                        image_format=image_format.lower(),
                        embed_images=embed
                    )

                    result = await services.page_service.generate_page(command)

                    if result.is_ok():
                        click.echo(f"✅ Generated: {type_info.name}")
                    else:
                        click.echo(f"❌ Failed {type_info.name}: {result.unwrap_err()}")

            tasks = [generate_single(type_info) for type_info in types]
            await asyncio.gather(*tasks, return_exceptions=True)

            click.echo(f"🎉 Completed bulk generation for {len(types)} types.")

    asyncio.run(run_generate())


@main.command('list-types')
@click.option('--max-results', type=int, default=10, help='Maximum number of results')
@click.option('--all', 'all_results', is_flag=True, help='Show all results (overrides --max-results)')
@click.option('--sorted', 'sorted_results', is_flag=True, help='Sort results alphabetically')
@click.option('--show-soma-sides', is_flag=True, help='Show soma side distribution')
@click.option('--show-statistics', is_flag=True, help='Show neuron counts and statistics')
@click.option('--filter-pattern', help='Filter types by pattern (regex)')
@click.pass_context
def list_types(ctx, max_results: int, all_results: bool, sorted_results: bool, show_soma_sides: bool,
               show_statistics: bool, filter_pattern: Optional[str]):
    """List available neuron types with metadata."""
    services = setup_services(ctx.obj['config_path'], ctx.obj['verbose'])

    async def run_list():
        # If --all is specified, override max_results
        effective_max_results = 0 if all_results else max_results

        command = ListNeuronTypesCommand(
            max_results=effective_max_results,
            all_results=all_results,
            sorted_results=sorted_results,
            show_soma_sides=show_soma_sides,
            show_statistics=show_statistics,
            filter_pattern=filter_pattern
        )

        result = await services.discovery_service.list_neuron_types(command)

        if result.is_err():
            click.echo(f"❌ Error: {result.unwrap_err()}", err=True)
            sys.exit(1)

        types = result.unwrap()

        if not types:
            click.echo("No neuron types found.")
            return

        # Display header
        if show_statistics and show_soma_sides:
            click.echo(f"{'Type':<20} {'Count':<8} {'Left':<6} {'Right':<6} {'Middle':<6} {'Avg Syn':<8}")
            click.echo("-" * 66)
        elif show_statistics:
            click.echo(f"{'Type':<30} {'Count':<8} {'Avg Synapses':<12}")
            click.echo("-" * 52)
        elif show_soma_sides:
            click.echo(f"{'Type':<25} {'Left':<6} {'Right':<6} {'Middle':<6}")
            click.echo("-" * 45)
        else:
            click.echo("Available neuron types:")
            click.echo("-" * 25)

        # Display results
        for type_info in types:
            if show_statistics and show_soma_sides:
                left = type_info.soma_sides.get('left', 0)
                right = type_info.soma_sides.get('right', 0)
                middle = type_info.soma_sides.get('middle', 0)
                click.echo(f"{type_info.name:<20} {type_info.count:<8} {left:<6} {right:<6} {middle:<6} {type_info.avg_synapses:<8.1f}")
            elif show_statistics:
                click.echo(f"{type_info.name:<30} {type_info.count:<8} {type_info.avg_synapses:<12.1f}")
            elif show_soma_sides:
                left = type_info.soma_sides.get('left', 0)
                right = type_info.soma_sides.get('right', 0)
                middle = type_info.soma_sides.get('middle', 0)
                click.echo(f"{type_info.name:<25} {left:<6} {right:<6} {middle:<6}")
            else:
                click.echo(f"  {type_info.name}")

        click.echo(f"\nShowing {len(types)} types")

    asyncio.run(run_list())


@main.command('inspect')
@click.argument('neuron_type')
@click.option('--soma-side',
              type=click.Choice(['left', 'right', 'middle', 'both', 'all'], case_sensitive=False),
              default='all',
              help='Soma side filter')
@click.option('--min-synapses', type=int, default=0, help='Minimum synapse count')
@click.pass_context
def inspect(ctx, neuron_type: str, soma_side: str, min_synapses: int):
    """Inspect detailed information about a specific neuron type."""
    services = setup_services(ctx.obj['config_path'], ctx.obj['verbose'])

    async def run_inspect():
        command = InspectNeuronTypeCommand(
            neuron_type=NeuronTypeName(neuron_type),
            soma_side=SomaSide.from_string(soma_side),
            min_synapse_count=min_synapses,
            include_connectivity=True
        )

        result = await services.discovery_service.inspect_neuron_type(command)

        if result.is_err():
            click.echo(f"❌ Error: {result.unwrap_err()}", err=True)
            sys.exit(1)

        stats = result.unwrap()

        # Display detailed information
        click.echo(f"\n📊 {stats.type_name} Statistics")
        click.echo("=" * 50)

        click.echo(f"\n🧠 Neuron Counts:")
        click.echo(f"  Total:       {stats.total_count}")
        click.echo(f"  Left:        {stats.soma_side_counts.get('left', 0)}")
        click.echo(f"  Right:       {stats.soma_side_counts.get('right', 0)}")
        click.echo(f"  Middle:      {stats.soma_side_counts.get('middle', 0)}")

        if stats.total_count > 0:
            bilateral_ratio = stats.bilateral_ratio
            click.echo(f"  Bilateral ratio: {bilateral_ratio:.2f}")

        if stats.synapse_stats:
            click.echo(f"\n⚡ Synapse Statistics:")
            click.echo(f"  Avg Pre:     {stats.synapse_stats.get('avg_pre', 0):.1f}")
            click.echo(f"  Avg Post:    {stats.synapse_stats.get('avg_post', 0):.1f}")
            click.echo(f"  Avg Total:   {stats.synapse_stats.get('avg_total', 0):.1f}")
            click.echo(f"  Median:      {stats.synapse_stats.get('median_total', 0):.1f}")
            click.echo(f"  Std Dev:     {stats.synapse_stats.get('std_dev_total', 0):.1f}")

        click.echo(f"\n⏰ Computed: {stats.computed_at.strftime('%Y-%m-%d %H:%M:%S')}")

    asyncio.run(run_inspect())


@main.command('test-connection')
@click.option('--detailed', is_flag=True, help='Show detailed dataset information')
@click.option('--timeout', type=int, default=30, help='Connection timeout in seconds')
@click.pass_context
def test_connection(ctx, detailed: bool, timeout: int):
    """Test connection to the NeuPrint server."""
    services = setup_services(ctx.obj['config_path'], ctx.obj['verbose'])

    async def run_test():
        command = TestConnectionCommand(
            detailed=detailed,
            timeout=timeout
        )

        result = await services.connection_service.test_connection(command)

        if result.is_err():
            click.echo(f"❌ Connection failed: {result.unwrap_err()}", err=True)
            sys.exit(1)

        dataset_info = result.unwrap()

        click.echo("✅ Connection successful!")

        if detailed:
            click.echo(f"\n📡 Server Information:")
            click.echo(f"  Server:     {dataset_info.server_url}")
            click.echo(f"  Dataset:    {dataset_info.name}")
            click.echo(f"  Version:    {dataset_info.version}")
            click.echo(f"  Status:     {dataset_info.connection_status}")
        else:
            click.echo(f"Connected to {dataset_info.name} at {dataset_info.server_url}")

    asyncio.run(run_test())


@main.command('fill-queue')
@click.option('--neuron-type', '-n', help='Neuron type to generate queue entry for')
@click.option('--all', 'all_types', is_flag=True, help='Create queue files for all neuron types')
@click.option('--soma-side',
              type=click.Choice(['left', 'right', 'middle', 'both', 'all'], case_sensitive=False),
              default='all',
              help='Soma side filter')
@click.option('--output-dir', help='Output directory')
@click.option('--image-format',
              type=click.Choice(['svg', 'png'], case_sensitive=False),
              default='svg',
              help='Format for hexagon grid images (default: svg)')
@click.option('--embed/--no-embed', default=True,
              help='Embed images directly in HTML instead of saving to files')
@click.option('--min-synapses', type=int, default=0, help='Minimum synapse count')
@click.option('--no-connectivity', is_flag=True, help='Skip connectivity data')
@click.option('--max-concurrent', type=int, default=3, help='Maximum concurrent operations')
@click.pass_context
def fill_queue(ctx, neuron_type: Optional[str], all_types: bool, soma_side: str, output_dir: Optional[str],
              image_format: str, embed: bool, min_synapses: int, no_connectivity: bool, max_concurrent: int):
    """Create YAML queue files with generate command options."""
    services = setup_services(ctx.obj['config_path'], ctx.obj['verbose'])

    async def run_fill_queue():
        # Create the command with the appropriate parameters
        command = FillQueueCommand(
            neuron_type=NeuronTypeName(neuron_type) if neuron_type else None,
            soma_side=SomaSide.from_string(soma_side),
            output_directory=output_dir,
            include_connectivity=not no_connectivity,
            min_synapse_count=min_synapses,
            image_format=image_format.lower(),
            embed_images=embed,
            all_types=all_types,
            max_types=10  # Default limit when not using --all
        )

        result = await services.queue_service.fill_queue(command)

        if result.is_ok():
            if neuron_type:
                click.echo(f"✅ Created queue file: {result.unwrap()}")
            else:
                click.echo(f"✅ {result.unwrap()}")
        else:
            click.echo(f"❌ Error: {result.unwrap_err()}", err=True)
            sys.exit(1)

    asyncio.run(run_fill_queue())


@main.command('pop')
@click.option('--output-dir', help='Output directory')
@click.pass_context
def pop(ctx, output_dir: Optional[str]):
    """Pop and process a queue file."""
    services = setup_services(ctx.obj['config_path'], ctx.obj['verbose'])

    async def run_pop():
        command = PopCommand(
            output_directory=output_dir
        )

        result = await services.queue_service.pop_queue(command)

        if result.is_ok():
            click.echo(f"✅ {result.unwrap()}")
        else:
            click.echo(f"❌ Error: {result.unwrap_err()}", err=True)
            sys.exit(1)

    asyncio.run(run_pop())


if __name__ == '__main__':
    main()
