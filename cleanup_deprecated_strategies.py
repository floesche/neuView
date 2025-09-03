#!/usr/bin/env python3
"""
Cleanup Utility for Deprecated Resource Strategies

This utility helps systematically identify, analyze, and clean up deprecated
resource strategy usage throughout the codebase. It provides both analysis
and automated cleanup capabilities for migrating to UnifiedResourceStrategy.
"""

import os
import re
import sys
import ast
import argparse
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass
import logging

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from quickpage.strategies.resource.deprecation import (
        DeprecationTracker,
        check_project_for_deprecated_usage,
        generate_migration_plan
    )
    from quickpage.strategies.resource.migration import (
        ResourceStrategyMigration,
        migrate_resource_config
    )
except ImportError as e:
    print(f"Warning: Could not import deprecation utilities: {e}")
    DeprecationTracker = None

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class DeprecatedCode:
    """Represents a piece of deprecated code found in the codebase."""
    file_path: str
    line_number: int
    code_line: str
    strategy_name: str
    context: str
    suggested_replacement: str


@dataclass
class CleanupStats:
    """Statistics for cleanup operations."""
    files_analyzed: int = 0
    deprecated_usages_found: int = 0
    files_modified: int = 0
    lines_changed: int = 0
    errors_encountered: int = 0


class DeprecatedStrategyAnalyzer:
    """
    Analyzes codebase for deprecated resource strategy usage.
    """

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.deprecated_patterns = {
            'CachedResourceStrategy': {
                'import_pattern': r'from\s+.*\s+import\s+.*CachedResourceStrategy',
                'usage_pattern': r'CachedResourceStrategy\s*\(',
                'replacement': 'UnifiedResourceStrategy with cache_strategy parameter'
            },
            'OptimizedResourceStrategy': {
                'import_pattern': r'from\s+.*\s+import\s+.*OptimizedResourceStrategy',
                'usage_pattern': r'OptimizedResourceStrategy\s*\(',
                'replacement': 'UnifiedResourceStrategy with enable_optimization=True'
            },
            'FileSystemResourceStrategy': {
                'import_pattern': r'from\s+.*\s+import\s+.*FileSystemResourceStrategy',
                'usage_pattern': r'FileSystemResourceStrategy\s*\(',
                'replacement': 'UnifiedResourceStrategy'
            }
        }

    def analyze_file(self, file_path: Path) -> List[DeprecatedCode]:
        """
        Analyze a single file for deprecated strategy usage.

        Args:
            file_path: Path to the file to analyze

        Returns:
            List of deprecated code instances found
        """
        deprecated_instances = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                for strategy_name, patterns in self.deprecated_patterns.items():
                    # Check for imports
                    if re.search(patterns['import_pattern'], line):
                        deprecated_instances.append(DeprecatedCode(
                            file_path=str(file_path),
                            line_number=line_num,
                            code_line=line.strip(),
                            strategy_name=strategy_name,
                            context='import',
                            suggested_replacement=f"from quickpage.strategies.resource import UnifiedResourceStrategy"
                        ))

                    # Check for usage
                    elif re.search(patterns['usage_pattern'], line):
                        deprecated_instances.append(DeprecatedCode(
                            file_path=str(file_path),
                            line_number=line_num,
                            code_line=line.strip(),
                            strategy_name=strategy_name,
                            context='usage',
                            suggested_replacement=patterns['replacement']
                        ))

        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")

        return deprecated_instances

    def analyze_project(self) -> List[DeprecatedCode]:
        """
        Analyze entire project for deprecated strategy usage.

        Returns:
            List of all deprecated code instances found
        """
        all_deprecated = []

        # File patterns to analyze
        file_patterns = ['*.py', '*.yaml', '*.yml']
        exclude_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv'}

        for pattern in file_patterns:
            for file_path in self.project_root.rglob(pattern):
                # Skip excluded directories
                if any(excluded in file_path.parts for excluded in exclude_dirs):
                    continue

                if pattern == '*.py':
                    deprecated_instances = self.analyze_file(file_path)
                    all_deprecated.extend(deprecated_instances)
                elif pattern in ['*.yaml', '*.yml']:
                    # Analyze YAML configuration files
                    config_instances = self._analyze_config_file(file_path)
                    all_deprecated.extend(config_instances)

        return all_deprecated

    def _analyze_config_file(self, file_path: Path) -> List[DeprecatedCode]:
        """Analyze YAML configuration files for deprecated patterns."""
        deprecated_instances = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()

            # Look for legacy configuration patterns
            legacy_patterns = [
                (r"type:\s*['\"]filesystem['\"]", "Use 'unified' strategy type"),
                (r"type:\s*['\"]composite['\"]", "Consider 'unified' for simpler cases"),
            ]

            for line_num, line in enumerate(lines, 1):
                for pattern, suggestion in legacy_patterns:
                    if re.search(pattern, line):
                        deprecated_instances.append(DeprecatedCode(
                            file_path=str(file_path),
                            line_number=line_num,
                            code_line=line.strip(),
                            strategy_name="legacy_config",
                            context="configuration",
                            suggested_replacement=suggestion
                        ))

        except Exception as e:
            logger.error(f"Error analyzing config file {file_path}: {e}")

        return deprecated_instances


class DeprecatedStrategyCleanup:
    """
    Performs automated cleanup of deprecated resource strategy code.
    """

    def __init__(self, project_root: str, dry_run: bool = True):
        self.project_root = Path(project_root)
        self.dry_run = dry_run
        self.stats = CleanupStats()

    def cleanup_imports(self, file_path: Path, deprecated_instances: List[DeprecatedCode]) -> bool:
        """
        Clean up deprecated imports in a file.

        Args:
            file_path: Path to the file to clean up
            deprecated_instances: List of deprecated code instances in this file

        Returns:
            True if file was modified, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()

            modified = False
            new_lines = []
            unified_import_added = False

            for line_num, line in enumerate(lines, 1):
                new_line = line

                # Check if this line has deprecated imports
                import_instances = [inst for inst in deprecated_instances
                                 if inst.line_number == line_num and inst.context == 'import']

                if import_instances:
                    # Replace deprecated imports
                    for instance in import_instances:
                        if 'CachedResourceStrategy' in line:
                            new_line = re.sub(r',?\s*CachedResourceStrategy', '', new_line)
                        if 'OptimizedResourceStrategy' in line:
                            new_line = re.sub(r',?\s*OptimizedResourceStrategy', '', new_line)
                        if 'FileSystemResourceStrategy' in line and 'UnifiedResourceStrategy' not in line:
                            new_line = re.sub(r'FileSystemResourceStrategy', 'UnifiedResourceStrategy', new_line)

                    # Add UnifiedResourceStrategy import if not present
                    if not unified_import_added and 'UnifiedResourceStrategy' not in content:
                        if 'from quickpage.strategies.resource import' in new_line:
                            if 'UnifiedResourceStrategy' not in new_line:
                                new_line = new_line.replace('import (', 'import (\n    UnifiedResourceStrategy,')
                                unified_import_added = True

                    modified = True

                new_lines.append(new_line)

            if modified and not self.dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))

            return modified

        except Exception as e:
            logger.error(f"Error cleaning up imports in {file_path}: {e}")
            self.stats.errors_encountered += 1
            return False

    def suggest_usage_replacements(self, deprecated_instances: List[DeprecatedCode]) -> Dict[str, List[str]]:
        """
        Generate specific replacement suggestions for deprecated usage patterns.

        Args:
            deprecated_instances: List of deprecated code instances

        Returns:
            Dictionary mapping files to replacement suggestions
        """
        suggestions = {}

        for instance in deprecated_instances:
            if instance.context == 'usage':
                file_path = instance.file_path
                if file_path not in suggestions:
                    suggestions[file_path] = []

                if instance.strategy_name == 'CachedResourceStrategy':
                    suggestion = f"Line {instance.line_number}: Replace CachedResourceStrategy wrapper with UnifiedResourceStrategy(cache_strategy=...)"
                elif instance.strategy_name == 'OptimizedResourceStrategy':
                    suggestion = f"Line {instance.line_number}: Replace OptimizedResourceStrategy wrapper with UnifiedResourceStrategy(enable_optimization=True)"
                elif instance.strategy_name == 'FileSystemResourceStrategy':
                    suggestion = f"Line {instance.line_number}: Replace FileSystemResourceStrategy with UnifiedResourceStrategy"
                else:
                    suggestion = f"Line {instance.line_number}: {instance.suggested_replacement}"

                suggestions[file_path].append(suggestion)

        return suggestions

    def cleanup_project(self, deprecated_instances: List[DeprecatedCode]) -> CleanupStats:
        """
        Perform cleanup on the entire project.

        Args:
            deprecated_instances: List of deprecated code instances to clean up

        Returns:
            Cleanup statistics
        """
        files_to_process = {}

        # Group instances by file
        for instance in deprecated_instances:
            file_path = Path(instance.file_path)
            if file_path not in files_to_process:
                files_to_process[file_path] = []
            files_to_process[file_path].append(instance)

        self.stats.files_analyzed = len(files_to_process)
        self.stats.deprecated_usages_found = len(deprecated_instances)

        for file_path, instances in files_to_process.items():
            try:
                # Clean up imports (can be automated)
                if self.cleanup_imports(file_path, instances):
                    self.stats.files_modified += 1
                    self.stats.lines_changed += len([inst for inst in instances if inst.context == 'import'])

            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                self.stats.errors_encountered += 1

        return self.stats


def generate_cleanup_report(deprecated_instances: List[DeprecatedCode]) -> str:
    """
    Generate a comprehensive cleanup report.

    Args:
        deprecated_instances: List of deprecated code instances found

    Returns:
        Formatted report string
    """
    if not deprecated_instances:
        return "✅ No deprecated resource strategy usage found!"

    # Group by strategy type
    by_strategy = {}
    by_file = {}

    for instance in deprecated_instances:
        strategy = instance.strategy_name
        file_path = instance.file_path

        if strategy not in by_strategy:
            by_strategy[strategy] = []
        by_strategy[strategy].append(instance)

        if file_path not in by_file:
            by_file[file_path] = []
        by_file[file_path].append(instance)

    report_lines = [
        "📋 Deprecated Resource Strategy Cleanup Report",
        "=" * 60,
        f"Total deprecated usages found: {len(deprecated_instances)}",
        f"Files affected: {len(by_file)}",
        f"Deprecated strategies: {len(by_strategy)}",
        ""
    ]

    # Summary by strategy
    report_lines.append("📊 By Strategy Type:")
    for strategy, instances in by_strategy.items():
        imports = len([i for i in instances if i.context == 'import'])
        usages = len([i for i in instances if i.context == 'usage'])
        config = len([i for i in instances if i.context == 'configuration'])

        report_lines.append(f"  {strategy}:")
        report_lines.append(f"    Imports: {imports}")
        report_lines.append(f"    Usages: {usages}")
        if config > 0:
            report_lines.append(f"    Config: {config}")
        report_lines.append("")

    # Detailed breakdown by file
    report_lines.append("📁 By File:")
    for file_path, instances in by_file.items():
        rel_path = str(Path(file_path).relative_to(Path.cwd())) if Path(file_path).is_relative_to(Path.cwd()) else file_path
        report_lines.append(f"  {rel_path}: {len(instances)} issue(s)")

        for instance in instances:
            report_lines.append(f"    Line {instance.line_number}: {instance.strategy_name} ({instance.context})")

    report_lines.extend([
        "",
        "🔧 Recommended Actions:",
        "1. Run with --cleanup to automatically fix imports",
        "2. Manually replace strategy usage with UnifiedResourceStrategy",
        "3. Update configuration files to use 'unified' strategy type",
        "4. Test thoroughly after changes",
        "",
        "📖 For detailed migration guidance:",
        "   python -m quickpage.strategies.resource.migration"
    ])

    return "\n".join(report_lines)


def main():
    """Main cleanup utility function."""
    parser = argparse.ArgumentParser(
        description="Cleanup deprecated resource strategy usage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Analyze project for deprecated usage
    python cleanup_deprecated_strategies.py --analyze

    # Generate detailed report
    python cleanup_deprecated_strategies.py --analyze --report

    # Perform automated cleanup (dry run)
    python cleanup_deprecated_strategies.py --cleanup --dry-run

    # Perform actual cleanup
    python cleanup_deprecated_strategies.py --cleanup

    # Full analysis and cleanup
    python cleanup_deprecated_strategies.py --analyze --cleanup --report
        """
    )

    parser.add_argument('--project-root',
                       default='.',
                       help='Root directory of project to analyze (default: current directory)')

    parser.add_argument('--analyze',
                       action='store_true',
                       help='Analyze project for deprecated strategy usage')

    parser.add_argument('--cleanup',
                       action='store_true',
                       help='Perform automated cleanup of deprecated code')

    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Show what would be changed without making actual changes')

    parser.add_argument('--report',
                       action='store_true',
                       help='Generate detailed cleanup report')

    parser.add_argument('--output',
                       help='Output file for report (default: stdout)')

    parser.add_argument('--verbose', '-v',
                       action='store_true',
                       help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    project_root = Path(args.project_root).resolve()

    if not project_root.exists():
        logger.error(f"Project root does not exist: {project_root}")
        return 1

    print(f"🔍 Analyzing project: {project_root}")

    # Analyze project
    analyzer = DeprecatedStrategyAnalyzer(str(project_root))
    deprecated_instances = analyzer.analyze_project()

    print(f"Found {len(deprecated_instances)} deprecated usage instances")

    # Generate report if requested
    if args.report or args.analyze:
        report = generate_cleanup_report(deprecated_instances)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"📄 Report written to: {args.output}")
        else:
            print("\n" + report)

    # Perform cleanup if requested
    if args.cleanup:
        print(f"\n🧹 Starting cleanup (dry_run={args.dry_run})...")

        cleanup = DeprecatedStrategyCleanup(str(project_root), dry_run=args.dry_run)
        stats = cleanup.cleanup_project(deprecated_instances)

        print(f"\n📊 Cleanup Statistics:")
        print(f"  Files analyzed: {stats.files_analyzed}")
        print(f"  Deprecated usages found: {stats.deprecated_usages_found}")
        print(f"  Files modified: {stats.files_modified}")
        print(f"  Lines changed: {stats.lines_changed}")
        print(f"  Errors encountered: {stats.errors_encountered}")

        if args.dry_run:
            print("\n⚠️  This was a dry run. Use --cleanup without --dry-run to apply changes.")
        else:
            print("\n✅ Cleanup completed!")

    # Show migration suggestions
    if deprecated_instances:
        cleanup = DeprecatedStrategyCleanup(str(project_root), dry_run=True)
        suggestions = cleanup.suggest_usage_replacements(deprecated_instances)

        if suggestions:
            print("\n💡 Manual Migration Suggestions:")
            for file_path, file_suggestions in suggestions.items():
                rel_path = str(Path(file_path).relative_to(project_root)) if Path(file_path).is_relative_to(project_root) else file_path
                print(f"\n  📁 {rel_path}:")
                for suggestion in file_suggestions:
                    print(f"    • {suggestion}")

    print(f"\n{'🎉 Project is clean!' if not deprecated_instances else '⚠️  Migration needed'}")
    return 0 if not deprecated_instances else 1


if __name__ == "__main__":
    sys.exit(main())
