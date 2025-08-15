#!/usr/bin/env python3
"""
Test script to verify batch query optimization implementation.
Compares performance of individual vs batch queries.
"""

import asyncio
import time
import sys
import logging
from pathlib import Path
from typing import List, Dict

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from quickpage.config import Config
from quickpage.services import ServiceContainer, CreateIndexCommand


class BatchOptimizationTester:
    """Test batch query optimization against original implementation."""

    def __init__(self, config_path: str = "config.cns.yaml"):
        self.config = Config.load(config_path)
        self.services = ServiceContainer(self.config)

    async def test_batch_vs_individual_queries(self, test_types: List[str]) -> Dict:
        """Test batch queries vs individual queries for neuron data."""
        print(f"Testing batch optimization with {len(test_types)} neuron types...")

        # Initialize connector
        from quickpage.neuprint_connector import NeuPrintConnector
        connector = NeuPrintConnector(self.config)

        results = {}

        # Test 1: Individual queries (original method)
        print("\n1. Testing individual queries (original)...")
        individual_start = time.time()
        individual_results = {}

        for neuron_type in test_types:
            try:
                data = connector.get_neuron_data(neuron_type, soma_side='both')
                individual_results[neuron_type] = data
            except Exception as e:
                print(f"   Error fetching {neuron_type}: {e}")

        individual_time = time.time() - individual_start
        results['individual'] = {
            'time': individual_time,
            'count': len(individual_results),
            'rate': len(individual_results) / individual_time if individual_time > 0 else 0
        }

        # Test 2: Batch queries (optimized method)
        print("\n2. Testing batch queries (optimized)...")
        batch_start = time.time()

        try:
            batch_results = connector.get_batch_neuron_data(test_types, soma_side='both')
        except Exception as e:
            print(f"   Batch query error: {e}")
            batch_results = {}

        batch_time = time.time() - batch_start
        results['batch'] = {
            'time': batch_time,
            'count': len(batch_results),
            'rate': len(batch_results) / batch_time if batch_time > 0 else 0
        }

        # Calculate improvement
        if individual_time > 0 and batch_time > 0:
            speedup = individual_time / batch_time
            time_saved = individual_time - batch_time
            results['improvement'] = {
                'speedup': speedup,
                'time_saved': time_saved,
                'percentage': ((individual_time - batch_time) / individual_time) * 100
            }

        # Verify data consistency
        consistency_results = self._verify_data_consistency(individual_results, batch_results)
        results['consistency'] = consistency_results

        return results

    def _verify_data_consistency(self, individual_results: Dict, batch_results: Dict) -> Dict:
        """Verify that batch results match individual results."""
        consistency = {
            'total_types': len(individual_results),
            'batch_types': len(batch_results),
            'missing_in_batch': [],
            'data_mismatches': [],
            'consistent': True
        }

        for neuron_type in individual_results:
            if neuron_type not in batch_results:
                consistency['missing_in_batch'].append(neuron_type)
                consistency['consistent'] = False
                continue

            # Compare basic metrics
            individual_data = individual_results[neuron_type]
            batch_data = batch_results[neuron_type]

            individual_count = len(individual_data.get('neurons', []))
            batch_count = len(batch_data.get('neurons', []))

            if individual_count != batch_count:
                consistency['data_mismatches'].append({
                    'type': neuron_type,
                    'individual_count': individual_count,
                    'batch_count': batch_count
                })
                consistency['consistent'] = False

        return consistency

    async def test_index_creation_performance(self, output_dir: str = "test_batch_output") -> Dict:
        """Test full index creation with batch optimization."""
        print(f"\nTesting full index creation performance...")

        # Ensure output directory exists and has test files
        test_output_path = Path(output_dir)
        test_output_path.mkdir(exist_ok=True)

        # Copy some test files
        source_output = Path("output")
        if source_output.exists():
            import shutil
            test_files = list(source_output.glob("*.html"))[:50]  # Test with 50 files

            for file in test_files:
                shutil.copy2(file, test_output_path)

            print(f"   Copied {len(test_files)} test files")

        # Test with ROI analysis
        command = CreateIndexCommand(
            output_directory=str(test_output_path),
            index_filename="index_batch_test.html",
            include_roi_analysis=True
        )

        start_time = time.time()
        result = await self.services.index_service.create_index(command)
        total_time = time.time() - start_time

        success = result.is_ok()

        return {
            'success': success,
            'time': total_time,
            'output': result.unwrap() if success else result.unwrap_err(),
            'test_files': len(test_files) if 'test_files' in locals() else 0
        }

    def print_results(self, results: Dict):
        """Print formatted test results."""
        print("\n" + "="*60)
        print("📊 BATCH OPTIMIZATION TEST RESULTS")
        print("="*60)

        if 'individual' in results and 'batch' in results:
            individual = results['individual']
            batch = results['batch']

            print(f"\n🔍 Query Performance Comparison:")
            print(f"   Individual queries: {individual['time']:.3f}s ({individual['rate']:.1f} types/sec)")
            print(f"   Batch queries:      {batch['time']:.3f}s ({batch['rate']:.1f} types/sec)")

            if 'improvement' in results:
                imp = results['improvement']
                print(f"\n📈 Performance Improvement:")
                print(f"   Speedup:      {imp['speedup']:.1f}x faster")
                print(f"   Time saved:   {imp['time_saved']:.3f}s")
                print(f"   Improvement:  {imp['percentage']:.1f}%")

        if 'consistency' in results:
            cons = results['consistency']
            print(f"\n✅ Data Consistency Check:")
            print(f"   Status: {'PASS' if cons['consistent'] else 'FAIL'}")
            print(f"   Types processed: {cons['total_types']}")
            print(f"   Batch results: {cons['batch_types']}")

            if cons['missing_in_batch']:
                print(f"   Missing in batch: {len(cons['missing_in_batch'])}")

            if cons['data_mismatches']:
                print(f"   Data mismatches: {len(cons['data_mismatches'])}")

        if 'index_test' in results:
            index = results['index_test']
            print(f"\n🏗️  Index Creation Test:")
            print(f"   Status: {'SUCCESS' if index['success'] else 'FAILED'}")
            print(f"   Time: {index['time']:.3f}s")
            print(f"   Test files: {index.get('test_files', 0)}")

    async def run_comprehensive_test(self):
        """Run comprehensive batch optimization test."""
        print("🚀 Starting Batch Optimization Test Suite")
        print("="*50)

        # Check prerequisites
        if not Path("config.cns.yaml").exists():
            print("❌ config.cns.yaml not found")
            return

        # Test with a small set of neuron types
        test_types = [
            "LC10a", "LC11", "LC12", "LC13", "LC14",
            "LC15", "LC16", "LC17", "LC18", "LC20"
        ]

        try:
            # Test batch vs individual queries
            query_results = await self.test_batch_vs_individual_queries(test_types)

            # Test full index creation
            index_results = await self.test_index_creation_performance()

            # Combine results
            all_results = {
                **query_results,
                'index_test': index_results
            }

            # Print results
            self.print_results(all_results)

            # Recommendations
            self._print_recommendations(all_results)

        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()

    def _print_recommendations(self, results: Dict):
        """Print optimization recommendations based on test results."""
        print("\n" + "="*60)
        print("💡 OPTIMIZATION RECOMMENDATIONS")
        print("="*60)

        if 'improvement' in results:
            speedup = results['improvement']['speedup']

            if speedup > 5:
                print("✅ Excellent improvement! Batch queries are working well.")
            elif speedup > 2:
                print("👍 Good improvement! Consider additional optimizations.")
            else:
                print("⚠️  Limited improvement. Check network latency and query complexity.")

        consistency = results.get('consistency', {})
        if not consistency.get('consistent', True):
            print("⚠️  Data consistency issues detected:")
            print("   - Verify batch query logic")
            print("   - Check data filtering and processing")
            print("   - Ensure proper error handling")

        print("\n🎯 Next Steps:")
        print("1. Deploy batch optimization to production")
        print("2. Monitor performance with larger datasets")
        print("3. Implement persistent caching for ROI hierarchy")
        print("4. Consider additional query optimizations")
        print("5. Add performance monitoring and alerting")


async def main():
    """Main test function."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Run tests
    tester = BatchOptimizationTester()
    await tester.run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main())
