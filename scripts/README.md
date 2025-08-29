# QuickPage Utility Scripts

This directory contains utility scripts for optimization, testing, and maintenance of the QuickPage system.

## Directory Contents

### Cache Optimization Scripts
- **`cleanup_redundant_cache.py`** - Remove redundant soma cache files after optimization
- **`investigate_consistency.py`** - Verify data consistency between cache systems
- **`optimization_implementation.py`** - Soma cache optimization implementation demo
- **`verify_optimization.py`** - Validate that optimizations are working correctly

### Testing and Validation Scripts
- **`test_optimization.py`** - Test optimization implementations
- **`realistic_bulk_test.py`** - Test realistic bulk generation scenarios

## Quick Reference

### Cache Management

```bash
# Verify optimization is working
python scripts/verify_optimization.py

# Check data consistency
python scripts/investigate_consistency.py

# Clean up redundant cache files (after optimization)
python scripts/cleanup_redundant_cache.py --dry-run
python scripts/cleanup_redundant_cache.py --confirm
```

### Testing

```bash
# Test optimizations
python scripts/test_optimization.py

# Run realistic bulk test
python scripts/realistic_bulk_test.py
```

## Script Details

### cleanup_redundant_cache.py
Safely removes redundant soma cache files after the soma cache optimization has been deployed.

**Usage**:
```bash
# Preview what will be deleted
python scripts/cleanup_redundant_cache.py --dry-run

# Actually delete the files
python scripts/cleanup_redundant_cache.py --confirm
```

**Features**:
- Validates optimization is working before deletion
- Creates backup of files before deletion
- Reports space savings
- Safe execution with confirmation prompts

### verify_optimization.py
Validates that the soma cache optimization is functioning correctly.

**Usage**:
```bash
python scripts/verify_optimization.py
```

**Checks**:
- Optimization is active
- Cache hit rates are good
- No fallback to old cache system
- Data consistency is maintained

### investigate_consistency.py
Compares data between different cache systems to ensure consistency.

**Usage**:
```bash
python scripts/investigate_consistency.py
```

**Validates**:
- Soma cache vs neuron cache data consistency
- Data format conversions
- Edge cases and error handling

## Prerequisites

Most scripts require:
- QuickPage installed and configured
- Cache files present in `output/.cache/`
- Active queue files (for some tests)

```bash
# Ensure cache and queue are ready
python -m quickpage cache build
python -m quickpage fill-queue
```

## Safety Features

All scripts include:
- **Dry-run modes** for safe preview
- **Validation checks** before making changes
- **Backup creation** for reversible operations
- **Error handling** and detailed logging
- **Confirmation prompts** for destructive operations

## Integration with Performance Analysis

These scripts work together with the performance analysis tools:

```bash
# Full optimization workflow
python scripts/verify_optimization.py          # Check current status
python performance/scripts/analyze_pop_performance.py  # Baseline performance
python scripts/cleanup_redundant_cache.py --confirm    # Clean up if ready
python performance/scripts/analyze_pop_performance.py  # Verify improvement
```

## Troubleshooting

### Common Issues

**Script can't find quickpage module**:
```bash
# Run from project root directory
cd /path/to/quickpage
python scripts/script_name.py
```

**No cache files found**:
```bash
# Build cache first
python -m quickpage cache build
```

**Optimization not detected**:
```bash
# Check if optimization code is deployed
grep -n "get_soma_sides_from_neuron_cache" src/quickpage/neuprint_connector.py
```

### Getting Help

Each script has built-in help:
```bash
python scripts/script_name.py --help
```

For performance-related scripts, see: `performance/README.md`

---

*Utility Scripts for QuickPage Optimization and Maintenance*