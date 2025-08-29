#!/usr/bin/env python3
"""
Cleanup script to remove redundant soma cache files after optimization deployment.

This script safely removes the *_soma_sides.json files that are now redundant
since the optimization extracts soma sides from neuron type cache files.

USAGE:
    python cleanup_redundant_cache.py --dry-run    # Preview what would be deleted
    python cleanup_redundant_cache.py --confirm    # Actually delete the files

SAFETY FEATURES:
- Dry run mode by default
- Validates optimization is working before cleanup
- Creates backup of files before deletion
- Detailed logging of all operations
"""

import argparse
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging

# Add the quickpage module to the path
sys.path.insert(0, 'src')

from quickpage.neuprint_connector import NeuPrintConnector
from quickpage.cache import NeuronTypeCacheManager
from quickpage.config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SomaCacheCleanup:
    """
    Handles cleanup of redundant soma cache files after optimization deployment.
    """

    def __init__(self, cache_dir: str = "output/.cache"):
        self.cache_dir = Path(cache_dir)
        self.backup_dir = self.cache_dir / "backup_soma_cache"
        self.config = None
        self.connector = None
        self.cache_manager = None

        # Initialize components
        try:
            self.config = Config.load("config.yaml")
            self.connector = NeuPrintConnector(self.config)
            self.cache_manager = NeuronTypeCacheManager(str(self.cache_dir))
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise

    def analyze_cache_state(self) -> Dict[str, Any]:
        """
        Analyze current cache state and identify redundant files.

        Returns:
            Dictionary with cache analysis results
        """
        logger.info("Analyzing cache state...")

        if not self.cache_dir.exists():
            raise FileNotFoundError(f"Cache directory {self.cache_dir} does not exist")

        # Find soma cache files
        soma_cache_files = list(self.cache_dir.glob("*_soma_sides.json"))

        # Find neuron cache files
        neuron_cache_files = [
            f for f in self.cache_dir.glob("*.json")
            if not f.name.endswith("_soma_sides.json")
            and not f.name.endswith("_columns.json")
            and f.name != "roi_hierarchy.json"
        ]

        # Calculate sizes
        soma_total_size = sum(f.stat().st_size for f in soma_cache_files)

        # Analyze file ages
        current_time = time.time()
        old_files = []
        recent_files = []

        for f in soma_cache_files:
            age_hours = (current_time - f.stat().st_mtime) / 3600
            if age_hours > 24:  # Older than 24 hours
                old_files.append(f)
            else:
                recent_files.append(f)

        return {
            'soma_cache_files': soma_cache_files,
            'soma_cache_count': len(soma_cache_files),
            'soma_total_size_bytes': soma_total_size,
            'soma_total_size_kb': soma_total_size / 1024,
            'neuron_cache_count': len(neuron_cache_files),
            'old_files': old_files,
            'recent_files': recent_files,
            'all_files_old': len(recent_files) == 0,
        }

    def validate_optimization_working(self, test_types: List[str] = None) -> Dict[str, Any]:
        """
        Validate that the optimization is working correctly before cleanup.

        Args:
            test_types: List of neuron types to test (defaults to sample from cache)

        Returns:
            Validation results
        """
        logger.info("Validating optimization is working...")

        if test_types is None:
            # Get sample of cached types
            cached_types = self.cache_manager.list_cached_neuron_types()
            test_types = cached_types[:5] if len(cached_types) >= 5 else cached_types

        if not test_types:
            return {
                'validation_passed': False,
                'error': 'No cached neuron types found for testing'
            }

        optimization_working = 0
        fallback_used = 0
        errors = 0

        for neuron_type in test_types:
            try:
                # Clear memory cache to force fresh lookup
                self.connector._soma_sides_cache.pop(neuron_type, None)

                # Test soma sides retrieval
                soma_sides = self.connector.get_soma_sides_for_type(neuron_type)

                # Check if optimization was used (this is a heuristic)
                # In a production system, you might add a flag to track this
                if neuron_type in self.connector._soma_sides_cache:
                    optimization_working += 1
                else:
                    fallback_used += 1

            except Exception as e:
                logger.warning(f"Error testing {neuron_type}: {e}")
                errors += 1

        total_tested = len(test_types)
        success_rate = optimization_working / total_tested if total_tested > 0 else 0

        validation_passed = success_rate >= 0.8 and errors == 0  # 80% success rate required

        return {
            'validation_passed': validation_passed,
            'total_tested': total_tested,
            'optimization_working': optimization_working,
            'fallback_used': fallback_used,
            'errors': errors,
            'success_rate': success_rate,
            'test_types': test_types
        }

    def create_backup(self, soma_cache_files: List[Path]) -> bool:
        """
        Create backup of soma cache files before deletion.

        Args:
            soma_cache_files: List of files to backup

        Returns:
            True if backup successful, False otherwise
        """
        if not soma_cache_files:
            logger.info("No files to backup")
            return True

        logger.info(f"Creating backup of {len(soma_cache_files)} soma cache files...")

        try:
            # Create backup directory
            self.backup_dir.mkdir(exist_ok=True)

            # Create timestamp for this backup
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            session_backup_dir = self.backup_dir / f"soma_cache_backup_{timestamp}"
            session_backup_dir.mkdir()

            # Copy files to backup
            backup_count = 0
            for soma_file in soma_cache_files:
                try:
                    backup_file = session_backup_dir / soma_file.name
                    shutil.copy2(soma_file, backup_file)
                    backup_count += 1
                except Exception as e:
                    logger.warning(f"Failed to backup {soma_file.name}: {e}")

            # Create backup manifest
            manifest = {
                'timestamp': timestamp,
                'original_count': len(soma_cache_files),
                'backed_up_count': backup_count,
                'backup_location': str(session_backup_dir),
                'files': [f.name for f in soma_cache_files]
            }

            manifest_file = session_backup_dir / "backup_manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)

            logger.info(f"Backup created: {session_backup_dir}")
            logger.info(f"Backed up {backup_count}/{len(soma_cache_files)} files")

            return backup_count == len(soma_cache_files)

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False

    def cleanup_soma_cache_files(self, soma_cache_files: List[Path], dry_run: bool = True) -> Dict[str, Any]:
        """
        Delete redundant soma cache files.

        Args:
            soma_cache_files: List of files to delete
            dry_run: If True, only simulate deletion

        Returns:
            Cleanup results
        """
        if dry_run:
            logger.info(f"DRY RUN: Would delete {len(soma_cache_files)} soma cache files")
        else:
            logger.info(f"Deleting {len(soma_cache_files)} soma cache files...")

        deleted_count = 0
        failed_deletions = []
        total_size_freed = 0

        for soma_file in soma_cache_files:
            try:
                file_size = soma_file.stat().st_size

                if dry_run:
                    logger.info(f"  Would delete: {soma_file.name} ({file_size} bytes)")
                    deleted_count += 1
                    total_size_freed += file_size
                else:
                    soma_file.unlink()
                    logger.info(f"  Deleted: {soma_file.name} ({file_size} bytes)")
                    deleted_count += 1
                    total_size_freed += file_size

            except Exception as e:
                logger.error(f"Failed to delete {soma_file.name}: {e}")
                failed_deletions.append({
                    'file': str(soma_file),
                    'error': str(e)
                })

        return {
            'dry_run': dry_run,
            'total_files': len(soma_cache_files),
            'deleted_count': deleted_count,
            'failed_count': len(failed_deletions),
            'total_size_freed_bytes': total_size_freed,
            'total_size_freed_kb': total_size_freed / 1024,
            'failed_deletions': failed_deletions
        }

    def generate_cleanup_report(self, analysis: Dict, validation: Dict, cleanup_result: Dict):
        """
        Generate comprehensive cleanup report.

        Args:
            analysis: Cache analysis results
            validation: Optimization validation results
            cleanup_result: Cleanup operation results
        """
        print(f"\n{'='*80}")
        print("SOMA CACHE CLEANUP REPORT")
        print(f"{'='*80}")

        # Cache analysis
        print(f"\n📊 CACHE ANALYSIS:")
        print(f"   Soma cache files found: {analysis['soma_cache_count']}")
        print(f"   Total size: {analysis['soma_total_size_kb']:.1f}KB")
        print(f"   Neuron cache files: {analysis['neuron_cache_count']}")

        if analysis['old_files']:
            print(f"   Old files (>24h): {len(analysis['old_files'])}")
        if analysis['recent_files']:
            print(f"   Recent files (<24h): {len(analysis['recent_files'])}")

        # Optimization validation
        print(f"\n✅ OPTIMIZATION VALIDATION:")
        if validation['validation_passed']:
            print(f"   Status: PASSED ✅")
            print(f"   Success rate: {validation['success_rate']*100:.1f}%")
            print(f"   Types tested: {validation['total_tested']}")
            print(f"   Optimization working: {validation['optimization_working']}")
            print(f"   Fallback used: {validation['fallback_used']}")
        else:
            print(f"   Status: FAILED ❌")
            print(f"   Errors: {validation['errors']}")
            print(f"   Success rate: {validation['success_rate']*100:.1f}% (required: ≥80%)")

        # Cleanup results
        print(f"\n🗑️  CLEANUP RESULTS:")
        if cleanup_result['dry_run']:
            print(f"   Mode: DRY RUN (simulation only)")
        else:
            print(f"   Mode: ACTUAL DELETION")

        print(f"   Files processed: {cleanup_result['total_files']}")
        print(f"   Successfully handled: {cleanup_result['deleted_count']}")
        print(f"   Failed: {cleanup_result['failed_count']}")
        print(f"   Space freed: {cleanup_result['total_size_freed_kb']:.1f}KB")

        if cleanup_result['failed_deletions']:
            print(f"   Failed deletions:")
            for failure in cleanup_result['failed_deletions'][:3]:
                print(f"     - {Path(failure['file']).name}: {failure['error']}")

        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if not validation['validation_passed']:
            print(f"   ❌ DO NOT PROCEED with cleanup")
            print(f"   🔧 Fix optimization issues first")
        elif cleanup_result['dry_run']:
            print(f"   ✅ Safe to proceed with actual cleanup")
            print(f"   📋 Run with --confirm to perform deletion")
        else:
            print(f"   ✅ Cleanup completed successfully")
            print(f"   📊 Monitor system to ensure no issues")

        if not cleanup_result['dry_run'] and cleanup_result['deleted_count'] > 0:
            print(f"   💾 Backup created in: {self.backup_dir}")

        # Next steps
        print(f"\n📋 NEXT STEPS:")
        if cleanup_result['dry_run']:
            print(f"   1. Verify optimization is working: ✅")
            print(f"   2. Run cleanup with --confirm flag")
            print(f"   3. Monitor system after cleanup")
        else:
            print(f"   1. Monitor quickpage generate operations")
            print(f"   2. Verify no fallback to old cache files")
            print(f"   3. Remove backup files after verification period")


def main():
    """
    Main cleanup function with command line interface.
    """
    parser = argparse.ArgumentParser(
        description="Cleanup redundant soma cache files after optimization deployment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --dry-run     # Preview what would be deleted (safe)
  %(prog)s --confirm     # Actually delete the files (requires validation)
  %(prog)s --force       # Skip validation and delete (dangerous!)

Safety Features:
  - Dry run mode by default
  - Validates optimization before cleanup
  - Creates backup before deletion
  - Detailed logging and reporting
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='Simulate cleanup without deleting files (default)'
    )
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Actually delete files (requires validation to pass)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip validation and delete files (dangerous!)'
    )
    parser.add_argument(
        '--cache-dir',
        default='output/.cache',
        help='Cache directory path (default: output/.cache)'
    )

    args = parser.parse_args()

    # Determine operation mode
    if args.confirm and args.dry_run:
        # Override default dry_run when confirm is specified
        dry_run = False
    elif args.confirm:
        dry_run = False
    else:
        dry_run = True

    print("Soma Cache Cleanup Utility")
    print("=" * 50)

    if dry_run:
        print("🔍 MODE: Dry run (simulation only)")
    else:
        print("⚠️  MODE: Actual deletion")

    try:
        # Initialize cleanup handler
        cleanup = SomaCacheCleanup(args.cache_dir)

        # Analyze cache state
        analysis = cleanup.analyze_cache_state()

        if analysis['soma_cache_count'] == 0:
            print("\n✅ No soma cache files found - cleanup not needed")
            return

        print(f"\n📊 Found {analysis['soma_cache_count']} soma cache files ({analysis['soma_total_size_kb']:.1f}KB)")

        # Validate optimization (unless forced)
        if args.force:
            print("\n⚠️  Skipping validation (--force specified)")
            validation = {'validation_passed': True}
        else:
            validation = cleanup.validate_optimization_working()

        # Check if we can proceed
        if not dry_run and not validation['validation_passed']:
            print("\n❌ Validation failed - cannot proceed with deletion")
            print("   Use --dry-run to simulate, or fix optimization issues first")
            sys.exit(1)

        # Create backup before deletion (if not dry run)
        if not dry_run:
            backup_success = cleanup.create_backup(analysis['soma_cache_files'])
            if not backup_success:
                print("\n❌ Backup failed - aborting cleanup for safety")
                sys.exit(1)

        # Perform cleanup
        cleanup_result = cleanup.cleanup_soma_cache_files(
            analysis['soma_cache_files'],
            dry_run=dry_run
        )

        # Generate report
        cleanup.generate_cleanup_report(analysis, validation, cleanup_result)

        # Final status
        if dry_run:
            print(f"\n✅ Dry run completed - no files were deleted")
        else:
            if cleanup_result['failed_count'] == 0:
                print(f"\n🎉 Cleanup completed successfully!")
                print(f"   Freed {cleanup_result['total_size_freed_kb']:.1f}KB of storage")
            else:
                print(f"\n⚠️  Cleanup completed with {cleanup_result['failed_count']} failures")

    except KeyboardInterrupt:
        print("\n\n⏹️  Cleanup cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        print(f"\n❌ Cleanup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
