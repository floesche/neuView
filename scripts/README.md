# neuView Utility Scripts

This directory contains utility scripts for the neuView system.

## Directory Status

The scripts directory has been cleaned up to remove one-off debugging and demonstration scripts that were created for specific purposes like system migrations, cache optimizations, and issue investigations.

### Removed Scripts

The following one-off debugging and verification scripts have been removed:
- Cache optimization testing scripts
- System migration verification scripts (Option B/C)
- Data consistency investigation scripts
- One-time performance testing scripts

These scripts served their purpose during development and debugging phases but are no longer needed for ongoing maintenance.

## Adding New Scripts

When adding utility scripts to this directory, consider:

### Permanent vs Temporary Scripts
- **Keep**: Scripts for ongoing maintenance, regular operations, or reusable utilities
- **Remove**: One-off debugging scripts, migration helpers, or issue-specific investigations

### Script Categories to Keep
- Regular maintenance utilities
- Reusable development tools
- System health checks
- Data migration tools (for ongoing use)
- Performance monitoring scripts

### Script Categories to Remove After Use
- One-time migration scripts
- Debugging scripts for specific issues
- Verification scripts for completed work
- Testing scripts for specific features

## Best Practices

1. **Document temporary scripts**: If creating debugging scripts, clearly mark them as temporary
2. **Clean up after completion**: Remove debugging scripts once the issue is resolved
3. **Use descriptive names**: Make it clear what each script does and whether it's permanent
4. **Include usage documentation**: Document how to use any permanent scripts

## Prerequisites

Scripts in this directory typically require:
- neuView installed and configured
- Appropriate cache files and data
- Project dependencies installed

```bash
# Ensure neuView is set up
python -m neuview --help
```

---

*Clean and focused utility scripts for neuView*