#!/usr/bin/env python3
"""
Single Query Profiler for NeuPrint

A simple script for profiling individual NeuPrint queries.
Useful for testing specific queries and measuring their performance.

Usage:
    python single_query_profiler.py --config config.yaml --query "MATCH (n:Neuron) RETURN count(n)"
    python single_query_profiler.py --config config.yaml --query-file my_query.cypher --runs 5
    python single_query_profiler.py --server neuprint.janelia.org --dataset "hemibrain:v1.2.1" --query "MATCH (n:Neuron) WHERE n.type = 'T4' RETURN n.bodyId LIMIT 10"
"""

import time
import argparse
import sys
import os
import statistics
from typing import Optional, Any, Dict, List
from pathlib import Path

try:
    import yaml
    from neuprint import Client
    from dotenv import load_dotenv
    import pandas as pd
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please install required dependencies:")
    print("pip install pandas pyyaml neuprint-python python-dotenv")
    sys.exit(1)


class SingleQueryProfiler:
    """Simple profiler for individual NeuPrint queries."""

    def __init__(self, server: str, dataset: str, token: str = None):
        """Initialize the profiler."""
        # Load environment variables from .env file
        load_dotenv()

        self.server = server
        self.dataset = dataset
        self.token = token or os.getenv('NEUPRINT_TOKEN')
        self.client = None

        if not self.token:
            raise ValueError(
                "NeuPrint token not found. Please:\n"
                "1. Set NEUPRINT_TOKEN in .env file, or\n"
                "2. Set NEUPRINT_TOKEN environment variable, or\n"
                "3. Use --token command line argument"
            )

    def connect(self) -> bool:
        """Connect to NeuPrint server."""
        try:
            self.client = Client(self.server, dataset=self.dataset, token=self.token)
            # Test connection
            info = self.client.fetch_database()
            print(f"✓ Connected to {self.server}")
            print(f"✓ Dataset: {self.dataset}")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False

    def profile_query(self, query: str, runs: int = 1, description: str = None) -> Dict[str, Any]:
        """Profile a single query with multiple runs."""
        if not self.client:
            if not self.connect():
                raise ConnectionError("Could not connect to NeuPrint")

        print(f"\n{'='*60}")
        print(f"PROFILING QUERY")
        print(f"{'='*60}")

        if description:
            print(f"Description: {description}")

        # Show query (truncated if too long)
        query_display = query.strip()
        if len(query_display) > 200:
            query_display = query_display[:200] + "..."
        print(f"Query: {query_display}")
        print(f"Runs: {runs}")
        print(f"{'='*60}")

        times = []
        result_counts = []
        errors = []

        for run in range(runs):
            print(f"Run {run + 1}/{runs}...", end=" ", flush=True)

            start_time = time.time()
            try:
                result = self.client.fetch_custom(query)
                execution_time = time.time() - start_time

                # Determine result count
                if isinstance(result, pd.DataFrame):
                    result_count = len(result)
                elif isinstance(result, (list, tuple)):
                    result_count = len(result)
                elif isinstance(result, dict):
                    result_count = len(result)
                else:
                    result_count = 1 if result is not None else 0

                times.append(execution_time)
                result_counts.append(result_count)

                print(f"{execution_time:.3f}s ({result_count} results)")

            except Exception as e:
                execution_time = time.time() - start_time
                errors.append(str(e))
                print(f"ERROR after {execution_time:.3f}s: {str(e)[:50]}...")

        # Calculate statistics
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            std_time = statistics.stdev(times) if len(times) > 1 else 0.0
            median_time = statistics.median(times)
            avg_results = statistics.mean(result_counts)
        else:
            avg_time = min_time = max_time = std_time = median_time = avg_results = 0.0

        success_rate = (runs - len(errors)) / runs if runs > 0 else 0.0

        # Display results
        print(f"\n{'='*60}")
        print(f"RESULTS")
        print(f"{'='*60}")
        print(f"Success Rate:     {success_rate:.1%}")
        print(f"Average Time:     {avg_time:.3f}s")
        print(f"Median Time:      {median_time:.3f}s")
        print(f"Min/Max Time:     {min_time:.3f}s / {max_time:.3f}s")
        if std_time > 0:
            print(f"Std Deviation:    {std_time:.3f}s")
        print(f"Average Results:  {avg_results:.0f}")

        if errors:
            print(f"\nErrors ({len(errors)}):")
            for i, error in enumerate(errors[:3], 1):  # Show first 3 errors
                print(f"  {i}. {error}")
            if len(errors) > 3:
                print(f"  ... and {len(errors) - 3} more")

        # Performance assessment
        print(f"\nPerformance Assessment:")
        if success_rate < 0.8:
            print("  ⚠️  Low success rate - query may have issues")
        elif avg_time < 1.0:
            print("  ✅ Fast query (< 1s)")
        elif avg_time < 5.0:
            print("  ⚡ Moderate query (1-5s)")
        elif avg_time < 30.0:
            print("  🐌 Slow query (5-30s)")
        else:
            print("  🚨 Very slow query (> 30s)")

        if std_time > avg_time * 0.3:
            print("  ⚠️  High variability - performance inconsistent")

        return {
            'query': query,
            'description': description,
            'runs': runs,
            'success_rate': success_rate,
            'times': times,
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'std_time': std_time,
            'median_time': median_time,
            'result_counts': result_counts,
            'avg_results': avg_results,
            'errors': errors
        }


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    load_dotenv()

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Extract neuprint configuration
    neuprint_config = config.get('neuprint', {})
    token = neuprint_config.get('token') or os.getenv('NEUPRINT_TOKEN')

    return {
        'server': neuprint_config.get('server'),
        'dataset': neuprint_config.get('dataset'),
        'token': token
    }


def load_query_file(file_path: str) -> str:
    """Load query from file."""
    try:
        with open(file_path, 'r') as f:
            query = f.read().strip()

        if not query:
            raise ValueError("Query file is empty")

        return query
    except Exception as e:
        raise ValueError(f"Error reading query file '{file_path}': {e}")


def validate_query(query: str) -> bool:
    """Basic query validation."""
    query = query.strip().upper()

    # Check for basic Cypher keywords
    cypher_keywords = ['MATCH', 'RETURN', 'WHERE', 'WITH', 'CREATE', 'DELETE', 'SET']
    has_cypher = any(keyword in query for keyword in cypher_keywords)

    if not has_cypher:
        print("⚠️  Warning: Query doesn't contain common Cypher keywords")
        print("   Make sure this is a valid Cypher query")

    # Check for potentially dangerous operations
    dangerous_keywords = ['DELETE', 'CREATE', 'SET', 'REMOVE', 'MERGE']
    has_dangerous = any(keyword in query for keyword in dangerous_keywords)

    if has_dangerous:
        print("⚠️  Warning: Query contains write operations")
        response = input("   Are you sure you want to execute this query? (y/N): ")
        return response.lower().strip() in ['y', 'yes']

    return True


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description='Profile a single NeuPrint query',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using config file
  python single_query_profiler.py --config config.yaml --query "MATCH (n:Neuron) RETURN count(n)"

  # Using query file
  python single_query_profiler.py --config config.yaml --query-file my_query.cypher --runs 5

  # Direct connection
  python single_query_profiler.py --server neuprint.janelia.org --dataset "hemibrain:v1.2.1" --query "MATCH (n:Neuron) WHERE n.type = 'T4' RETURN n.bodyId LIMIT 10"
        """
    )

    # Connection options
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--config', '-c', help='Path to config YAML file')
    group.add_argument('--server', help='NeuPrint server URL')

    parser.add_argument('--dataset', '-d', help='Dataset name (required if using --server)')
    parser.add_argument('--token', '-t', help='NeuPrint authentication token')

    # Query options
    query_group = parser.add_mutually_exclusive_group(required=True)
    query_group.add_argument('--query', '-q', help='Cypher query to execute')
    query_group.add_argument('--query-file', '-f', help='File containing Cypher query')

    # Profiling options
    parser.add_argument('--runs', '-r', type=int, default=1,
                       help='Number of times to run the query (default: 1)')
    parser.add_argument('--description', help='Description of the query')
    parser.add_argument('--no-validation', action='store_true',
                       help='Skip query validation')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    try:
        # Get connection parameters
        if args.config:
            if not os.path.exists(args.config):
                print(f"Error: Config file '{args.config}' not found.")
                sys.exit(1)
            config = load_config(args.config)
            server = config['server']
            dataset = config['dataset']
            token = config['token']
        else:
            if not args.dataset:
                print("Error: --dataset is required when using --server")
                sys.exit(1)
            server = args.server
            dataset = args.dataset
            token = args.token or os.getenv('NEUPRINT_TOKEN')

        # Validate connection parameters
        if not server or not dataset:
            print("Error: Server and dataset must be specified")
            sys.exit(1)

        if not token:
            print("Error: NeuPrint token not found.")
            print("Please set NEUPRINT_TOKEN in .env file or use --token")
            sys.exit(1)

        # Get query
        if args.query_file:
            query = load_query_file(args.query_file)
            description = args.description or f"Query from {args.query_file}"
        else:
            query = args.query
            description = args.description

        # Validate query
        if not args.no_validation:
            if not validate_query(query):
                print("Query execution cancelled.")
                sys.exit(1)

        # Validate runs
        if args.runs < 1:
            print("Error: Number of runs must be at least 1")
            sys.exit(1)

        if args.runs > 20:
            print("Warning: Large number of runs may take a long time")
            response = input(f"Run query {args.runs} times? (y/N): ")
            if response.lower().strip() not in ['y', 'yes']:
                sys.exit(1)

        # Create profiler and run
        profiler = SingleQueryProfiler(server, dataset, token)

        print(f"Single Query Profiler")
        print(f"Server: {server}")
        print(f"Dataset: {dataset}")

        results = profiler.profile_query(query, args.runs, description)

        print(f"\n{'='*60}")
        print("PROFILING COMPLETE")
        print(f"{'='*60}")

        if args.verbose and results['times']:
            print(f"Individual times: {[f'{t:.3f}s' for t in results['times']]}")
            print(f"Individual result counts: {results['result_counts']}")

    except KeyboardInterrupt:
        print("\n\nProfiler interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
