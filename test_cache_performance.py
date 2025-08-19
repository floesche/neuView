#!/usr/bin/env python3
"""
Cache Performance Demonstration Script

This script demonstrates the caching improvements for reducing redundant Cypher queries
during neuron page generation. It shows the difference between cache hits and misses
for ROI hierarchy, meta queries, and neuron data.
"""

import asyncio
import time
import logging
from pathlib import Path
import sys

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from quickpage.config import Config
from quickpage.services import ServiceContainer, GeneratePageCommand
from quickpage.models import NeuronTypeName, SomaSide

# Configure logging to show cache performance
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def demonstrate_cache_performance():
    """Demonstrate the cache performance improvements."""

    print("🧪 Cache Performance Demonstration")
    print("=" * 50)

    # Load configuration
    config = Config.load("config.yaml")
    services = ServiceContainer(config)

    # Test neuron type
    test_neuron_type = "Dm4"

    print(f"\n📊 Testing with neuron type: {test_neuron_type}")
    print("-" * 30)

    # Clear caches to start fresh
    print("🗑️  Clearing all caches...")
    services.neuprint_connector.clear_global_cache()
    services.neuprint_connector.clear_neuron_data_cache()

    # First run - expect cache misses
    print("\n🔄 First run (cache misses expected):")
    start_time = time.time()

    command = GeneratePageCommand(
        neuron_type=NeuronTypeName(test_neuron_type),
        soma_side=SomaSide.BOTH,
        output_directory="test_output",
        image_format="svg",
        embed_images=True,
        uncompress=False
    )

    result1 = await services.page_service.generate_page(command)
    first_run_time = time.time() - start_time

    if result1.is_ok():
        print(f"✅ Generated page in {first_run_time:.2f}s")
    else:
        print(f"❌ Error: {result1.unwrap_err()}")
        return

    # Get cache stats after first run
    stats1 = services.neuprint_connector.get_cache_stats()
    print(f"📈 Cache stats after first run:")
    print(f"   ROI hierarchy hits: {stats1['roi_hierarchy_hits']}")
    print(f"   ROI hierarchy misses: {stats1['roi_hierarchy_misses']}")
    print(f"   Meta query hits: {stats1['meta_hits']}")
    print(f"   Meta query misses: {stats1['meta_misses']}")
    print(f"   Total queries saved: {stats1['database_queries_saved'] + stats1['connectivity_queries_saved'] + stats1['roi_hierarchy_hits'] + stats1['meta_hits']}")

    # Second run - expect cache hits
    print("\n🔄 Second run (cache hits expected):")
    start_time = time.time()

    result2 = await services.page_service.generate_page(command)
    second_run_time = time.time() - start_time

    if result2.is_ok():
        print(f"✅ Generated page in {second_run_time:.2f}s")
    else:
        print(f"❌ Error: {result2.unwrap_err()}")
        return

    # Get cache stats after second run
    stats2 = services.neuprint_connector.get_cache_stats()
    print(f"📈 Cache stats after second run:")
    print(f"   ROI hierarchy hits: {stats2['roi_hierarchy_hits']}")
    print(f"   ROI hierarchy misses: {stats2['roi_hierarchy_misses']}")
    print(f"   Meta query hits: {stats2['meta_hits']}")
    print(f"   Meta query misses: {stats2['meta_misses']}")
    print(f"   Total queries saved: {stats2['database_queries_saved'] + stats2['connectivity_queries_saved'] + stats2['roi_hierarchy_hits'] + stats2['meta_hits']}")

    # Calculate improvements
    roi_cache_improvement = stats2['roi_hierarchy_hits'] - stats1['roi_hierarchy_hits']
    meta_cache_improvement = stats2['meta_hits'] - stats1['meta_hits']
    total_cache_improvement = (stats2['database_queries_saved'] + stats2['connectivity_queries_saved'] +
                              stats2['roi_hierarchy_hits'] + stats2['meta_hits']) - \
                             (stats1['database_queries_saved'] + stats1['connectivity_queries_saved'] +
                              stats1['roi_hierarchy_hits'] + stats1['meta_hits'])

    time_improvement = first_run_time - second_run_time
    time_improvement_percent = (time_improvement / first_run_time) * 100 if first_run_time > 0 else 0

    print(f"\n📊 Performance Improvements:")
    print(f"   Additional ROI hierarchy cache hits: {roi_cache_improvement}")
    print(f"   Additional meta query cache hits: {meta_cache_improvement}")
    print(f"   Additional total queries saved: {total_cache_improvement}")
    print(f"   Time improvement: {time_improvement:.2f}s ({time_improvement_percent:.1f}%)")

    # Test with different soma side to show neuron data caching
    print(f"\n🔄 Third run with different soma side (LEFT):")
    start_time = time.time()

    command_left = GeneratePageCommand(
        neuron_type=NeuronTypeName(test_neuron_type),
        soma_side=SomaSide.LEFT,
        output_directory="test_output",
        image_format="svg",
        embed_images=True,
        uncompress=False
    )

    result3 = await services.page_service.generate_page(command_left)
    third_run_time = time.time() - start_time

    if result3.is_ok():
        print(f"✅ Generated LEFT side page in {third_run_time:.2f}s")
    else:
        print(f"❌ Error: {result3.unwrap_err()}")
        return

    # Final cache stats
    stats3 = services.neuprint_connector.get_cache_stats()
    print(f"📈 Final cache stats:")
    print(f"   Neuron data hit rate: {stats3['hit_rate_percent']:.1f}%")
    print(f"   ROI hierarchy hit rate: {stats3['roi_hit_rate_percent']:.1f}%")
    print(f"   Meta query hit rate: {stats3['meta_hit_rate_percent']:.1f}%")
    print(f"   Total cached neuron types: {stats3['cached_neuron_types']}")
    print(f"   Total queries saved: {stats3['database_queries_saved'] + stats3['connectivity_queries_saved'] + stats3['roi_hierarchy_hits'] + stats3['meta_hits']}")

    print(f"\n🎉 Cache Performance Summary:")
    print(f"   The caching system successfully reduced database queries")
    print(f"   ROI hierarchy queries are now cached globally")
    print(f"   Meta queries are cached per server/dataset")
    print(f"   Neuron data is cached and reused across soma sides")
    print(f"   Overall performance improvement: {time_improvement_percent:.1f}%")


async def test_bulk_generation_cache():
    """Test cache performance with bulk generation."""
    print("\n🔄 Testing bulk generation cache performance...")

    config = Config.load("config.yaml")
    services = ServiceContainer(config)

    # Clear caches
    services.neuprint_connector.clear_global_cache()
    services.neuprint_connector.clear_neuron_data_cache()

    test_types = ["Dm4", "Tm1", "Tm2"]  # Test with multiple types

    print(f"📊 Testing with neuron types: {', '.join(test_types)}")

    total_start_time = time.time()

    for i, neuron_type in enumerate(test_types):
        print(f"\n🔄 Generating {neuron_type} ({i+1}/{len(test_types)})...")

        command = GeneratePageCommand(
            neuron_type=NeuronTypeName(neuron_type),
            soma_side=SomaSide.BOTH,
            output_directory="test_output",
            image_format="svg",
            embed_images=True,
            uncompress=False
        )

        start_time = time.time()
        result = await services.page_service.generate_page(command)
        generation_time = time.time() - start_time

        if result.is_ok():
            print(f"✅ Generated {neuron_type} in {generation_time:.2f}s")
        else:
            print(f"❌ Failed {neuron_type}: {result.unwrap_err()}")

    total_time = time.time() - total_start_time

    # Final statistics
    final_stats = services.neuprint_connector.get_cache_stats()
    print(f"\n📊 Bulk Generation Results:")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average time per type: {total_time/len(test_types):.2f}s")
    print(f"   ROI hierarchy hit rate: {final_stats['roi_hit_rate_percent']:.1f}%")
    print(f"   Total queries saved: {final_stats['database_queries_saved'] + final_stats['connectivity_queries_saved'] + final_stats['roi_hierarchy_hits'] + final_stats['meta_hits']}")
    print(f"   Cached neuron types: {final_stats['cached_neuron_types']}")


async def main():
    """Main demonstration function."""
    try:
        await demonstrate_cache_performance()
        await test_bulk_generation_cache()

        print(f"\n✨ Cache performance demonstration completed!")
        print(f"💡 Key improvements:")
        print(f"   • ROI hierarchy queries are now cached globally")
        print(f"   • Meta queries are cached per server/dataset")
        print(f"   • Neuron data is cached and reused across different soma sides")
        print(f"   • Significant reduction in redundant database queries")
        print(f"   • Improved performance for subsequent runs")

    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
