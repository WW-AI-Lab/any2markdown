# Any2Markdown MCP Server

[![Python Version](https://img.shields.io/badge/python-3.10--3.13-blue.svg)](https://python.org)
[![MCP Protocol](https://img.shields.io/badge/MCP-1.26%2B-green.svg)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()

A high-performance document conversion server that supports both **Model Context Protocol (MCP)** and **RESTful API** interfaces. Convert PDF, Word, and Excel documents to Markdown with advanced features like image extraction, header/footer removal, and batch processing.

**📚 Language Versions**: [English README](README-en.md) | [中文说明](README.md)

## ✨ Key Features

### 🔄 Dual Protocol Support
- **MCP Protocol**: Native support for Model Context Protocol with Streamable HTTP Transport
- **RESTful API**: Traditional HTTP API with OpenAPI/Swagger documentation
- **Unified Backend**: Both protocols share the same conversion logic

### 📄 Document Conversion
- **PDF to Markdown**: Powered by [marker-pdf](https://github.com/VikParuchuri/marker) with high-quality text extraction
- **Word to Markdown**: Support for .docx/.doc with formatting preservation  
- **Excel to Markdown**: Support for .xlsx/.xls with table conversion
- **Batch Processing**: Convert multiple documents concurrently

### 🖼️ Advanced Features
- **Image Extraction**: Extract and serve images from documents via static URLs
- **Header/Footer Removal**: Intelligent removal of repetitive page elements
- **Multi-format Output**: Markdown, HTML, and JSON output formats
- **Structure Analysis**: Document structure analysis and validation
- **Concurrent Processing**: High-performance async processing with rate limiting

## 🚀 Quick Start

### Prerequisites
- Python 3.10 - 3.13 (validated on Python 3.13; 3.14 is not recommended yet)
- 4GB+ RAM (for AI models)
- 10GB+ disk space (for model cache)

### Installation

```bash
# Clone the repository
git clone https://github.com/WW-AI-Lab/any2markdown.git
cd any2markdown

# Create virtual environment (Python 3.13 recommended)
python3.13 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (Huawei mirror by default)
PIP_CONFIG_FILE=.pip/pip.conf pip install -r requirements.txt

# Or use one-command bootstrap
./scripts/setup_venv.sh
```

### Quick Start

#### Option 1: Docker Deployment (Recommended, Ready-to-use)

```bash
# Start service using pre-built image
docker run -d \
  -p 3000:3000 \
  --name any2markdown-mcp-server \
  --restart unless-stopped \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/temp_images:/app/temp_images \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/models:/root/.cache/marker \
  -v $(pwd)/models/huggingface:/root/.cache/huggingface \
  -v $(pwd)/models/torch:/root/.cache/torch \
  -v $(pwd)/models/transformers:/root/.cache/transformers \
  ccr.ccs.tencentyun.com/yfgaia/any2markdown-mcp-server:latest

# 💡 Volume Mount Explanation:
# - uploads/: Uploaded file storage
# - temp_images/: Temporary image cache
# - logs/: Log files
# - models/: AI model cache (auto-downloaded on first run, ~3-5GB)

# Or using deployment script
./scripts/deploy.sh docker

# GPU-enabled deployment (requires NVIDIA GPU)
./scripts/deploy.sh docker-gpu

# Custom port deployment
./scripts/deploy.sh docker -p 8080

# Or using docker-compose directly:
docker-compose up -d any2markdown-mcp
```

#### Option 2: Source Code Deployment (Development Environment)

```bash
# Start the server using deployment script
./scripts/deploy.sh source

# Or manually:
python run_server.py

# The server will be available at:
# - MCP Protocol: http://localhost:3000 (Streamable HTTP)
# - REST API: http://localhost:3000/api/v1/
# - API Documentation: http://localhost:3000/api/v1/docs
```

### Test the Installation

```bash
# Test RESTful API
python test_restful_api.py

# Test MCP Protocol (official SDK, streamable-http)
python test_streamable_client.py ~/Downloads/测试翻译_1_1_translate.docx

# Check service status
./scripts/deploy.sh status

# Stop services
./scripts/deploy.sh stop
```

## 📖 Usage Examples

### RESTful API

```bash
# Convert PDF to Markdown
curl -X POST "http://localhost:3000/api/v1/convert/pdf" \
  -H "Content-Type: application/json" \
  -d '{
    "file_content": "<base64-encoded-pdf>",
    "filename": "document.pdf",
    "extract_images": true,
    "remove_header_footer": true
  }'

# Get system status
curl "http://localhost:3000/api/v1/status"

# View API documentation
open http://localhost:3000/api/v1/docs
```

### MCP Protocol

```python
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client

# Connect to MCP server
async with stdio_client() as (read, write):
    async with ClientSession(read, write) as session:
        # Convert PDF document
        result = await session.call_tool(
            "convert_pdf_to_markdown",
            {
                "file_content": base64_pdf_content,
                "filename": "document.pdf",
                "extract_images": True,
                "remove_header_footer": True
            }
        )
        print(result.content)
```

## 🛠️ Available Tools/Endpoints

| Tool/Endpoint | Description | Input Formats | Features |
|---------------|-------------|---------------|----------|
| `convert_pdf_to_markdown` | PDF conversion with AI-powered text extraction | PDF | OCR, layout detection, image extraction |
| `convert_word_to_markdown` | Word document conversion | DOCX, DOC | Formatting preservation, image extraction |
| `convert_excel_to_markdown` | Spreadsheet conversion | XLSX, XLS | Multi-sheet, formula support |
| `batch_convert_documents` | Batch processing | Mixed formats | Concurrent processing |
| `analyze_pdf_structure` | Document structure analysis | PDF | Metadata extraction |
| `validate_document` | Document validation | All formats | Format verification |
| `get_supported_formats` | List supported formats | - | Capability discovery |

## 🏗️ Architecture

```
┌─────────────────────────┐  ┌─────────────────────────┐
│     MCP Clients         │  │    HTTP Clients         │
│  (Claude, IDEs, etc.)   │  │  (Web, Mobile, etc.)    │
└─────────────────────────┘  └─────────────────────────┘
            │                            │
            ▼                            ▼
┌─────────────────────────────────────────────────────┐
│              Any2Markdown Server                    │
├─────────────────────────┬───────────────────────────┤
│     MCP Protocol        │      RESTful API          │
│  (Streamable HTTP)      │   (OpenAPI/Swagger)       │
└─────────────────────────┴───────────────────────────┘
            │                            │
            └─────────────┬──────────────┘
                          ▼
┌─────────────────────────────────────────────────────┐
│               Shared Backend                        │
├─────────────────────────────────────────────────────┤
│  Document Processors  │  Model Manager  │  Utils    │
│  ├─ PDF (marker)      │  ├─ AI Models   │  ├─ File  │
│  ├─ Word (python-docx)│  ├─ Cache       │  ├─ Valid │
│  └─ Excel (pandas)    │  └─ Memory      │  └─ Image │
└─────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
any2markdown/
├── 📚 docs/                    # Documentation
│   ├── README.md               # Project overview  
│   ├── technical-design.md     # Technical architecture
│   ├── restful-api-design.md   # API specification
│   └── requirements.md         # Requirements analysis
├── 💻 src/any2markdown_mcp/    # Source code
│   ├── server.py               # Main server (MCP + FastAPI)
│   ├── config.py               # Configuration management
│   ├── 🔧 tools/               # MCP tools implementation
│   │   ├── pdf_tools.py        # PDF conversion tools
│   │   ├── word_tools.py       # Word conversion tools
│   │   ├── excel_tools.py      # Excel conversion tools
│   │   └── utility_tools.py    # Utility tools
│   ├── 🌐 api/                 # RESTful API layer
│   │   ├── handlers.py         # API endpoints
│   │   ├── models.py           # Pydantic models
│   │   └── utils.py            # API utilities
│   ├── ⚙️ processors/          # Document processors
│   │   ├── pdf_processor.py    # PDF processing logic
│   │   ├── word_processor.py   # Word processing logic
│   │   └── excel_processor.py  # Excel processing logic
│   └── 🧠 models/              # AI model management
│       └── model_manager.py    # Model loading and caching
├── 🧪 tests/                   # Test files
├── 📋 requirements.txt         # Dependencies
├── 🏗️ pyproject.toml           # Project configuration
└── 🚀 run_server.py            # Server startup script
```

## ⚙️ Configuration

### Environment Variables

```bash
# Server Configuration
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=3000

# Processing Configuration  
MAX_CONCURRENT_JOBS=3
MAX_FILE_SIZE=100MB
TEMP_IMAGE_DIR=./temp_images

# Model Configuration
MODEL_CACHE_DIR=~/.cache/marker
USE_GPU=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/server.log
DEBUG=false
```

### Deployment Options

#### Source Code Deployment

```bash
# Basic deployment
./scripts/deploy.sh source

# Development mode with debug logging
./scripts/deploy.sh source --dev

# Custom port and disable GPU
./scripts/deploy.sh source -p 8080 --no-gpu

# Custom environment file
./scripts/deploy.sh source -e .env.production
```

#### Docker Deployment

```bash
# Standard Docker deployment
./scripts/deploy.sh docker

# GPU-enabled deployment (requires NVIDIA Docker)
./scripts/deploy.sh docker-gpu

# Custom port
./scripts/deploy.sh docker -p 8080

# Development mode
./scripts/deploy.sh docker --dev
```

#### Service Management

```bash
# Check service status
./scripts/deploy.sh status

# Stop all services
./scripts/deploy.sh stop

# Clean up resources
./scripts/deploy.sh cleanup
```

### Configuration File

Create `config.toml` or set environment variables:

```toml
[server]
host = "0.0.0.0"
port = 3000
max_concurrent_jobs = 3

[processing]
max_file_size = "100MB"
temp_image_dir = "./temp_images"
enable_header_footer_removal = true

[models]
cache_dir = "~/.cache/marker"
enable_gpu = true
preload_models = true

[logging]
level = "INFO"
file = "logs/server.log"
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit          # Unit tests
pytest -m integration   # Integration tests
pytest -m slow          # Tests requiring model loading

# Run with coverage
pytest --cov=src/any2markdown_mcp --cov-report=html

# Test specific functionality
python test_restful_api.py      # REST API tests
python test_streamable_client.py ~/Downloads/测试翻译_1_1_translate.docx # MCP protocol tests
```

## 📊 Performance

### Benchmarks
- **PDF Conversion**: ~2-5 seconds per page (with GPU)
- **Word Conversion**: ~0.5-2 seconds per document  
- **Excel Conversion**: ~0.1-1 second per sheet
- **Concurrent Requests**: Up to 3 simultaneous conversions
- **Memory Usage**: ~2-4GB (with models loaded)

### Optimization Tips
- Enable GPU acceleration for PDF processing
- Adjust `MAX_CONCURRENT_JOBS` based on available memory
- Use SSD storage for model cache
- Configure appropriate timeout values for large documents

## 🤝 Contributing

We welcome contributions! Please see our [contributing guidelines](docs/contributing.md).

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run code quality checks
black src/ tests/
isort src/ tests/  
mypy src/
flake8 src/
pytest
```

### Adding New Document Types

1. Create processor in `src/any2markdown_mcp/processors/`
2. Add MCP tools in `src/any2markdown_mcp/tools/`
3. Add API endpoints in `src/any2markdown_mcp/api/`
4. Update documentation and tests

## 📄 API Documentation

- **Interactive API Docs**: http://localhost:3000/api/v1/docs
- **OpenAPI Specification**: http://localhost:3000/api/v1/openapi.json
- **Technical Design**: [docs/technical-design.md](docs/technical-design.md)
- **API Design**: [docs/restful-api-design.md](docs/restful-api-design.md)

## 🔗 Related Projects

- [Model Context Protocol](https://modelcontextprotocol.io/) - Official MCP specification
- [marker-pdf](https://github.com/VikParuchuri/marker) - PDF to markdown conversion
- [python-docx](https://python-docx.readthedocs.io/) - Word document processing
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/WW-AI-Lab/any2markdown/issues)
- **Discussions**: [GitHub Discussions](https://github.com/WW-AI-Lab/any2markdown/discussions)

## 🎯 Roadmap

- [ ] Support for PowerPoint (PPTX) conversion
- [ ] Real-time collaborative editing
- [ ] Plugin system for custom processors
- [ ] Docker containerization
- [ ] Kubernetes deployment manifests
- [ ] Performance monitoring and metrics
- [ ] Multi-language OCR support
- [ ] Cloud storage integration

---

**Made with ❤️ by the Any2Markdown team** 
