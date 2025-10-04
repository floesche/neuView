# neuView Utility Scripts

This directory contains utility scripts for the neuView system.

## Current Scripts

### Version Management
- **`increment_version.py`**: Automatically increments project version and creates git tags
  ```bash
  python scripts/increment_version.py [--dry-run]
  ```

### Batch Processing  
- **`extract_and_fill.py`**: Extracts neuron types from config files and runs fill-queue commands
  ```bash
  python scripts/extract_and_fill.py [config_file] [test_category]
  ```

## Documentation

**For comprehensive documentation about neuView development patterns, including:**
- Dynamic ROI system implementation
- Cache management patterns  
- Script lifecycle management
- ROI ID collision fixes
- Jinja template processing

**Please refer to the main documentation:**
- **Developer Guide**: `docs/developer-guide.md`
- **User Guide**: `docs/user-guide.md`

All technical documentation has been consolidated into the main docs for better discoverability and maintenance.

## Script Management Guidelines

### Permanent vs Temporary Scripts
- **Keep**: Reusable utilities, maintenance tools, ongoing development scripts
- **Remove**: One-off debugging scripts, issue-specific investigations, completed migration tools

### Adding New Scripts
When adding utility scripts:

1. **Determine Permanence**: Will this be used repeatedly or is it one-time?
2. **Document Purpose**: Include clear docstrings and usage examples
3. **Follow Patterns**: Use established naming and structure conventions
4. **Clean Up**: Remove temporary scripts after completing their purpose

### Documentation Pattern
All permanent scripts should include:
```python
#!/usr/bin/env python3
"""
Script Name: Brief Description

Purpose: What this script does and when to use it
Usage: python scripts/script_name.py [options]
Requirements: Any special dependencies or setup
"""
```

## Prerequisites

Scripts in this directory typically require:
- neuView installed and configured
- Project dependencies installed via pixi
- Appropriate configuration files

```bash
# Ensure neuView is set up
python -m neuview --help
```

---

*Clean and focused utility scripts for neuView - see main docs for comprehensive technical information*