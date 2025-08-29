# QuickPage Performance Analysis and Optimization

This directory contains comprehensive performance analysis tools, reports, and optimizations for the QuickPage system, with a focus on the `quickpage pop` command optimization.

## Directory Structure

```
performance/
├── README.md                    # This file
├── scripts/                     # Performance analysis and profiling scripts
│   ├── analyze_pop_performance.py       # Comprehensive pop command analysis
│   ├── profile_pop_command.py           # Basic pop command profiling
│   ├── profile_pop_detailed.py          # Detailed instrumented profiling
│   ├── profile_bulk_generation.py       # Bulk generation performance analysis
│   ├── profile_realistic_bulk.py        # Realistic bulk scenario profiling
│   ├── profile_soma_cache.py             # Soma cache performance analysis
│   └── performance_comparison.py        # Performance comparison utilities
├── reports/                     # Analysis reports and documentation
│   ├── QUICKPAGE_POP_PERFORMANCE_OPTIMIZATION_REPORT.md  # Main optimization report
│   ├── SOMA_CACHE_OPTIMIZATION_REPORT.md                 # Soma cache analysis
│   └── OPTIMIZATION_IMPLEMENTATION_COMPLETE.md           # Implementation status
└── data/                        # Performance data and logs
    ├── pop_performance_analysis.json      # Latest comprehensive analysis
    ├── detailed_pop_performance_report.json
    ├── pop_performance_report.json
    └── pop_detailed_profile.log
```

## Key Performance Findings

### Current Performance (Baseline)
- **Throughput**: 0.16 operations/second
- **Average Execution Time**: 6.26 seconds per operation
- **Queue Processing Time**: 19.6 hours for 11,287 files
- **Database Queries**: 21 per operation
- **Cache Hit Rate**: 100% (existing cache)

### Identified Bottlenecks
1. **🔴 CRITICAL**: Sequential processing architecture
2. **🔴 CRITICAL**: Excessive database queries (21 per operation)
3. **🟡 MEDIUM**: Service initialization overhead (4.1%)
4. **🟡 MEDIUM**: Redundant cache I/O operations

## Optimization Strategy

### Phase 1: Immediate Optimizations (0-2 weeks)
- [x] **Soma Cache Optimization**: 50% reduction in cache I/O (IMPLEMENTED)
- [ ] **Batch Processing**: 3-5x throughput improvement
- [ ] **Database Connection Pooling**: 15-25% query overhead reduction

**Expected Result**: 0.16 → 1.0 ops/sec (6x improvement)

### Phase 2: Architecture Enhancement (2-6 weeks)
- [ ] **Service Daemon Mode**: Eliminate command overhead
- [ ] **Advanced Caching**: Query result caching
- [ ] **Async Pipeline**: Convert to async/await architecture

**Expected Result**: 1.0 → 2.5 ops/sec (2.5x additional improvement)

### Phase 3: Advanced Features (6-12 weeks)
- [ ] **Pre-computation**: Off-peak data processing
- [ ] **Incremental Updates**: Smart regeneration
- [ ] **Memory Optimization**: Template and data caching

**Expected Result**: 2.5 → 5.0 ops/sec (2x additional improvement)

## Quick Start

### Running Performance Analysis

```bash
# Comprehensive pop command analysis
cd quickpage
python performance/scripts/analyze_pop_performance.py

# Basic profiling
python performance/scripts/profile_pop_command.py

# Detailed instrumented profiling
python performance/scripts/profile_pop_detailed.py
```

### Key Scripts

| Script | Purpose | Output |
|--------|---------|--------|
| `analyze_pop_performance.py` | **Main analysis tool** - Comprehensive performance analysis with optimization recommendations | `performance/data/pop_performance_analysis.json` |
| `profile_pop_command.py` | Basic pop command profiling with timing and throughput metrics | `pop_performance_report.json` |
| `profile_pop_detailed.py` | Detailed instrumented profiling with component-level timing | `detailed_pop_performance_report.json` |
| `profile_bulk_generation.py` | Bulk generation scenario analysis | Console output + logs |
| `profile_soma_cache.py` | Soma cache optimization analysis | Console output |

### Prerequisites

```bash
# Ensure queue files exist
python -m quickpage fill-queue

# Verify queue status
ls -la output/.queue/*.yaml | wc -l
```

## Implementation Status

### ✅ Completed Optimizations

#### Soma Cache Optimization (DEPLOYED)
- **Status**: Implementation complete and validated
- **Impact**: 50% reduction in cache I/O operations
- **Files Affected**: `src/quickpage/neuprint_connector.py`
- **Validation**: 100% data consistency, zero regressions
- **Cleanup**: `scripts/cleanup_redundant_cache.py` available

### 🚧 In Progress

#### Batch Processing Implementation
- **Priority**: HIGH
- **Expected Impact**: 3-5x throughput improvement
- **Implementation**: Add `--batch N` option to pop command
- **Status**: Design complete, implementation pending

### 📋 Planned Optimizations

1. **Database Connection Pooling** (Priority: HIGH)
2. **Service Daemon Mode** (Priority: MEDIUM)
3. **Async Processing Pipeline** (Priority: MEDIUM)
4. **Pre-computation System** (Priority: LOW)

## Performance Monitoring

### Key Metrics to Track

```bash
# Throughput monitoring
watch -n 60 'find output/.queue -name "*.yaml" | wc -l'

# Performance benchmarking
time python -m quickpage pop

# Cache performance
grep "cache.*hit\|cache.*miss" logs/*.log | wc -l
```

### Success Criteria

**Phase 1 Targets**:
- [ ] Throughput ≥ 0.8 ops/sec
- [ ] Average time ≤ 1.5s per operation
- [ ] Cache hit rate ≥ 95%
- [ ] Zero functionality regressions

**Long-term Targets**:
- [ ] Throughput ≥ 4.0 ops/sec
- [ ] Queue processing ≤ 1 hour (11K+ files)
- [ ] Database queries ≤ 5 per operation

## Usage Examples

### Basic Performance Analysis
```bash
# Run comprehensive analysis on 15 operations
python performance/scripts/analyze_pop_performance.py

# View results
cat performance/data/pop_performance_analysis.json | jq '.statistics.timing'
```

### Custom Profiling
```bash
# Profile specific number of operations
python performance/scripts/profile_pop_command.py --count 25

# Profile with custom timeout
python performance/scripts/profile_pop_detailed.py --timeout 600
```

### Optimization Validation
```bash
# Verify soma cache optimization is working
python scripts/verify_optimization.py

# Compare performance before/after optimization
python performance/scripts/performance_comparison.py
```

## Troubleshooting

### Common Issues

**No queue files available**:
```bash
python -m quickpage fill-queue
```

**Performance regression**:
```bash
# Check optimization status
python scripts/verify_optimization.py

# Revert to fallback if needed
git checkout HEAD~1 src/quickpage/neuprint_connector.py
```

**High memory usage**:
```bash
# Monitor memory during profiling
python performance/scripts/profile_pop_detailed.py --memory-monitoring
```

## Contributing

### Adding New Performance Analysis

1. Create script in `performance/scripts/`
2. Output data to `performance/data/`
3. Update this README with usage instructions
4. Add to `.gitignore` if generating large data files

### Reporting Performance Issues

Include:
- System information (Python version, OS)
- Queue size and characteristics
- Performance metrics (throughput, timing)
- Error logs if applicable

## References

- [Main Optimization Report](reports/QUICKPAGE_POP_PERFORMANCE_OPTIMIZATION_REPORT.md)
- [Soma Cache Analysis](reports/SOMA_CACHE_OPTIMIZATION_REPORT.md)
- [Implementation Status](reports/OPTIMIZATION_IMPLEMENTATION_COMPLETE.md)

---

*Last Updated: January 2025*  
*Performance Baseline: 0.16 ops/sec*  
*Optimization Target: 5.0 ops/sec*