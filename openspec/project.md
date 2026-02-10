# Project Context

## Purpose
`any2markdown` 的目标是提供一个可部署、可集成的文档转换服务，将 PDF/Word/Excel 转换为 Markdown（可选 HTML/JSON 输出），并对外同时暴露 MCP 与 REST API 接口。项目强调“统一转换核心 + 多协议访问”，以便在 AI Agent、工作流平台与传统后端中复用同一套处理能力。

## Tech Stack
- Python 3.10 - 3.13（推荐 3.13）
- `mcp` / FastMCP（MCP 服务暴露）
- FastAPI（通过 FastMCP custom routes 提供 REST 与静态资源）
- `marker-pdf` + `pymupdf`（PDF 处理）
- `python-docx`（Word 处理）
- `pandas` + `openpyxl`（Excel 处理）
- `pydantic` / `pydantic-settings`（配置与数据模型）
- `structlog`（结构化日志）

## Project Conventions

### Code Style
- 代码风格以 `pyproject.toml` 为准：
  - `black` 行宽 `88`
  - `isort` 使用 `black` profile
  - `flake8`、`mypy` 开启较严格规则
- 新增代码优先补全类型注解；公共函数与工具接口建议保留清晰 docstring。
- 命名遵循语义化：`processor/tool/handler` 分层命名，不使用缩写堆叠。
- 变更应最小化，避免无关重构或跨模块大面积格式改写。

### Architecture Patterns
- 分层模式：
  - `tools/`：协议适配与参数编排
  - `processors/`：格式转换核心逻辑
  - `api/`：REST 入口与响应封装
  - `config.py`：环境配置与默认值
- MCP 与 REST 共用同一处理链，避免双实现分叉。
- 图片提取后通过 `/static/*` 提供访问，转换结果中写入图片 URL。
- 处理流程默认异步化，批量转换通过 semaphore 控制并发。

### Testing Strategy
- 目标测试框架为 `pytest`（含 `pytest-asyncio` 与覆盖率配置）。
- 当前仓库未包含 `tests/` 目录，属于现实约束；新增测试时需与既有 `pytest` 配置兼容。
- 建议验证顺序：先做受影响模块的最小验证，再做端到端转换验证（MCP/REST 至少一条链路）。

### Git Workflow
- 功能开发建议使用特性分支（`feature/*`、`fix/*`）。
- 提交信息建议使用清晰前缀（如 `feat:`, `fix:`, `docs:`），聚焦单一意图。
- 对“新增能力/破坏性变更/架构变更”先走 OpenSpec proposal，再进入实现与合并。

## Domain Context
- 输入文档常见为业务报告、合同、票据、表格等，转换稳定性优先于极致格式还原。
- PDF 依赖模型与OCR链路，首次运行会下载较大模型缓存。
- API 设计中 `include_content` 默认为 `false`，减少大文本返回带来的带宽与延迟压力。
- 支持批量转换与文档校验，适合上游系统做前置过滤与异步处理。

## Important Constraints
- 文件类型白名单：`pdf/docx/doc/xlsx/xls`。
- 默认最大文件大小：`100MB`（`max_file_size`）。
- 默认端口：`3000`，MCP 路径：`/mcp`，REST 前缀：`/api/v1`。
- 运行依赖模型缓存目录（Marker/HuggingFace/Torch）；部署时需预留磁盘与内存。
- 文档中存在部分历史规划内容，改动功能时必须同步修正文档，确保“代码即事实”。

## External Dependencies
- Model Context Protocol 生态（MCP Client/Agent）。
- Marker PDF 与其模型依赖（PyTorch / Transformers / HuggingFace Hub）。
- 可选 Redis（配置存在，按部署需求启用）。
- Docker / docker-compose（生产与本地部署路径）。
