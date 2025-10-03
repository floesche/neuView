# neuView

A modern Python CLI tool that generates beautiful HTML pages for neuron types using data from NeuPrint. Built with Domain-Driven Design (DDD) architecture for maintainability and extensibility.

## ✨ Features

- **🔌 NeuPrint Integration**: Direct data fetching with intelligent caching
- **📱 Modern Web Interface**: Responsive design with advanced filtering
- **⚡ High Performance**: Up to 97.9% speed improvement with persistent caching
- **🧠 Multi-Dataset Support**: Automatic adaptation for CNS, Hemibrain, Optic-lobe
- **🎨 Beautiful Reports**: Clean, accessible HTML pages with interactive features
- **🔍 Advanced Search**: Real-time filtering by cell count, neurotransmitter, brain regions
- **📊 Rich Analytics**: Hemisphere balance, connectivity stats, ROI summaries

## 🚀 Quick Start

1. **Install dependencies:**
```bash
git clone <repository-url>
cd neuview
pixi install
```

2. **Set up your NeuPrint token:**
```bash
pixi run setup-env
# Edit .env and add your NeuPrint token
```

3. **Generate your first neuron page:**
```bash
neuview generate -n Dm4
```

4. **View results:**
Open `output/index.html` in your browser

## 📁 Project Structure

```
neuview/
├── src/neuview/             # Core application code
├── docs/                    # User and developer documentation
├── config/                  # Configuration files
├── scripts/                 # Utility and maintenance scripts
├── performance/             # Performance analysis and optimization
│   ├── scripts/            # Profiling and analysis tools
│   ├── reports/            # Performance reports and documentation
│   └── data/               # Performance data and logs
├── templates/              # HTML templates
├── static/                 # Static web assets
├── test/                   # Test files and outputs
└── output/                 # Generated HTML pages and cache
```

## 📖 Documentation

- **[User Guide](docs/user-guide.md)** - Installation, configuration, usage, and troubleshooting
- **[Developer Guide](docs/developer-guide.md)** - Architecture, development setup, and contribution guidelines
- **[Performance Analysis](performance/README.md)** - Performance optimization and profiling tools

## ⚡ Performance Optimization

neuView has been extensively optimized for high-throughput processing:

- **31x Performance Improvement**: From 0.16 to 5.0 operations/second
- **Soma Cache Optimization**: 50% reduction in cache I/O operations (deployed)
- **Batch Processing**: Process multiple queue files efficiently
- **Database Connection Pooling**: Reduced query overhead
- **Comprehensive Profiling**: Detailed performance analysis tools

See [Performance Reports](performance/reports/) for detailed analysis and optimization strategies.

## 🏗️ Architecture

neuView is built using modern software engineering principles:

- **Domain-Driven Design (DDD)** with clean architecture
- **CQRS Pattern** for maintainable command/query separation
- **Result Pattern** for explicit error handling
- **Persistent Caching** for optimal performance
- **Async Processing** for improved throughput
- **Responsive Frontend** with advanced filtering capabilities

## 📊 Performance

- **Cache Hit Rates**: Up to 88.9% for ROI hierarchy, 80.6% for column queries
- **Speed Improvements**: 97.9% faster on subsequent runs
- **Cross-session Benefits**: Persistent cache survives restarts
- **Database Load Reduction**: Significant decrease in redundant queries

## 🧪 Testing

```bash
# Run all tests (unit + integration)
pixi run test

# Run all tests with verbose output
pixi run test-verbose

# Run tests with coverage
pixi run test-coverage

# Test NeuPrint connection
neuview test-connection

# Generate test data
pixi run test-set
```

## 🔄 CI/CD

The project includes automated testing workflows:

- **Unit Tests**: Fast, isolated tests for individual components
- **Integration Tests**: End-to-end tests for component interactions
- **Code Quality**: Linting and formatting checks with Ruff
- **Multi-environment**: Tests run in clean pixi environments

### GitHub Actions Workflows

- `.github/workflows/test.yml` - Simple unit test execution on every push
- `.github/workflows/ci.yml` - Comprehensive CI with tests, coverage, and linting

The workflows use pixi for consistent dependency management and testing environments.

## 🤝 Contributing

We welcome contributions! Please see our comprehensive documentation:

- **[Developer Guide](docs/developer-guide.md)** - Architecture, development setup, and coding standards
- **[Performance Analysis](performance/README.md)** - Optimization tools and profiling
- **[Utility Scripts](scripts/README.md)** - Maintenance and testing tools

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **User Documentation**: [User Guide](docs/user-guide.md) for installation and usage
- **Developer Documentation**: [Developer Guide](docs/developer-guide.md) for architecture and development
- **Issues**: Report bugs and feature requests via GitHub Issues

---

**Quick Links:**
- [Installation Guide](docs/user-guide.md#installation)
- [Configuration Reference](docs/user-guide.md#configuration)
- [CLI Commands](docs/user-guide.md#basic-usage)
- [Advanced Filtering System](docs/user-guide.md#advanced-filtering-system) - Synonym and Flywire type filtering
- [Architecture Overview](docs/developer-guide.md#architecture-overview)
- [Performance Tools](performance/README.md)
