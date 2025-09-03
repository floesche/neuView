# Cache Manifest Refactoring Summary

## Overview
Refactored the queue system to properly reflect the caching nature of the central manifest file. The `queue.yaml` file was functioning more as a cache/registry of processed neuron types rather than an actual queue, so the file handling has been updated accordingly.

## Changes Made

### File Location and Format Changes
- **Moved**: `output/.queue/queue.yaml` → `output/.cache/manifest.json`
- **Format Change**: YAML → JSON for better performance and consistency with other cache files
- **Purpose**: Better reflects the file's function as a cache manifest of processed neuron types

### Method Renaming
- `update_queue_manifest()` → `update_cache_manifest()`
- `load_queued_neuron_types()` → `load_cached_neuron_types()`
- `get_queued_neuron_types()` → `get_cached_neuron_types()`
- `_load_queued_neuron_types()` → `_load_cached_neuron_types()`

### Variable Renaming
- `_queued_types` → `_cached_types`
- `queued_types` → `cached_types`
- `queue_neurons` → `cached_neurons`

### Files Modified

#### Core Services
- `src/quickpage/services/queue_file_manager.py`
  - Updated manifest file path and method names
  - Improved comments to reflect caching nature
  
- `src/quickpage/core_services.py`
  - Updated QueueService to use new cache-focused method names
  - Updated variable names and comments

#### Processing Components
- `src/quickpage/services/queue_processor.py`
  - Simplified queue file discovery since cache manifest moved out of queue directory
  - Updated status reporting to reference manifest file in new location

- `src/quickpage/services/index_service.py`
  - Updated to read from `manifest.json` in `.cache` directory
  - Updated to use JSON parsing instead of YAML
  - Updated variable names to reflect caching nature

#### Utilities
- `src/quickpage/services/neuron_search_service.py`
  - Updated to use new cache method name

- `src/quickpage/utils/html_utils.py`
  - Updated to use new cache method name and variable names

#### Performance Scripts
- `performance/scripts/profile_pop_detailed.py`
  - Simplified queue file discovery since cache manifest moved out of queue directory

#### CLI and Documentation
- `src/quickpage/cli.py`
  - Updated command description to mention JSON cache manifest
  - Updated success messages

- `docs/developer-guide.md`
  - Updated references to manifest.json

- `docs/user-guide.md`
  - Updated file structure documentation to show manifest in .cache directory
  - Updated troubleshooting references
  - Updated search data sources documentation

### Migration
- Existing `queue.yaml` files are automatically migrated to `manifest.json` in `.cache` directory
- Format converted from YAML to JSON
- No data structure changes - only file location, format, and method semantics

### System Behavior
The queue system now properly distinguishes between:

1. **Individual Queue Files**: `.queue/*.yaml` files
   - Contain work items for the `pop` command to process
   - Function as a proper work queue

2. **Cache Manifest**: `.cache/manifest.json`
   - Contains registry of processed neuron types in JSON format
   - Functions as a cache/lookup index
   - Located in the proper cache directory
   - Used by search and indexing systems

### Benefits
- **Clearer Semantics**: File and method names now accurately reflect their purpose
- **Better Organization**: Cache manifest is now in the proper `.cache` directory
- **Improved Performance**: JSON format is faster to parse than YAML
- **Better Understanding**: Distinction between queue files and cache manifest is now explicit
- **Improved Maintainability**: Code is more self-documenting
- **Consistent Terminology**: Eliminates confusion between queueing and caching concepts
- **Format Consistency**: All cache files now use JSON format

### Backward Compatibility
- Existing `queue.yaml` files are migrated to `manifest.json` in `.cache` directory
- CLI command names remain unchanged for user compatibility
- Individual queue file processing remains unchanged
- All functionality preserved while improving internal consistency

### Testing
- Verified that cached neuron types load correctly from manifest.json
- Confirmed queue processing works correctly with manifest moved out of queue directory
- Validated that the fill-queue command updates the cache manifest correctly
- Tested queue status reporting with new manifest location