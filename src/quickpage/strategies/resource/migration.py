"""
Resource Strategy Migration Utility

This module provides utilities to help migrate from legacy resource strategy
configurations to the new unified strategy approach. It includes configuration
conversion, compatibility checking, and migration guidance.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class ResourceStrategyMigration:
    """
    Utility class for migrating resource strategy configurations.

    This class helps convert legacy resource strategy configurations
    to the new unified strategy format while maintaining backward compatibility.
    """

    @staticmethod
    def detect_legacy_configuration(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect legacy configuration patterns and return migration recommendations.

        Args:
            config: Resource configuration dictionary

        Returns:
            Dictionary containing migration recommendations and detected issues
        """
        issues = []
        recommendations = []
        legacy_patterns = []

        resource_config = config.get('resource', {})
        strategy_type = resource_config.get('type', 'filesystem')

        # Check for legacy strategy types
        if strategy_type == 'filesystem':
            legacy_patterns.append("Using legacy 'filesystem' strategy type")
            recommendations.append("Consider migrating to 'unified' strategy type")

        # Check for complex wrapping patterns
        if resource_config.get('optimize', False) and strategy_type == 'filesystem':
            legacy_patterns.append("Using OptimizedResourceStrategy wrapper pattern")
            recommendations.append("Unified strategy has built-in optimization")

        # Check for cache configuration that would trigger wrapping
        cache_config = config.get('cache', {})
        if cache_config.get('enabled', False) and strategy_type == 'filesystem':
            legacy_patterns.append("Using CachedResourceStrategy wrapper pattern")
            recommendations.append("Unified strategy has built-in caching")

        # Check for deprecated parameter names
        if 'resource_dirs' in resource_config:
            legacy_patterns.append("Using deprecated 'resource_dirs' parameter")
            recommendations.append("Rename 'resource_dirs' to 'base_paths'")

        # Check for lambda functions in composite strategy (if detectable)
        if strategy_type == 'composite':
            recommendations.append("Ensure composite strategy uses regex patterns, not lambda functions")

        return {
            'has_legacy_patterns': len(legacy_patterns) > 0,
            'legacy_patterns': legacy_patterns,
            'recommendations': recommendations,
            'migration_needed': len(legacy_patterns) > 2,  # More than 2 issues suggests full migration needed
            'current_strategy': strategy_type
        }

    @staticmethod
    def convert_to_unified_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert legacy resource configuration to unified strategy format.

        Args:
            config: Original configuration dictionary

        Returns:
            Updated configuration dictionary using unified strategy
        """
        new_config = config.copy()
        resource_config = new_config.get('resource', {})
        cache_config = new_config.get('cache', {})

        # Convert to unified strategy
        new_resource_config = {
            'type': 'unified',
            'follow_symlinks': resource_config.get('follow_symlinks', True),
            'optimize': resource_config.get('optimize', False),
            'minify': resource_config.get('minify', True),
            'compress': resource_config.get('compress', True),
            'metadata_cache': True,  # Enable by default for performance
        }

        # Handle cache configuration
        if cache_config.get('enabled', False):
            new_resource_config['cache_ttl'] = cache_config.get('ttl', 3600)

        # Handle deprecated parameter names
        if 'resource_dirs' in resource_config:
            # Note: base_paths will be handled by the strategy constructor
            logger.warning("Detected 'resource_dirs' parameter. Consider updating to 'base_paths'.")

        # Preserve other configuration
        for key, value in resource_config.items():
            if key not in ['type', 'optimize', 'minify', 'compress'] and not key.startswith('_'):
                new_resource_config[key] = value

        new_config['resource'] = new_resource_config

        return new_config

    @staticmethod
    def create_migration_plan(current_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a detailed migration plan for transitioning to unified strategy.

        Args:
            current_config: Current resource configuration

        Returns:
            Dictionary containing migration plan and steps
        """
        detection_result = ResourceStrategyMigration.detect_legacy_configuration(current_config)

        migration_plan = {
            'migration_needed': detection_result['migration_needed'],
            'current_strategy': detection_result['current_strategy'],
            'target_strategy': 'unified',
            'steps': [],
            'estimated_complexity': 'low',
            'breaking_changes': [],
            'benefits': []
        }

        # Define migration steps based on current configuration
        resource_config = current_config.get('resource', {})
        strategy_type = resource_config.get('type', 'filesystem')

        if strategy_type == 'filesystem':
            migration_plan['steps'].extend([
                "1. Update 'type' from 'filesystem' to 'unified'",
                "2. Remove manual OptimizedResourceStrategy/CachedResourceStrategy wrapping",
                "3. Use built-in optimization and caching configuration"
            ])
            migration_plan['estimated_complexity'] = 'low'

        elif strategy_type == 'composite':
            migration_plan['steps'].extend([
                "1. Review composite strategy patterns",
                "2. Consider if unified strategy can replace some composite usage",
                "3. Update local resource strategies to use unified strategy"
            ])
            migration_plan['estimated_complexity'] = 'medium'

        # Add general steps
        migration_plan['steps'].extend([
            "4. Test resource loading functionality",
            "5. Verify caching and optimization behavior",
            "6. Update any direct strategy instantiation code"
        ])

        # Identify benefits
        migration_plan['benefits'] = [
            "Reduced complexity - no more strategy wrapping",
            "Better performance with integrated caching",
            "Consistent optimization across all resources",
            "Simplified configuration",
            "Better memory management for metadata caching"
        ]

        # Identify potential breaking changes
        if detection_result['has_legacy_patterns']:
            migration_plan['breaking_changes'] = [
                "Configuration format changes",
                "Strategy class imports may need updating",
                "Custom strategy wrapping code will need modification"
            ]

        return migration_plan

    @staticmethod
    def validate_migration(old_config: Dict[str, Any], new_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that a migration preserves essential functionality.

        Args:
            old_config: Original configuration
            new_config: Migrated configuration

        Returns:
            Dictionary containing validation results
        """
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'preserved_features': [],
            'new_features': []
        }

        old_resource = old_config.get('resource', {})
        new_resource = new_config.get('resource', {})
        old_cache = old_config.get('cache', {})

        # Validate essential features are preserved
        essential_features = ['follow_symlinks', 'optimize', 'minify', 'compress']
        for feature in essential_features:
            if feature in old_resource:
                if old_resource[feature] == new_resource.get(feature):
                    validation_result['preserved_features'].append(feature)
                else:
                    validation_result['warnings'].append(
                        f"Feature '{feature}' value changed: {old_resource[feature]} -> {new_resource.get(feature)}"
                    )

        # Check for new features
        if new_resource.get('metadata_cache', False) and not old_resource.get('metadata_cache', False):
            validation_result['new_features'].append("metadata_cache enabled")

        # Validate caching configuration
        if old_cache.get('enabled', False):
            if 'cache_ttl' not in new_resource:
                validation_result['warnings'].append("Cache was enabled but no cache_ttl specified in new config")
            else:
                validation_result['preserved_features'].append("caching")

        # Check for potential issues
        if new_resource.get('type') != 'unified':
            validation_result['errors'].append("Migration did not set strategy type to 'unified'")
            validation_result['valid'] = False

        return validation_result

    @staticmethod
    def generate_migration_report(config: Dict[str, Any]) -> str:
        """
        Generate a human-readable migration report.

        Args:
            config: Current configuration to analyze

        Returns:
            Formatted migration report as string
        """
        detection = ResourceStrategyMigration.detect_legacy_configuration(config)
        plan = ResourceStrategyMigration.create_migration_plan(config)
        new_config = ResourceStrategyMigration.convert_to_unified_config(config)
        validation = ResourceStrategyMigration.validate_migration(config, new_config)

        report_lines = [
            "Resource Strategy Migration Report",
            "=" * 40,
            "",
            f"Current Strategy: {detection['current_strategy']}",
            f"Migration Needed: {'Yes' if detection['migration_needed'] else 'No'}",
            f"Complexity: {plan['estimated_complexity']}",
            ""
        ]

        if detection['legacy_patterns']:
            report_lines.extend([
                "Legacy Patterns Detected:",
                *[f"  • {pattern}" for pattern in detection['legacy_patterns']],
                ""
            ])

        if detection['recommendations']:
            report_lines.extend([
                "Recommendations:",
                *[f"  • {rec}" for rec in detection['recommendations']],
                ""
            ])

        if plan['steps']:
            report_lines.extend([
                "Migration Steps:",
                *[f"  {step}" for step in plan['steps']],
                ""
            ])

        if plan['benefits']:
            report_lines.extend([
                "Benefits of Migration:",
                *[f"  • {benefit}" for benefit in plan['benefits']],
                ""
            ])

        if plan['breaking_changes']:
            report_lines.extend([
                "Potential Breaking Changes:",
                *[f"  ⚠️  {change}" for change in plan['breaking_changes']],
                ""
            ])

        # Add validation results
        if validation['valid']:
            report_lines.append("✅ Migration validation: PASSED")
        else:
            report_lines.append("❌ Migration validation: FAILED")
            for error in validation['errors']:
                report_lines.append(f"   Error: {error}")

        if validation['warnings']:
            report_lines.extend([
                "",
                "Warnings:",
                *[f"  ⚠️  {warning}" for warning in validation['warnings']]
            ])

        return "\n".join(report_lines)


def migrate_resource_config(config: Dict[str, Any],
                          auto_apply: bool = False,
                          show_report: bool = True) -> Tuple[Dict[str, Any], str]:
    """
    Convenience function to migrate resource configuration.

    Args:
        config: Current configuration dictionary
        auto_apply: Whether to automatically apply the migration
        show_report: Whether to generate and return a migration report

    Returns:
        Tuple of (migrated_config, migration_report)
    """
    migration = ResourceStrategyMigration()

    # Generate report
    report = ""
    if show_report:
        report = migration.generate_migration_report(config)

    # Perform migration
    if auto_apply:
        new_config = migration.convert_to_unified_config(config)
        if show_report:
            print(report)
        return new_config, report
    else:
        if show_report:
            print(report)
        return config, report


# Example usage and testing functions
def example_legacy_config() -> Dict[str, Any]:
    """Return an example legacy configuration for testing."""
    return {
        'resource': {
            'type': 'filesystem',
            'resource_dirs': ['/path/to/resources'],  # Deprecated parameter name
            'optimize': True,
            'minify': True,
            'compress': False,
            'follow_symlinks': True
        },
        'cache': {
            'enabled': True,
            'type': 'memory',
            'ttl': 7200
        }
    }


def example_migration_demo():
    """Demonstrate the migration process."""
    legacy_config = example_legacy_config()

    print("Legacy Configuration Migration Demo")
    print("=" * 50)

    # Analyze and migrate
    migrated_config, report = migrate_resource_config(
        legacy_config,
        auto_apply=True,
        show_report=True
    )

    print("\n" + "=" * 50)
    print("Original Config:")
    print(legacy_config)

    print("\nMigrated Config:")
    print(migrated_config)


if __name__ == "__main__":
    example_migration_demo()
