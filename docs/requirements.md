# 需求分析与功能清单

本文档旨在明确"any2markdown"项目重构的核心需求和功能范围。

## 1. 核心需求

用户反馈当前 `any2markdown` 的实现方式存在严重问题，未使用官方推荐的 MCP (Model Context Protocol) SDK，而是采用了普通的 HTTP 服务。本次重构的核心目标是**将项目完全迁移到官方 MCP Python SDK，并采用 `StreamableHTTP` 协议进行通信**。

## 2. 功能性需求

| 模块 | 功能点 | 详细说明 | 优先级 |
| --- | --- | --- | --- |
| **MCP Server** | **基于 `StreamableHTTP` 的重构** | <ul><li>替换现有 Web 服务框架（如 `aiohttp` 的底层直接应用）为 `mcp_client.mcp_server.StreamableHttpMcpServer`。</li><li>**禁止**使用 `fastmcp` 或其他非官方、非标准的实现。</li></ul> | **高** |
| | **工具注册与暴露** | <ul><li>服务器必须能够动态加载并注册 `src/any2markdown_mcp/tools/` 目录下的所有工具。</li><li>确保 `pdf_tools`, `word_tools`, `excel_tools`, `utility_tools` 中的功能可以被客户端正确发现和调用。</li></ul> | **高** |
| | **异步与流式处理** | <ul><li>服务器必须是完全异步的 (`asyncio`)。</li><li>利用 `StreamableHTTP` 的特性，支持潜在的流式响应，例如在处理大型文件时可以逐步返回处理状态或结果。</li></ul> | **中** |
| **MCP Client** | **官方 SDK 客户端** | <ul><li>创建一个新的测试客户端 `test_streamable_client.py`。</li><li>该客户端必须使用 `mcp_client.mcp_client.StreamableHttpMcpClient`。</li></ul> | **高** |
| | **功能验证** | <ul><li>客户端需要能够连接到重构后的 MCP Server。</li><li>实现至少一个完整的工具调用测试用例（例如，调用 `convert_pdf_to_markdown`），并能成功接收和验证返回结果。</li></ul> | **高** |

## 3. 非功能性需求

| 类别 | 需求说明 |
| --- | --- |
| **性能** | 服务器应具备高性能和高并发处理能力，能够稳定处理多个并发的转换请求。 |
| **兼容性** | 新的实现需要与项目现有的配置文件 (`config.py`)、日志系统 (`logger.py`) 和处理器 (`processors/`) 无缝集成。 |
| **可维护性** | 代码结构应清晰，遵循 Python最佳实践，关键部分需有注释，方便未来扩展和维护。 |
| **文档** | <ul><li>更新 `README.md`，提供启动新版 MCP Server 和运行测试客户端的明确指令。</li><li>本次重构过程本身需要有清晰的规划文档。</li></ul> |
| **错误处理** | 提供健壮的错误处理机制，当工具执行失败或请求无效时，能向客户端返回标准格式的错误信息。 |

## 4. 范围外说明

*   本次重构不涉及新增任何文件转换功能。
*   不涉及对现有文件处理器（`pdf_processor.py` 等）内部逻辑的修改，仅关注其与新版 MCP Server 的集成。
*   不涉及 UI 界面的开发。 