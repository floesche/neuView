# Migration Guide: New CLI Architecture

## Overview

QuickPage has been upgraded to use a modern Domain-Driven Design (DDD) architecture with an improved CLI interface. The old CLI has been replaced with a new, more powerful version that maintains backward compatibility while adding new features.

## What Changed

### ✅ CLI Commands (Fully Compatible)

The core CLI commands work the same way, but with enhanced capabilities:

```bash
# These commands work exactly as before:
quickpage generate --neuron-type Dm4
quickpage test-connection
python -m quickpage generate --neuron-type LC10a

# But now you also get new features:
quickpage list-types --sorted --show-statistics
quickpage inspect Dm4
quickpage generate --neuron-type Dm4 --soma-side left --no-connectivity
```

### 🆕 New Commands

Several new commands have been added:

- `quickpage inspect <neuron-type>` - Detailed analysis of a neuron type
- `quickpage list-types` - Enhanced neuron type discovery with filtering
- Enhanced `generate` command with more options
- Better `test-connection` with detailed output

### 🏗️ Architecture Improvements

- **Async Operations**: All operations are now async for better performance
- **Result Pattern**: Explicit error handling instead of exceptions
- **Better Caching**: Intelligent caching of neuron data
- **Type Safety**: Rich domain model with compile-time type checking

## Migration Steps

### For Most Users: No Action Required

If you were using the CLI commands directly, everything should work exactly as before:

```bash
# This still works exactly the same
quickpage generate --neuron-type Dm4
python -m quickpage --help
pixi run quickpage generate
```

### For Advanced Users: New Capabilities Available

You can now use enhanced features:

```bash
# New inspection capabilities
quickpage inspect Dm4 --soma-side left

# Better type discovery
quickpage list-types --sorted --max-results 20 --show-soma-sides

# More generation options
quickpage generate --neuron-type LC10a --no-connectivity

# Verbose output for debugging
quickpage --verbose generate --neuron-type Dm4
```

### For Developers: Programmatic API Enhanced

The programmatic API has been significantly improved while maintaining backward compatibility:

```python
# Old way still works (legacy compatibility)
from quickpage import Config, NeuPrintConnector, PageGenerator

# New way with DDD architecture
from quickpage import (
    NeuronTypeName, SomaSide, GeneratePageCommand,
    PageGenerationService, Result, Ok, Err
)

# Rich domain model
neuron_type = NeuronTypeName("Dm4")
soma_side = SomaSide("left") 
command = GeneratePageCommand(neuron_type=neuron_type, soma_side=soma_side)

# Explicit error handling
result = await service.generate_page(command)
if result.is_ok():
    print(f"Success: {result.unwrap()}")
else:
    print(f"Error: {result.error}")
```

## New Pixi Tasks

Several convenience tasks have been added:

```bash
pixi run generate-dm4      # Generate page for Dm4
pixi run list-types        # List available neuron types
pixi run test-connection   # Test NeuPrint connection
pixi run inspect-dm4       # Inspect Dm4 statistics
```

## Configuration Changes

### ✅ No Breaking Changes

Your existing `config.yaml` files work exactly as before. No changes needed.

### 🆕 New Configuration Options Available

You can now use additional configuration options:

```yaml
# New optional settings
discovery:
  max_types: 20
  randomize: true
  type_filter: "LC.*"
  exclude_types: ["Unknown", "Unclear"]

output:
  generate_json: true
  include_3d_view: true
```

## File Structure

The new architecture organizes code better but doesn't break existing usage:

```
quickpage/src/quickpage/
├── core/                    # New: Domain layer
├── application/             # New: Application services  
├── infrastructure/          # New: Infrastructure adapters
├── shared/                  # New: Shared utilities
├── cli.py                   # Updated: Modern CLI
├── config.py                # Same: No breaking changes
├── neuprint_connector.py    # Same: Legacy compatibility
└── page_generator.py        # Same: Legacy compatibility
```

## Troubleshooting

### Issue: Command not found after update

**Solution**: Make sure you're using the latest version:
```bash
pixi install
pixi run quickpage --help
```

### Issue: Different output format

The new CLI provides more detailed and structured output. If you were parsing CLI output in scripts, you might need to adjust for the improved format.

**Before**:
```
Generated: output/Dm4_L.html
```

**After**:
```
✓ Generated: output/Dm4_left.html, JSON: output/.data/Dm4_left.json
```

### Issue: Performance differences

The new CLI includes caching and async operations, so it might behave slightly differently:
- First runs may be slower (building cache)
- Subsequent runs will be faster (using cache)
- Bulk operations are now concurrent and much faster

## Rollback (If Needed)

If you need to use the old CLI for any reason, it's still available as `cli_legacy.py`:

```bash
# Use the legacy CLI (not recommended)
python -m quickpage.cli_legacy --help
```

However, we recommend using the new CLI as it provides the same functionality with improvements.

## Getting Help

- Use `quickpage --help` to see all available commands
- Use `quickpage <command> --help` for command-specific help
- Enable verbose mode with `--verbose` for debugging
- Check the README.md for detailed usage examples

## Summary

✅ **Backward Compatible**: Existing commands work the same way
🆕 **New Features**: Enhanced commands and capabilities  
🚀 **Better Performance**: Async operations and caching
🏗️ **Modern Architecture**: Clean, maintainable, testable code
📚 **Better Documentation**: Comprehensive help and examples

The migration is seamless for most users, and the new features are available when you need them.