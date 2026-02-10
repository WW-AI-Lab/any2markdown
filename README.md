# Any2Markdown MCP 服务器

[![Python 版本](https://img.shields.io/badge/python-3.10--3.13-blue.svg)](https://python.org)
[![MCP 协议](https://img.shields.io/badge/MCP-1.26%2B-green.svg)](https://modelcontextprotocol.io/)
[![许可证](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![构建状态](https://img.shields.io/badge/build-passing-brightgreen.svg)]()

一个高性能的文档转换服务器，同时支持 **Model Context Protocol (MCP 模型上下文协议)** 和 **RESTful API** 接口。将 PDF、Word 和 Excel 文档转换为 Markdown 格式，具备图片提取、页眉页脚移除和批量处理等高级功能。

**📚 语言版本**: [English README](README-en.md) | [中文说明](README.md)

## ✨ 核心特性

### 🔄 双协议支持
- **MCP 协议**：原生支持模型上下文协议和流式 HTTP 传输
- **RESTful API**：传统 HTTP API，配备 OpenAPI/Swagger 文档
- **统一后端**：两种协议共享相同的转换逻辑

### 📄 文档转换
- **PDF 转 Markdown**：基于 [marker-pdf](https://github.com/VikParuchuri/marker) 的高质量文本提取
- **Word 转 Markdown**：支持 .docx/.doc 格式，保持格式化
- **Excel 转 Markdown**：支持 .xlsx/.xls 格式，表格转换
- **批量处理**：并发处理多个文档

### 🖼️ 高级功能
- **图片提取**：从文档中提取图片并通过静态 URL 提供服务
- **页眉页脚移除**：智能移除重复的页面元素
- **多格式输出**：Markdown、HTML 和 JSON 输出格式
- **结构分析**：文档结构分析和验证
- **并发处理**：高性能异步处理和速率限制

## 🚀 快速开始

### 系统要求
- Python 3.10 - 3.13（已验证 Python 3.13，暂不建议 3.14）
- 4GB+ 内存（用于 AI 模型）
- 10GB+ 磁盘空间（用于模型缓存）

### 安装

```bash
# 克隆仓库
git clone https://github.com/WW-AI-Lab/any2markdown.git
cd any2markdown

# 创建虚拟环境（推荐使用 Python 3.13）
python3.13 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 准备环境变量文件
cp env.example .env

# 安装依赖（默认使用华为镜像）
PIP_CONFIG_FILE=.pip/pip.conf pip install -r requirements.txt

# 或一键安装
./scripts/setup_venv.sh
```

### 快速启动

#### 方式一：Docker 部署（推荐，开箱即用）

```bash
# 使用预构建镜像直接启动服务
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

# 💡 卷挂载说明：
# - uploads/: 上传文件存储
# - temp_images/: 临时图片缓存  
# - logs/: 日志文件
# - models/: AI模型缓存（首次运行会自动下载，约3-5GB）

# 或使用部署脚本
./scripts/deploy.sh docker

# GPU 加速部署（需要 NVIDIA GPU）
./scripts/deploy.sh docker-gpu

# 自定义端口部署
./scripts/deploy.sh docker -p 8080

# 或直接使用 docker-compose：
docker-compose up -d any2markdown-mcp
```

#### 方式二：源码部署（开发环境）

```bash
# 使用部署脚本启动服务器
./scripts/deploy.sh source

# 或手动启动：
python run_server.py

# 服务器将在以下地址可用：
# - MCP 协议：http://localhost:3000/mcp (流式 HTTP)
# - REST API：http://localhost:3000/api/v1/
# - API 文档：http://localhost:3000/api/v1/docs
```

### 测试安装

```bash
# 测试 RESTful API
python test_restful_api.py

# 测试 MCP 协议（官方 SDK，streamable-http）
python test_streamable_client.py ~/Downloads/测试翻译_1_1_translate.docx

# 检查服务状态
./scripts/deploy.sh status

# 停止服务
./scripts/deploy.sh stop
```

## 📖 使用示例

### RESTful API

> 📋 **完整API文档**: 详细的API设计和使用说明请参考 [RESTful API 设计文档](docs/restful-api-design.md)
> 
> 📋 **dify集成文档**: 详细的dify集成文档请参考 [dify集成文档](docs/dify.md)

Any2Markdown 提供统一的RESTful API接口，支持两种调用方式：

#### 快速开始

```bash
# 文件上传方式 (推荐)
curl -X POST "http://localhost:3000/api/v1/convert" \
  -F "file=@document.pdf" \
  -F "extract_images=true" \
  -F "include_content=false"

# JSON方式 (base64编码)
curl -X POST "http://localhost:3000/api/v1/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "files": [{
      "filename": "document.pdf",
      "file_content": "<base64编码的PDF>",
      "options": {
        "extract_images": true,
        "include_content": false
      }
    }]
  }'

# 查看系统状态
curl "http://localhost:3000/api/v1/status"

# 访问API文档
open http://localhost:3000/api/v1/docs
```

#### 支持的功能

- ✅ **统一端点**: 单一`/api/v1/convert`端点处理所有文档类型
- ✅ **双调用方式**: 支持文件上传和base64 JSON两种方式  
- ✅ **多文件处理**: 支持批量转换多个文档
- ✅ **自动检测**: 根据文件扩展名自动识别文档类型
- ✅ **丰富选项**: 支持图片提取、页面范围、格式保留等选项

### MCP 协议

```python
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client

# 连接到 MCP 服务器
async with stdio_client() as (read, write):
    async with ClientSession(read, write) as session:
        # 转换 PDF 文档
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

## 🛠️ 可用工具/端点

| 工具/端点 | 描述 | 输入格式 | 功能特性 |
|-----------|------|----------|----------|
| `convert_pdf_to_markdown` | PDF 转换，AI 驱动的文本提取 | PDF | OCR、布局检测、图片提取 |
| `convert_word_to_markdown` | Word 文档转换 | DOCX, DOC | 格式保持、图片提取 |
| `convert_excel_to_markdown` | 电子表格转换 | XLSX, XLS | 多工作表、公式支持 |
| `batch_convert_documents` | 批量处理 | 混合格式 | 并发处理 |
| `analyze_pdf_structure` | 文档结构分析 | PDF | 元数据提取 |
| `validate_document` | 文档验证 | 所有格式 | 格式验证 |
| `get_supported_formats` | 列出支持的格式 | - | 功能发现 |

## 🏗️ 架构设计

```
┌─────────────────────────┐  ┌─────────────────────────┐
│     MCP 客户端          │  │    HTTP 客户端          │
│  (Claude, IDE 等)       │  │  (Web, Mobile 等)       │
└─────────────────────────┘  └─────────────────────────┘
            │                            │
            ▼                            ▼
┌─────────────────────────────────────────────────────┐
│              Any2Markdown 服务器                    │
├─────────────────────────┬───────────────────────────┤
│     MCP 协议            │      RESTful API          │
│  (流式 HTTP)            │   (OpenAPI/Swagger)       │
└─────────────────────────┴───────────────────────────┘
            │                            │
            └─────────────┬──────────────┘
                          ▼
┌─────────────────────────────────────────────────────┐
│               共享后端                               │
├─────────────────────────────────────────────────────┤
│  文档处理器           │  模型管理器     │  工具模块    │
│  ├─ PDF (marker)      │  ├─ AI 模型     │  ├─ 文件    │
│  ├─ Word (python-docx)│  ├─ 缓存        │  ├─ 验证    │
│  └─ Excel (pandas)    │  └─ 内存        │  └─ 图片    │
└─────────────────────────────────────────────────────┘
```

## 📁 项目结构

```
any2markdown/
├── 📚 docs/                    # 文档
│   ├── README.md               # 项目概述
│   ├── technical-design.md     # 技术架构
│   ├── restful-api-design.md   # API 规范
│   └── requirements.md         # 需求分析
├── 💻 src/any2markdown_mcp/    # 源代码
│   ├── server.py               # 主服务器 (MCP + FastAPI)
│   ├── config.py               # 配置管理
│   ├── 🔧 tools/               # MCP 工具实现
│   │   ├── pdf_tools.py        # PDF 转换工具
│   │   ├── word_tools.py       # Word 转换工具
│   │   ├── excel_tools.py      # Excel 转换工具
│   │   └── utility_tools.py    # 实用工具
│   ├── 🌐 api/                 # RESTful API 层
│   │   ├── handlers.py         # API 端点
│   │   ├── models.py           # Pydantic 模型
│   │   └── utils.py            # API 工具
│   ├── ⚙️ processors/          # 文档处理器
│   │   ├── pdf_processor.py    # PDF 处理逻辑
│   │   ├── word_processor.py   # Word 处理逻辑
│   │   └── excel_processor.py  # Excel 处理逻辑
│   └── 🧠 models/              # AI 模型管理
│       └── model_manager.py    # 模型加载和缓存
├── 🧪 tests/                   # 测试文件
├── 🚀 scripts/                 # 部署脚本
│   └── deploy.sh               # 统一部署脚本
├── 📋 requirements.txt         # 依赖列表
├── 🏗️ pyproject.toml           # 项目配置
├── 🐳 Dockerfile               # Docker 配置
├── 🐳 docker-compose.yml       # Docker Compose 配置
└── 🚀 run_server.py            # 服务器启动脚本
```

## ⚙️ 配置

### 环境变量

```bash
# 服务器配置
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=3000

# 处理配置  
MAX_CONCURRENT_JOBS=3
MAX_FILE_SIZE=100MB
TEMP_IMAGE_DIR=./temp_images

# 模型配置
MODEL_CACHE_DIR=~/.cache/marker
USE_GPU=true

# Hugging Face模型缓存配置
HF_HOME=~/.cache/huggingface
HF_HUB_CACHE=~/.cache/huggingface/hub
HF_ASSETS_CACHE=~/.cache/huggingface/assets
TORCH_HOME=~/.cache/torch
TRANSFORMERS_CACHE=~/.cache/transformers

# 模型下载配置
HF_HUB_ENABLE_HF_TRANSFER=false
HF_HUB_DISABLE_PROGRESS_BARS=false
HF_HUB_DISABLE_TELEMETRY=true

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/server.log
DEBUG=false
```

### 部署选项

#### 源码部署

```bash
# 基础部署
./scripts/deploy.sh source

# 开发模式，启用调试日志
./scripts/deploy.sh source --dev

# 自定义端口并禁用 GPU
./scripts/deploy.sh source -p 8080 --no-gpu

# 自定义环境文件
./scripts/deploy.sh source -e .env.production
```

#### Docker 部署

```bash
# 标准 Docker 部署
./scripts/deploy.sh docker

# GPU 加速部署（需要 NVIDIA Docker）
./scripts/deploy.sh docker-gpu

# 自定义端口
./scripts/deploy.sh docker -p 8080

# 开发模式
./scripts/deploy.sh docker --dev
```

#### 模型缓存配置

为了避免每次重启容器都重新下载模型，建议配置模型缓存目录挂载：

```bash
# 1. 初始化模型缓存目录结构
./scripts/setup_model_cache.sh

# 2. 使用 Docker Compose（推荐）
docker-compose up -d

# 3. 或者手动指定挂载目录
docker run -d \
  -p 3000:3000 \
  -v ./models/marker:/home/appuser/.cache/marker \
  -v ./models/huggingface:/home/appuser/.cache/huggingface \
  -v ./models/torch:/home/appuser/.cache/torch \
  -v ./models/transformers:/home/appuser/.cache/transformers \
  -v ./logs:/app/logs \
  -v ./temp_images:/app/temp_images \
  --name any2markdown \
  any2markdown:latest
```

**模型缓存说明：**
- **首次启动**：系统会自动下载所需模型（约3-5GB），需要较长时间
- **后续启动**：使用缓存的模型，启动速度显著提升
- **磁盘空间**：建议预留至少10GB空间用于模型缓存
- **网络要求**：需要能够访问 Hugging Face Hub

#### 服务管理

```bash
# 检查服务状态
./scripts/deploy.sh status

# 停止所有服务
./scripts/deploy.sh stop

# 清理资源
./scripts/deploy.sh cleanup
```

### 配置文件

创建 `config.toml` 或设置环境变量：

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

# Hugging Face 模型缓存配置
hf_home = "~/.cache/huggingface"
hf_hub_cache = "~/.cache/huggingface/hub"
hf_assets_cache = "~/.cache/huggingface/assets"
torch_home = "~/.cache/torch"
transformers_cache = "~/.cache/transformers"

# 模型下载选项
hf_hub_enable_hf_transfer = false
hf_hub_disable_progress_bars = false
hf_hub_disable_telemetry = true

[logging]
level = "INFO"
file = "logs/server.log"
```

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行特定测试类别
pytest -m unit          # 单元测试
pytest -m integration   # 集成测试
pytest -m slow          # 需要模型加载的测试

# 运行覆盖率测试
pytest --cov=src/any2markdown_mcp --cov-report=html

# 测试特定功能
python test_restful_api.py      # REST API 测试
python test_streamable_client.py ~/Downloads/测试翻译_1_1_translate.docx  # MCP 协议测试
```

## dify集成

支持在dify工作流中集成，即通过dify 默认的http节点即可实现文件转换，具体方法查阅[dify集成](docs/dify.md)

## 📊 性能

### 基准测试

- **PDF 转换**：~2-5 秒/页（使用 GPU）
- **Word 转换**：~0.5-2 秒/文档
- **Excel 转换**：~0.1-1 秒/工作表
- **并发请求**：最多 3 个同时转换
- **内存使用**：~2-4GB（模型加载后）

### 优化建议
- 为 PDF 处理启用 GPU 加速
- 根据可用内存调整 `MAX_CONCURRENT_JOBS`
- 为模型缓存使用 SSD 存储
- 为大型文档配置适当的超时值

## 🤝 贡献

我们欢迎贡献！请查看我们的[贡献指南](docs/contributing.md)。

### 开发环境设置

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 安装 pre-commit 钩子
pre-commit install

# 运行代码质量检查
black src/ tests/
isort src/ tests/  
mypy src/
flake8 src/
pytest
```

### 添加新文档类型

1. 在 `src/any2markdown_mcp/processors/` 中创建处理器
2. 在 `src/any2markdown_mcp/tools/` 中添加 MCP 工具
3. 在 `src/any2markdown_mcp/api/` 中添加 API 端点
4. 更新文档和测试

## 📄 API 文档

- **交互式 API 文档**：http://localhost:3000/api/v1/docs
- **OpenAPI 规范**：http://localhost:3000/api/v1/openapi.json
- **技术设计**：[docs/technical-design.md](docs/technical-design.md)
- **API 设计**：[docs/restful-api-design.md](docs/restful-api-design.md)

## 🔗 相关项目

- [模型上下文协议](https://modelcontextprotocol.io/) - 官方 MCP 规范
- [marker-pdf](https://github.com/VikParuchuri/marker) - PDF 转 Markdown 转换
- [python-docx](https://python-docx.readthedocs.io/) - Word 文档处理
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Web 框架

## 📝 许可证

本项目使用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙋 支持

- **文档**：[docs/](docs/)
- **问题反馈**：[GitHub Issues](https://github.com/WW-AI-Lab/any2markdown/issues)
- **讨论**：[GitHub Discussions](https://github.com/WW-AI-Lab/any2markdown/discussions)

## 🎯 发展路线图

- [ ] 支持 PowerPoint (PPTX) 转换
- [ ] 图片类型PDF转换效果优化
- [ ] Kubernetes 部署清单
- [ ] 云存储集成
