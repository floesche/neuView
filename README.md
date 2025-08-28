# QuickPage

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
cd quickpage
pixi install
```

2. **Set up your NeuPrint token:**
```bash
pixi run setup-env
# Edit .env and add your NeuPrint token
```

3. **Generate your first neuron page:**
```bash
quickpage generate -n Dm4
```

4. **View results:**
Open `output/index.html` in your browser

## 📖 Documentation

- **[User Guide](docs/user-guide.md)** - Installation, configuration, usage, and troubleshooting
- **[Developer Guide](docs/developer-guide.md)** - Architecture, development setup, and contribution guidelines

## 🏗️ Architecture

QuickPage is built using modern software engineering principles:

- **Domain-Driven Design (DDD)** with clean architecture
- **CQRS Pattern** for maintainable command/query separation
- **Result Pattern** for explicit error handling
- **Persistent Caching** for optimal performance
- **Responsive Frontend** with advanced filtering capabilities

## 📊 Performance

- **Cache Hit Rates**: Up to 88.9% for ROI hierarchy, 80.6% for column queries
- **Speed Improvements**: 97.9% faster on subsequent runs
- **Cross-session Benefits**: Persistent cache survives restarts
- **Database Load Reduction**: Significant decrease in redundant queries

## 🎯 Project Structure

```
quickpage/
├── src/quickpage/           # Application source code
├── templates/               # Jinja2 HTML templates  
├── static/                  # CSS, JS, and static assets
├── docs/                    # User and developer documentation
├── examples/                # Example configurations
├── test/                    # Test files
└── output/                  # Generated HTML pages
```

## 🧪 Testing

```bash
# Run all tests
pixi run test

# Test NeuPrint connection
pixi run test-connection

# Generate sample data
pixi run generate-sample
```

## 🤝 Contributing

We welcome contributions! Please see the [Developer Guide](docs/developer-guide.md) for:

- Development setup instructions
- Architecture overview
- Coding standards and conventions
- Testing strategies
- Pull request guidelines

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: See [User Guide](docs/user-guide.md) for detailed usage instructions
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Development**: See [Developer Guide](docs/developer-guide.md) for technical details

---

**Quick Links:**
- [Installation Guide](docs/user-guide.md#installation) 
- [Configuration Reference](docs/user-guide.md#configuration)
- [CLI Commands](docs/user-guide.md#basic-usage)
- [Architecture Overview](docs/developer-guide.md#architecture-overview)
- [Performance Optimization](docs/developer-guide.md#performance-optimizations)