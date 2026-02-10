<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

## 项目定位与目标

`any2markdown` 是一个文档转 Markdown 服务，当前实现目标是：
- 同时提供 `MCP` 与 `RESTful API` 两种调用方式；
- 支持 `PDF`、`Word(docx/doc)`、`Excel(xlsx/xls)` 转换；
- 提供图片提取、文档校验、批量转换、基础结构分析能力；
- 统一由 `src/any2markdown_mcp/` 下处理器与工具层实现核心逻辑。

## 代码结构速览

- `src/any2markdown_mcp/server.py`：FastMCP 入口，注册 MCP 工具与 REST 路由。
- `src/any2markdown_mcp/tools/`：MCP 工具函数层（参数协议、响应组装）。
- `src/any2markdown_mcp/processors/`：文档处理核心逻辑（PDF/Word/Excel）。
- `src/any2markdown_mcp/api/`：REST API Handler 与请求/响应模型。
- `src/any2markdown_mcp/config.py`：环境变量与默认配置。

## 代码规范与工程约束

### Python 与风格

- Python 版本基线：`>=3.10,<3.14`（推荐 `3.13`，见 `pyproject.toml`）。
- 行宽按 `88` 字符控制（Black/isort 配置已定义）。
- 新增或修改函数优先补全类型注解，保持 `mypy` 严格配置兼容。
- 保持异步接口一致性：工具与处理链路使用 `async`。

### 功能与接口约束

- 输入文件类型受 `allowed_file_types` 限制：`pdf/docx/doc/xlsx/xls`。
- 默认最大文件大小：`100MB`（`max_file_size`）。
- 默认服务端口：`3000`，MCP 路径：`/mcp`，REST 前缀：`/api/v1`。
- 转换接口默认 `include_content=false`，避免在响应中返回大文本正文。

### 资源与运行约束

- 首次 PDF 能力使用可能触发模型下载，依赖 `~/.cache/marker` 与 HuggingFace/Torch 缓存目录。
- 项目当前文档中存在“规划态”和“实现态”混合内容；修改功能时应同步更新文档，避免与实际代码偏离。
- 仓库当前未包含 `tests/` 目录；如新增测试需与现有 `pytest` 配置保持一致。

## 修改原则（给协作代理）

- 优先做“最小可验证改动”，避免无关重构。
- 变更接口或配置项时，至少同步更新以下文档之一：
  - `README.md`
  - `docs/*.md` 对应专题文档
  - `openspec/project.md`（项目约定变更）
- 涉及新增能力、破坏性变更、架构级调整时，先按 `openspec/AGENTS.md` 走 proposal 流程，再实现代码。
