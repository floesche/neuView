#!/usr/bin/env python3
"""
Cache Migration Script for QuickPage
Migrates existing cache files from old locations to the new output/.cache directory.
"""

import os
import shutil
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def setup_logging():
    """Set up logging for the migration script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def migrate_cache_to_output_directory():
    """
    Migrate cache files from old locations to output/.cache directory.

    Old locations:
    - cache/roi_hierarchy.json
    - cache/ (general cache directory)

    New location:
    - output/.cache/roi_hierarchy.json
    """
    print("🔄 Starting cache migration to output/.cache")

    # Define paths
    old_cache_dir = Path("cache")
    old_roi_cache = old_cache_dir / "roi_hierarchy.json"

    output_dir = Path("output")
    new_cache_dir = output_dir / ".cache"
    new_roi_cache = new_cache_dir / "roi_hierarchy.json"

    migration_log = []

    # Create new cache directory
    new_cache_dir.mkdir(parents=True, exist_ok=True)
    migration_log.append(f"✅ Created new cache directory: {new_cache_dir}")

    # Migrate ROI hierarchy cache
    if old_roi_cache.exists():
        try:
            # Validate the cache file before migration
            with open(old_roi_cache, 'r') as f:
                cache_data = json.load(f)

            # Check if it's a valid cache structure
            if 'hierarchy' in cache_data and 'timestamp' in cache_data:
                # Copy to new location
                shutil.copy2(old_roi_cache, new_roi_cache)
                migration_log.append(f"✅ Migrated ROI hierarchy cache: {old_roi_cache} → {new_roi_cache}")

                # Verify the migration
                with open(new_roi_cache, 'r') as f:
                    migrated_data = json.load(f)

                if migrated_data == cache_data:
                    migration_log.append(f"✅ Verified cache integrity after migration")
                else:
                    migration_log.append(f"⚠️  Cache integrity check failed")

            else:
                migration_log.append(f"⚠️  Invalid cache format in {old_roi_cache}, skipping migration")

        except Exception as e:
            migration_log.append(f"❌ Failed to migrate ROI cache: {e}")
    else:
        migration_log.append(f"ℹ️  No existing ROI cache found at {old_roi_cache}")

    # Migrate other cache files if they exist
    if old_cache_dir.exists():
        for cache_file in old_cache_dir.iterdir():
            if cache_file.is_file() and cache_file.name != "roi_hierarchy.json":
                try:
                    new_cache_file = new_cache_dir / cache_file.name
                    shutil.copy2(cache_file, new_cache_file)
                    migration_log.append(f"✅ Migrated cache file: {cache_file} → {new_cache_file}")
                except Exception as e:
                    migration_log.append(f"❌ Failed to migrate {cache_file}: {e}")

    # Print migration summary
    print("\n📊 Cache Migration Summary:")
    for log_entry in migration_log:
        print(f"   {log_entry}")

    return migration_log


def cleanup_old_cache(confirm=True):
    """
    Clean up old cache directory after successful migration.

    Args:
        confirm: If True, asks for user confirmation before deletion
    """
    old_cache_dir = Path("cache")

    if not old_cache_dir.exists():
        print("ℹ️  No old cache directory to clean up")
        return

    if confirm:
        response = input(f"\n🗑️  Remove old cache directory '{old_cache_dir}'? (y/N): ").lower().strip()
        if response not in ['y', 'yes']:
            print("ℹ️  Keeping old cache directory")
            return

    try:
        shutil.rmtree(old_cache_dir)
        print(f"✅ Removed old cache directory: {old_cache_dir}")
    except Exception as e:
        print(f"❌ Failed to remove old cache directory: {e}")


def verify_new_cache_structure():
    """Verify that the new cache structure is working correctly."""
    print("\n🔍 Verifying new cache structure...")

    output_dir = Path("output")
    cache_dir = output_dir / ".cache"
    roi_cache = cache_dir / "roi_hierarchy.json"

    checks = []

    # Check if cache directory exists
    if cache_dir.exists():
        checks.append("✅ Cache directory exists")
    else:
        checks.append("❌ Cache directory missing")

    # Check if ROI cache exists and is valid
    if roi_cache.exists():
        try:
            with open(roi_cache, 'r') as f:
                cache_data = json.load(f)

            if 'hierarchy' in cache_data and 'timestamp' in cache_data:
                checks.append("✅ ROI hierarchy cache is valid")

                # Check cache age
                import time
                cache_age = time.time() - cache_data.get('timestamp', 0)
                if cache_age < 24 * 3600:  # 24 hours
                    checks.append(f"✅ ROI cache is fresh ({cache_age/3600:.1f} hours old)")
                else:
                    checks.append(f"⚠️  ROI cache is stale ({cache_age/3600:.1f} hours old)")
            else:
                checks.append("❌ ROI hierarchy cache has invalid format")

        except Exception as e:
            checks.append(f"❌ Failed to read ROI cache: {e}")
    else:
        checks.append("ℹ️  No ROI cache found (will be created on first use)")

    # Check permissions
    try:
        test_file = cache_dir / "test_write.tmp"
        test_file.write_text("test")
        test_file.unlink()
        checks.append("✅ Cache directory is writable")
    except Exception as e:
        checks.append(f"❌ Cache directory not writable: {e}")

    print("📋 Cache verification results:")
    for check in checks:
        print(f"   {check}")

    return checks


def main():
    """Main migration function."""
    setup_logging()

    print("🚀 QuickPage Cache Migration Tool")
    print("=" * 50)

    # Check prerequisites
    if not Path("output").exists():
        print("❌ Output directory not found. Please ensure QuickPage has been run at least once.")
        return

    # Perform migration
    migration_log = migrate_cache_to_output_directory()

    # Verify new structure
    verification_results = verify_new_cache_structure()

    # Offer to clean up old cache
    cleanup_old_cache(confirm=True)

    print("\n" + "=" * 50)
    print("🎯 Migration completed!")
    print("\nNext steps:")
    print("1. The cache is now located in output/.cache/")
    print("2. ROI hierarchy will be cached persistently across runs")
    print("3. Cache files will be automatically managed by QuickPage")
    print("4. No further manual intervention required")

    # Generate migration report
    generate_migration_report(migration_log, verification_results)


def generate_migration_report(migration_log, verification_results):
    """Generate a migration report file."""
    report_path = Path("cache_migration_report.txt")

    try:
        with open(report_path, 'w') as f:
            f.write("QuickPage Cache Migration Report\n")
            f.write("=" * 40 + "\n\n")

            f.write("Migration Log:\n")
            for log_entry in migration_log:
                f.write(f"  {log_entry}\n")

            f.write("\nVerification Results:\n")
            for result in verification_results:
                f.write(f"  {result}\n")

            f.write(f"\nMigration completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        print(f"📄 Migration report saved to: {report_path}")

    except Exception as e:
        print(f"⚠️  Failed to generate migration report: {e}")


if __name__ == "__main__":
    import time
    main()
