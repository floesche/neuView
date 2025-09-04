"""
Simplified CLI for QuickPage with clean architecture.

This CLI preserves all existing commands and options while using a simplified
architecture that maintains the same functionality and output.
"""

import asyncio
import click
import sys
from typing import Optional
import logging

from .commands import (
    GeneratePageCommand,
    TestConnectionCommand,
    FillQueueCommand,
    PopCommand,
    CreateListCommand
)
from .services import ServiceContainer
from .services.neuron_discovery_service import (
    InspectNeuronTypeCommand
)
from .models import NeuronTypeName, SomaSide


# Configure logging
logging.basicConfig(
    level=logging.WARNING,
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
              type=click.Choice(['left', 'right', 'middle', 'combined', 'all'], case_sensitive=False),
              default='all',
              help='Soma side filter')
@click.option('--output-dir', help='Output directory')
@click.option('--image-format',
              type=click.Choice(['svg', 'png'], case_sensitive=False),
              default='svg',
              help='Format for hexagon grid images (default: svg)')
@click.option('--embed/--no-embed', default=False,
              help='Embed images directly in HTML instead of saving to files')
@click.option('--minify/--no-minify', default=True, help='Enable/disable HTML minification (default: enabled)')

@click.pass_context
def generate(ctx, neuron_type: Optional[str], soma_side: str, output_dir: Optional[str],
             image_format: str, embed: bool, minify: bool):
    """Generate HTML pages for neuron types."""
    services = setup_services(ctx.obj['config_path'], ctx.obj['verbose'])

    async def run_generate():
        if neuron_type:
            # Generate for specific neuron type
            command = GeneratePageCommand(
                neuron_type=NeuronTypeName(neuron_type),
                soma_side=SomaSide.from_string(soma_side),
                output_directory=output_dir,
                image_format=image_format.lower(),
                embed_images=embed,
                minify=minify,

            )

            result = await services.page_service.generate_page(command)

            if result.is_ok():
                click.echo(f"✅ Generated page: {result.unwrap()}")
            else:
                click.echo(f"❌ Error: {result.unwrap_err()}", err=True)
                sys.exit(1)
        else:
            # Auto-discover and generate for multiple types
            try:
                # Use connector directly to discover neuron types
                discovered_types = services.neuprint_connector.discover_neuron_types(services.config.discovery)
                type_names = list(discovered_types)[:20]  # Limit to 20 types

                if not type_names:
                    click.echo("No neuron types found.")
                    return
            except Exception as e:
                click.echo(f"❌ Error discovering types: {str(e)}", err=True)
                sys.exit(1)
            click.echo(f"Found {len(type_names)} neuron types. Generating pages...")

            # Generate pages with controlled concurrency
            max_concurrent = 3  # Default concurrency limit
            semaphore = asyncio.Semaphore(max_concurrent)

            async def generate_single(type_name):
                async with semaphore:
                    command = GeneratePageCommand(
                        neuron_type=NeuronTypeName(type_name),
                        soma_side=SomaSide.from_string(soma_side),
                        output_directory=output_dir,
                        image_format=image_format.lower(),
                        embed_images=embed,
                        minify=minify,

                    )

                    result = await services.page_service.generate_page(command)

                    if result.is_ok():
                        click.echo(f"✅ Generated: {type_name}")
                    else:
                        click.echo(f"❌ Failed {type_name}: {result.unwrap_err()}")

            tasks = [generate_single(type_name) for type_name in type_names]
            await asyncio.gather(*tasks, return_exceptions=True)

            click.echo(f"🎉 Completed bulk generation for {len(type_names)} types.")

    asyncio.run(run_generate())





@main.command('inspect')
@click.argument('neuron_type')
@click.option('--soma-side',
              type=click.Choice(['left', 'right', 'middle', 'combined', 'all'], case_sensitive=False),
              default='all',
              help='Soma side filter')
@click.pass_context
def inspect(ctx, neuron_type: str, soma_side: str):
    """Inspect detailed information about a specific neuron type."""
    services = setup_services(ctx.obj['config_path'], ctx.obj['verbose'])

    async def run_inspect():
        command = InspectNeuronTypeCommand(
            neuron_type=NeuronTypeName(neuron_type),
            soma_side=SomaSide.from_string(soma_side)
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
@click.option('--all', 'all_types', is_flag=True, help='Create queue files for all neuron types and update cache manifest')
@click.option('--soma-side',
              type=click.Choice(['left', 'right', 'middle', 'combined', 'all'], case_sensitive=False),
              default='all',
              help='Soma side filter')
@click.option('--output-dir', help='Output directory')
@click.option('--image-format',
              type=click.Choice(['svg', 'png'], case_sensitive=False),
              default='svg',
              help='Format for hexagon grid images (default: svg)')
@click.option('--embed/--no-embed', default=False,
              help='Embed images directly in HTML instead of saving to files')
@click.pass_context
def fill_queue(ctx, neuron_type: Optional[str], all_types: bool, soma_side: str, output_dir: Optional[str],
              image_format: str, embed: bool):
    """Create YAML queue files with generate command options and update JSON cache manifest."""
    services = setup_services(ctx.obj['config_path'], ctx.obj['verbose'])

    async def run_fill_queue():
        # Create the command with the appropriate parameters
        command = FillQueueCommand(
            neuron_type=NeuronTypeName(neuron_type) if neuron_type else None,
            soma_side=SomaSide.from_string(soma_side),
            output_directory=output_dir,
            image_format=image_format.lower(),
            embed_images=embed,
            all_types=all_types,
            max_types=10,  # Default limit when not using --all
            config_file=ctx.obj['config_path']
        )

        result = await services.queue_service.fill_queue(command)

        if result.is_ok():
            if neuron_type:
                click.echo(f"✅ Created queue file and updated JSON cache manifest: {result.unwrap()}")
            else:
                click.echo(f"✅ {result.unwrap()}")
        else:
            click.echo(f"❌ Error: {result.unwrap_err()}", err=True)
            sys.exit(1)

    asyncio.run(run_fill_queue())


@main.command('pop')
@click.option('--output-dir', help='Output directory')
@click.option('--minify/--no-minify', default=True, help='Enable/disable HTML minification (default: enabled)')
@click.pass_context
def pop(ctx, output_dir: Optional[str], minify: bool):
    """Pop and process a queue file."""
    services = setup_services(ctx.obj['config_path'], ctx.obj['verbose'])

    async def run_pop():
        command = PopCommand(
            output_directory=output_dir,
            minify=minify
        )

        result = await services.queue_service.pop_queue(command)

        if result.is_ok():
            click.echo(f"✅ {result.unwrap()}")
        else:
            click.echo(f"❌ Error: {result.unwrap_err()}", err=True)
            sys.exit(1)

    asyncio.run(run_pop())


@main.command('create-list')
@click.option('--output-dir', help='Output directory to scan for neuron pages')
@click.option('--minify/--no-minify', default=True, help='Enable/disable HTML minification (default: enabled)')
@click.pass_context
def create_list(ctx, output_dir: Optional[str], minify: bool):
    """Generate an index page listing all available neuron types.

    Includes ROI analysis for comprehensive neuron information.
    """
    services = setup_services(ctx.obj['config_path'], ctx.obj['verbose'])

    async def run_create_list():
        command = CreateListCommand(
            output_directory=output_dir,
            include_roi_analysis=True,
            minify=minify
        )

        result = await services.index_service.create_index(command)

        if result.is_ok():
            click.echo(f"✅ Created index page: {result.unwrap()}")
        else:
            click.echo(f"❌ Error: {result.unwrap_err()}", err=True)
            sys.exit(1)

    asyncio.run(run_create_list())


@main.command('cache')
@click.option('--action',
              type=click.Choice(['stats', 'list', 'clean', 'clear'], case_sensitive=False),
              default='stats',
              help='Cache action to perform')
@click.option('--neuron-type', '-n', help='Specific neuron type for cache operations')
@click.pass_context
def cache(ctx, action: str, neuron_type: Optional[str]):
    """Manage persistent cache for neuron type data."""
    services = setup_services(ctx.obj['config_path'], ctx.obj['verbose'])

    async def run_cache(action, neuron_type):
        from .cache import create_cache_manager

        # Get cache manager
        output_dir = services.config.output.directory
        cache_manager = create_cache_manager(output_dir)

        if action == 'stats':
            # Show cache statistics
            stats = cache_manager.get_cache_stats()
            click.echo("📊 Cache Statistics:")
            click.echo(f"  Cache directory: {stats['cache_dir']}")

            if 'error' in stats:
                click.echo(f"  ❌ Error: {stats['error']}")
                return

            click.echo(f"  Total files: {stats['total_files']}")
            click.echo(f"  Valid files: {stats['valid_files']}")
            click.echo(f"  Expired files: {stats['expired_files']}")
            click.echo(f"  Corrupted files: {stats['corrupted_files']}")
            click.echo(f"  Total size: {stats['total_size_mb']} MB")

            # Show column cache statistics
            import json
            from pathlib import Path
            import time

            # Column data is now integrated into neuron cache files
            click.echo(f"\nℹ️  Column Data: Now integrated into individual neuron cache files")

        elif action == 'list':
            # List cached neuron types
            cached_types = cache_manager.list_cached_neuron_types()
            if cached_types:
                click.echo(f"📋 Cached neuron types ({len(cached_types)}):")
                for neuron_type in cached_types:
                    click.echo(f"  • {neuron_type}")
            else:
                click.echo("📋 No cached neuron types found")

        elif action == 'clean':
            # Clean expired cache files
            removed_count = cache_manager.cleanup_expired_cache()

            if removed_count > 0:
                message = f"🧹 Cleaned up {removed_count} expired cache files"
                click.echo(message)
            else:
                click.echo("🧹 No expired cache files to clean")

        elif action == 'clear':
            # Clear specific neuron type or all cache
            if neuron_type:
                success = cache_manager.invalidate_neuron_type_cache(neuron_type)
                if success:
                    click.echo(f"🗑️  Cleared cache for {neuron_type}")
                else:
                    click.echo(f"❌ No cache found for {neuron_type}")
            else:
                # Confirm clearing all cache
                if click.confirm("Are you sure you want to clear ALL cache files?"):
                    import shutil
                    from pathlib import Path
                    cache_dir = Path(cache_manager.cache_dir)
                    column_cache_count = 0

                    if cache_dir.exists():
                        shutil.rmtree(cache_dir)
                        cache_dir.mkdir(parents=True, exist_ok=True)
                        click.echo("🗑️  Cleared all cache files")

                        # Also clear global cache
                        services.neuprint_connector.clear_global_cache()
                        click.echo("🗑️  Cleared global ROI hierarchy and meta query cache")
                    else:
                        click.echo("📁 Cache directory doesn't exist")

    asyncio.run(run_cache(action, neuron_type))


if __name__ == '__main__':
    main()
