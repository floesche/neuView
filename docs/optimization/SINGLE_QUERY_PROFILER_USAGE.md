# Single Query Profiler Usage Guide

A simple, focused tool for profiling individual NeuPrint queries. Perfect for testing specific queries and measuring their performance in isolation.

## Quick Start

### Prerequisites
```bash
pip install pandas pyyaml neuprint-python python-dotenv
```

### Setup
1. Make sure you have a `.env` file with your token:
   ```bash
   echo "NEUPRINT_TOKEN=your-actual-token-here" > .env
   ```

2. Use your existing config file or create one:
   ```yaml
   neuprint:
     server: "neuprint.janelia.org"
     dataset: "hemibrain:v1.2.1"
   ```

### Basic Usage
```bash
# Profile a simple query
python single_query_profiler.py --config config.yaml --query "MATCH (n:Neuron) RETURN count(n)"

# Run a query multiple times for better statistics
python single_query_profiler.py --config config.yaml --query "MATCH (n:Neuron) WHERE n.type = 'T4' RETURN n.bodyId LIMIT 10" --runs 5

# Use a query from a file
python single_query_profiler.py --config config.yaml --query-file example_queries/neuron_count.cypher
```

## Command Line Options

```
Connection Options:
  --config, -c PATH        Path to config YAML file
  --server URL             NeuPrint server URL  
  --dataset, -d NAME       Dataset name (required with --server)
  --token, -t TOKEN        Authentication token (optional if in .env)

Query Options:
  --query, -q QUERY        Cypher query to execute
  --query-file, -f FILE    File containing Cypher query

Profiling Options:
  --runs, -r NUM           Number of times to run query [default: 1]
  --description DESC       Description of the query
  --no-validation         Skip query validation
  --verbose, -v           Verbose output
```

## Example Use Cases

### 1. Test a New Query
```bash
python single_query_profiler.py \
  --config config.yaml \
  --query "MATCH (n:Neuron) WHERE n.type = 'LC10' RETURN n.bodyId, n.size ORDER BY n.size DESC LIMIT 5" \
  --description "Find largest LC10 neurons"
```

### 2. Performance Testing with Multiple Runs
```bash
python single_query_profiler.py \
  --config config.yaml \
  --query-file example_queries/connectivity_summary.cypher \
  --runs 10 \
  --description "Connectivity analysis performance test"
```

### 3. Compare Query Performance
```bash
# Test basic query
python single_query_profiler.py --config config.yaml --query "MATCH (n:Neuron) RETURN count(n)" --runs 5

# Test complex query  
python single_query_profiler.py --config config.yaml --query-file example_queries/roi_analysis.cypher --runs 3
```

### 4. Direct Connection (No Config File)
```bash
python single_query_profiler.py \
  --server neuprint.janelia.org \
  --dataset "optic-lobe:v1.0" \
  --query "MATCH (n:Neuron) WHERE n.status = 'Traced' RETURN n.type, count(n) ORDER BY count(n) DESC LIMIT 10" \
  --runs 3
```

## Example Queries

The `example_queries/` directory contains sample queries:

### Basic Queries
- `neuron_count.cypher` - Count total neurons
- `t4_neurons.cypher` - Get T4 neuron information

### Advanced Queries  
- `connectivity_summary.cypher` - Analyze connections between neuron types
- `roi_analysis.cypher` - Analyze neuron distribution across brain regions

### Using Example Queries
```bash
# Count neurons
python single_query_profiler.py --config config.yaml --query-file example_queries/neuron_count.cypher

# Analyze T4 neurons
python single_query_profiler.py --config config.yaml --query-file example_queries/t4_neurons.cypher --runs 3

# Complex connectivity analysis
python single_query_profiler.py --config config.yaml --query-file example_queries/connectivity_summary.cypher --runs 2
```

## Output Explanation

The profiler provides detailed performance metrics:

```
==============================================================
RESULTS
==============================================================
Success Rate:     100.0%
Average Time:     2.456s
Median Time:      2.401s
Min/Max Time:     2.234s / 2.678s
Std Deviation:    0.187s
Average Results:  143

Performance Assessment:
  ⚡ Moderate query (1-5s)
```

### Key Metrics
- **Success Rate**: Percentage of successful query executions
- **Average/Median Time**: Central tendency of execution times
- **Min/Max Time**: Range of execution times
- **Std Deviation**: Measure of timing consistency
- **Average Results**: Number of results returned

### Performance Categories
- ✅ **Fast** (< 1s): Suitable for real-time applications
- ⚡ **Moderate** (1-5s): Good for interactive use
- 🐌 **Slow** (5-30s): May need optimization
- 🚨 **Very Slow** (> 30s): Requires optimization or caching

### Warning Indicators
- ⚠️ **Low success rate**: Query may have issues
- ⚠️ **High variability**: Inconsistent performance (caching effects)

## Creating Your Own Query Files

### Simple Query File
```cypher
// my_query.cypher
MATCH (n:Neuron)
WHERE n.type IN ['T4', 'T5']
RETURN n.bodyId, n.type, n.size
ORDER BY n.size DESC
LIMIT 20
```

### Complex Query File
```cypher
// complex_analysis.cypher
// Multi-step pathway analysis
MATCH path = (n1:Neuron)-[c1:ConnectsTo]->(n2:Neuron)-[c2:ConnectsTo]->(n3:Neuron)
WHERE n1.type = 'T4' AND n2.type = 'Mi1' AND n3.type = 'T5'
  AND c1.weight > 10 AND c2.weight > 10
RETURN n1.bodyId, n2.bodyId, n3.bodyId, c1.weight, c2.weight
ORDER BY c1.weight + c2.weight DESC
LIMIT 50
```

## Safety Features

### Query Validation
The profiler automatically checks for:
- Basic Cypher syntax
- Potentially dangerous write operations (DELETE, CREATE, etc.)
- Empty queries

### Safeguards
- Warns about write operations and asks for confirmation
- Limits on number of runs (asks confirmation for > 20 runs)
- Connection testing before query execution

### Skip Validation
```bash
# Skip safety checks (use carefully)
python single_query_profiler.py --config config.yaml --query "..." --no-validation
```

## Troubleshooting

### Connection Issues
```bash
# Test basic connectivity
python single_query_profiler.py --config config.yaml --query "RETURN 1" --description "Connection test"
```

### Token Issues
```bash
# Check if token is loaded
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
token = os.getenv('NEUPRINT_TOKEN')
print(f'Token found: {bool(token)}')
if token: print(f'Token length: {len(token)}')
"
```

### Query Syntax Issues
- Use `--verbose` flag for detailed error messages
- Test queries in the NeuPrint web interface first
- Start with simple queries and add complexity gradually

### Performance Issues
- Use fewer runs for slow queries
- Add `LIMIT` clauses to large result sets
- Consider using `EXPLAIN` in NeuPrint web interface to understand query execution

## Integration Tips

### Development Workflow
1. **Write query** in NeuPrint web interface
2. **Test performance** with single query profiler
3. **Optimize** if needed
4. **Integrate** into your application

### Performance Benchmarking
```bash
# Create a benchmark script
#!/bin/bash
echo "Benchmarking key queries..."

python single_query_profiler.py --config config.yaml --query-file queries/basic_count.cypher --runs 5
python single_query_profiler.py --config config.yaml --query-file queries/type_summary.cypher --runs 3  
python single_query_profiler.py --config config.yaml --query-file queries/connectivity.cypher --runs 2

echo "Benchmark complete!"
```

### CI/CD Integration
```bash
# Add to CI pipeline for performance regression testing
python single_query_profiler.py \
  --config ci_config.yaml \
  --query-file critical_queries/user_dashboard.cypher \
  --runs 3 \
  --description "Dashboard query performance test"
```

## Comparison with Full Profiler

| Feature | Single Query Profiler | Full Profiler |
|---------|----------------------|---------------|
| **Use Case** | Test specific queries | Compare multiple query types |
| **Setup** | Minimal | More comprehensive |
| **Output** | Focused metrics | Detailed analysis + plots |
| **Speed** | Fast | Slower (many queries) |
| **Best For** | Development/debugging | Performance analysis |

Choose the single query profiler when you want to:
- Test a specific query you're developing
- Debug performance issues with a particular query
- Quickly measure execution time
- Validate query syntax and performance

Choose the full profiler when you want to:
- Compare different types of queries
- Generate comprehensive performance reports
- Create visualizations
- Analyze overall database performance