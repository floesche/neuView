"""
Deprecation Utility for Resource Strategies

This module provides utilities for tracking, reporting, and guiding migration
from deprecated resource strategies to the modern UnifiedResourceStrategy.
"""

import warnings
import logging
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
import threading

logger = logging.getLogger(__name__)


class DeprecationTracker:
    """
    Tracks usage of deprecated resource strategies and provides migration guidance.

    This class helps identify where deprecated strategies are being used in the
    codebase and provides specific guidance for migrating to UnifiedResourceStrategy.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.deprecated_usages: Dict[str, List[Dict[str, Any]]] = {}
        self.migration_suggestions: Dict[str, str] = {
            'CachedResourceStrategy': """
Migration from CachedResourceStrategy:

OLD CODE:
    fs_strategy = FileSystemResourceStrategy(base_paths=[...])
    cached_strategy = CachedResourceStrategy(fs_strategy, cache_strategy, cache_ttl=3600)

NEW CODE:
    unified_strategy = UnifiedResourceStrategy(
        base_paths=[...],
        cache_strategy=cache_strategy,
        cache_ttl=3600
    )

Benefits:
- No wrapper overhead
- Better performance
- Integrated cache management
- Built-in cache statistics
""",
            'OptimizedResourceStrategy': """
Migration from OptimizedResourceStrategy:

OLD CODE:
    fs_strategy = FileSystemResourceStrategy(base_paths=[...])
    opt_strategy = OptimizedResourceStrategy(
        fs_strategy,
        enable_minification=True,
        enable_compression=True
    )

NEW CODE:
    unified_strategy = UnifiedResourceStrategy(
        base_paths=[...],
        enable_optimization=True,
        enable_minification=True,
        enable_compression=True
    )

Benefits:
- No wrapper overhead
- Better performance
- Integrated optimization
- Enhanced minification algorithms
""",
            'FileSystemResourceStrategy': """
Migration from FileSystemResourceStrategy:

OLD CODE:
    fs_strategy = FileSystemResourceStrategy(base_paths=[...])

NEW CODE:
    unified_strategy = UnifiedResourceStrategy(
        base_paths=[...],
        enable_optimization=False  # If you don't want optimization
    )

Benefits:
- Future-proof architecture
- Optional built-in caching and optimization
- Better error handling
- Enhanced metadata support
"""
        }
        self._initialized = True

    def track_usage(self, strategy_name: str, caller_info: Optional[str] = None) -> None:
        """
        Track usage of a deprecated strategy.

        Args:
            strategy_name: Name of the deprecated strategy
            caller_info: Optional information about where it was called from
        """
        if strategy_name not in self.deprecated_usages:
            self.deprecated_usages[strategy_name] = []

        usage_info = {
            'timestamp': datetime.now().isoformat(),
            'caller': caller_info or 'Unknown',
            'count': 1
        }

        # Check if we already have a record for this caller
        for usage in self.deprecated_usages[strategy_name]:
            if usage['caller'] == usage_info['caller']:
                usage['count'] += 1
                usage['last_seen'] = usage_info['timestamp']
                return

        self.deprecated_usages[strategy_name].append(usage_info)

    def get_usage_report(self) -> str:
        """
        Generate a comprehensive usage report for deprecated strategies.

        Returns:
            Formatted report string
        """
        if not self.deprecated_usages:
            return "✅ No deprecated strategy usage detected!"

        report_lines = [
            "📋 Deprecated Resource Strategy Usage Report",
            "=" * 60,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]

        total_usages = 0
        for strategy_name, usages in self.deprecated_usages.items():
            total_count = sum(usage['count'] for usage in usages)
            total_usages += total_count

            report_lines.extend([
                f"⚠️  {strategy_name}:",
                f"   Total usages: {total_count}",
                f"   Unique locations: {len(usages)}",
                ""
            ])

            for usage in usages:
                report_lines.append(f"   📍 {usage['caller']} (used {usage['count']} times)")

            report_lines.append("")

        report_lines.extend([
            f"📊 Summary: {total_usages} total usages across {len(self.deprecated_usages)} deprecated strategies",
            "",
            "🔧 Migration Priority:",
            "  1. High: CachedResourceStrategy, OptimizedResourceStrategy (redundant wrappers)",
            "  2. Medium: FileSystemResourceStrategy (legacy, but functional)",
            "",
            "📖 For migration guidance, use: get_migration_guide('<strategy_name>')",
            "🚀 For automated migration, use the migration utility in migration.py"
        ])

        return "\n".join(report_lines)

    def get_migration_guide(self, strategy_name: str) -> str:
        """
        Get specific migration guidance for a deprecated strategy.

        Args:
            strategy_name: Name of the deprecated strategy

        Returns:
            Migration guidance string
        """
        if strategy_name in self.migration_suggestions:
            return f"📖 Migration Guide for {strategy_name}:\n{self.migration_suggestions[strategy_name]}"
        else:
            return f"❓ No specific migration guide available for {strategy_name}"

    def clear_tracking(self) -> None:
        """Clear all tracking data."""
        self.deprecated_usages.clear()

    def get_deprecated_strategies(self) -> Set[str]:
        """Get set of all tracked deprecated strategies."""
        return set(self.deprecated_usages.keys())


def warn_deprecated_strategy(strategy_name: str,
                           replacement: str = "UnifiedResourceStrategy",
                           caller_info: Optional[str] = None) -> None:
    """
    Issue a deprecation warning and track usage.

    Args:
        strategy_name: Name of the deprecated strategy
        replacement: Name of the recommended replacement
        caller_info: Optional caller information for tracking
    """
    # Track the usage
    tracker = DeprecationTracker()
    tracker.track_usage(strategy_name, caller_info)

    # Issue the warning
    message = (f"{strategy_name} is deprecated and will be removed in a future version. "
              f"Use {replacement} instead for better performance and simplified configuration.")

    warnings.warn(message, DeprecationWarning, stacklevel=3)
    logger.warning(f"Deprecated strategy usage: {strategy_name} at {caller_info or 'unknown location'}")


def generate_migration_plan(deprecated_usages: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Generate a migration plan based on tracked deprecated strategy usage.

    Args:
        deprecated_usages: Dictionary of deprecated strategy usages

    Returns:
        Migration plan dictionary
    """
    plan = {
        'total_usages': sum(sum(usage['count'] for usage in usages)
                           for usages in deprecated_usages.values()),
        'strategies_to_migrate': list(deprecated_usages.keys()),
        'priority_order': [],
        'estimated_effort': 'Low',
        'migration_steps': [],
        'risk_assessment': 'Low'
    }

    # Determine priority order
    priority_map = {
        'CachedResourceStrategy': 1,
        'OptimizedResourceStrategy': 1,
        'FileSystemResourceStrategy': 2
    }

    plan['priority_order'] = sorted(
        deprecated_usages.keys(),
        key=lambda x: priority_map.get(x, 3)
    )

    # Estimate effort
    if plan['total_usages'] > 20:
        plan['estimated_effort'] = 'High'
    elif plan['total_usages'] > 10:
        plan['estimated_effort'] = 'Medium'

    # Generate migration steps
    plan['migration_steps'] = [
        "1. Review deprecated strategy usage report",
        "2. Identify all locations using deprecated strategies",
        "3. Update imports to use UnifiedResourceStrategy",
        "4. Convert configurations to unified format",
        "5. Test functionality with new strategy",
        "6. Remove deprecated strategy imports",
        "7. Update documentation and examples"
    ]

    # Assess risk
    wrapper_strategies = ['CachedResourceStrategy', 'OptimizedResourceStrategy']
    if any(strategy in deprecated_usages for strategy in wrapper_strategies):
        plan['risk_assessment'] = 'Medium - Complex wrapper patterns need careful migration'

    return plan


def check_project_for_deprecated_usage(project_root: str) -> Dict[str, Any]:
    """
    Scan a project directory for deprecated strategy usage.

    Args:
        project_root: Root directory of the project to scan

    Returns:
        Dictionary containing scan results
    """
    import os
    import re
    from pathlib import Path

    deprecated_strategies = [
        'CachedResourceStrategy',
        'OptimizedResourceStrategy',
        'FileSystemResourceStrategy'  # If used without migration to unified
    ]

    results = {
        'files_scanned': 0,
        'deprecated_found': {},
        'files_with_issues': [],
        'scan_summary': {}
    }

    pattern = re.compile(r'\b(' + '|'.join(deprecated_strategies) + r')\b')

    for root, dirs, files in os.walk(project_root):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]

        for file in files:
            if file.endswith(('.py', '.yaml', '.yml', '.json')):
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        matches = pattern.findall(content)
                        if matches:
                            results['files_with_issues'].append(str(file_path))
                            for match in matches:
                                if match not in results['deprecated_found']:
                                    results['deprecated_found'][match] = []
                                results['deprecated_found'][match].append(str(file_path))

                    results['files_scanned'] += 1
                except Exception as e:
                    logger.warning(f"Could not scan file {file_path}: {e}")

    # Generate summary
    results['scan_summary'] = {
        'total_deprecated_usages': sum(len(files) for files in results['deprecated_found'].values()),
        'unique_deprecated_strategies': len(results['deprecated_found']),
        'files_needing_migration': len(results['files_with_issues']),
        'migration_recommended': len(results['deprecated_found']) > 0
    }

    return results


# Global tracker instance
_tracker = DeprecationTracker()

def get_deprecation_tracker() -> DeprecationTracker:
    """Get the global deprecation tracker instance."""
    return _tracker
