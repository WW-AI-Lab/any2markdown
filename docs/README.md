# Any2Markdown MCP Server 项目文档

## 📖 文档概览

本项目基于 Model Context Protocol (MCP) 重新实现文档转换服务，将PDF、Word、Excel文档转换为Markdown格式。使用官方最新SDK和Streamable HTTP Transport模式。

## 🗂️ 文档结构

### 📋 规划文档
- **[开发规划](./mcp-server-development-plan.md)** - 完整的MCP server开发规划，包含所有tools设计
- **[技术设计](./technical-design.md)** - 详细的技术实现设计和架构说明
- **[实现路线图](./implementation-roadmap.md)** - 分阶段的开发计划和时间线

## 🎯 项目目标

### 核心功能
- ✅ **PDF转换**: 基于marker-pdf的高质量PDF转换
- ✅ **Word转换**: 支持.docx/.doc格式的Word文档转换
- ✅ **Excel转换**: 支持.xlsx/.xls格式的Excel文档转换
- ✅ **批量处理**: 支持多文档并发处理
- ✅ **多格式输出**: 支持markdown、html、json输出格式
- ✅ **页眉页脚移除**: 智能识别并移除文档页眉页脚
- ✅ **图片静态化**: 提取文档图片并提供可访问的URL

### 技术特性
- 🔗 **MCP协议**: 基于标准MCP协议实现
- 🌐 **HTTP传输**: 使用Streamable HTTP Transport
- ⚡ **异步处理**: 原生异步支持和并发控制
- 🛡️ **类型安全**: 严格的输入输出Schema定义
- 🔧 **工具化**: 每个功能作为独立MCP tool

## 🛠️ MCP Tools 概览

### 文档转换工具

| Tool Name | 功能描述 | 输入格式 | 输出格式 |
|-----------|----------|----------|----------|
| `convert_pdf_to_markdown` | PDF文档转换，支持移除页眉页脚和图片提取 | PDF (Base64) | Markdown/HTML/JSON |
| `convert_word_to_markdown` | Word文档转换，支持移除页眉页脚和图片提取 | DOCX/DOC (Base64) | Markdown/HTML/JSON |
| `convert_excel_to_markdown` | Excel文档转换 | XLSX/XLS (Base64) | Markdown/HTML/JSON |
| `batch_convert_documents` | 批量文档转换 | 多文档数组 | 批量转换结果 |

### 分析和工具类

| Tool Name | 功能描述 | 用途 |
|-----------|----------|------|
| `analyze_pdf_structure` | PDF结构分析 | 预分析PDF文档结构信息 |
| `validate_document` | 文档验证 | 验证文档格式和处理可行性 |
| `get_supported_formats` | 获取支持格式 | 查询系统支持的文档格式 |

## 🏗️ 技术架构

### MCP协议层次
```
┌─────────────────────────┐
│   Client Application    │
└─────────────────────────┘
            │ MCP Client SDK
            ▼
┌─────────────────────────┐
│  HTTP/JSON-RPC Channel  │
└─────────────────────────┘
            │ Streamable HTTP
            ▼
┌──────────────────────────┬────────────────────────┐
│   MCP Server Core        │  Static File Service   │
├──────────────────────────┤  (for extracted images)│
│   Tool Registry          │                        │
│   ├─ PDF Tools           │                        │
│   ├─ Word Tools          │                        │
│   ├─ Excel Tools         │                        │
│   └─ Utility Tools       │                        │
└──────────────────────────┴────────────────────────┘
            │
            ▼
┌─────────────────────────┐
│  Document Processors    │
├─────────────────────────┤
│  ├─ Marker PDF          │
│  ├─ Python-docx         │
│  └─ Pandas/OpenPyXL     │
└─────────────────────────┘
```

### 核心组件
- **MCP Server**: 基于官方python-sdk实现
- **Tool Registry**: 工具注册和管理系统
- **Document Processors**: 文档处理器层
- **Model Manager**: marker模型管理系统
- **Concurrent Controller**: 并发控制和资源管理
- **Static File Service**: 静态文件服务，用于托管从文档中提取的图片

## 📦 项目结构

```
any2markdown/
├── docs/                           # 📚 项目文档
│   ├── README.md                   # 📖 文档索引 (本文件)
│   ├── mcp-server-development-plan.md  # 📋 开发规划
│   ├── technical-design.md         # 🏗️ 技术设计
│   └── implementation-roadmap.md   # 📅 实现路线图
├── src/                           # 💻 源代码
│   └── any2markdown_mcp/          # 📦 主包
│       ├── __init__.py
│       ├── server.py              # 🖥️ MCP服务器主文件
│       ├── config.py              # ⚙️ 配置管理
│       ├── logger.py              # 📝 日志系统
│       ├── tools/                 # 🔧 MCP工具实现
│       │   ├── pdf_tools.py       # 📄 PDF转换工具
│       │   ├── word_tools.py      # 📃 Word转换工具
│       │   ├── excel_tools.py     # 📊 Excel转换工具
│       │   └── utility_tools.py   # 🛠️ 工具类
│       ├── processors/            # ⚙️ 文档处理器
│       │   ├── base_processor.py  # 🏗️ 基础处理器
│       │   ├── pdf_processor.py   # 📄 PDF处理器
│       │   ├── word_processor.py  # 📃 Word处理器
│       │   └── excel_processor.py # 📊 Excel处理器
│       ├── models/                # 🧠 模型管理
│       │   └── model_manager.py   # 🎯 模型管理器
│       └── utils/                 # 🛠️ 工具函数
│           ├── file_utils.py      # 📁 文件处理
│           └── validation.py      # ✅ 验证功能
├── tests/                         # 🧪 测试代码
├── examples/                      # 📚 使用示例  
├── requirements.txt               # 📋 依赖列表
├── pyproject.toml                 # 🏗️ 项目配置
├── Dockerfile                     # 🐳 Docker配置
└── README.md                      # 📖 项目说明
```

## 🚀 快速开始

### 1. 环境准备
```bash
# 克隆项目
cd any2markdown

# 创建虚拟环境 (Python 3.9+)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动服务器
```bash
# 开发模式启动
python -m src.any2markdown_mcp.server --dev

# 生产模式启动  
python -m src.any2markdown_mcp.server --host 0.0.0.0 --port 8080
```

### 3. 测试连接
```bash
# 健康检查
curl http://localhost:8080/health

# 获取支持的格式
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/call", "params": {"name": "get_supported_formats"}}'
```

## 📊 开发进度

### 阶段概览
- 🚀 **阶段1**: 基础设施搭建 (1-2天)
- 📄 **阶段2**: 核心转换工具实现 (3-4天)  
- 🔧 **阶段3**: 高级功能实现 (2-3天)
- 🧪 **阶段4**: 测试和完善 (2-3天)

### 当前状态
- ✅ 项目规划完成
- ✅ 技术设计完成
- ✅ 实现路线图制定
- ⏳ 基础设施搭建 (进行中)

详细进度请查看 [实现路线图](./implementation-roadmap.md)

## 🔗 相关链接

### 官方资源
- [Model Context Protocol 官网](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP 规范文档](https://spec.modelcontextprotocol.io/)

### 技术文档
- [Marker PDF 文档](https://github.com/VikParuchuri/marker)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Python-docx 文档](https://python-docx.readthedocs.io/)

## 🤝 贡献指南

### 开发工作流
1. 查看 [实现路线图](./implementation-roadmap.md) 了解当前任务
2. 创建功能分支: `git checkout -b feature/tool-name`
3. 实现功能并添加测试
4. 确保代码质量: `black`, `isort`, `mypy`, `pytest`
5. 提交代码: 遵循 [提交规范](./implementation-roadmap.md#git提交规范)
6. 创建Pull Request

### 代码标准
- 📏 行长度: 88字符
- 🏷️ 类型注解: 必须
- 📚 文档字符串: 必须
- 🧪 测试覆盖率: >80%

## 🆘 获取帮助

### 问题排查
1. 查看 [技术设计文档](./technical-design.md) 了解架构
2. 检查日志文件和错误信息
3. 查看 [已知问题](#) (待创建)

### 联系方式
- 📧 技术问题: 查看现有实现或创建Issue
- 📋 功能请求: 参考 [开发规划](./mcp-server-development-plan.md)
- 🐛 Bug报告: 提供详细的复现步骤

---

## 📄 许可证

本项目遵循与原项目相同的许可证。

---

**🎯 目标**: 创建一个高性能、可扩展、标准化的文档转换MCP服务器，提供比传统API更好的开发体验和集成能力。

**🚀 愿景**: 成为MCP生态系统中文档处理的标准解决方案，支持多种文档格式和输出选项。 