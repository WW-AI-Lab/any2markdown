"""
Any2Markdown MCP Server (使用 FastMCP 高级API)

使用官方推荐的 FastMCP 库创建 MCP 服务器，支持 StreamableHTTP 传输，
并通过 custom_route 添加静态文件服务和RESTful API。
"""

from pathlib import Path
from mcp.server.fastmcp import FastMCP
from fastapi import Response, Request
import mimetypes

from .config import settings
from .logger import get_logger

# 导入所有工具函数
from .tools.pdf_tools import convert_pdf_to_markdown, analyze_pdf_structure
from .tools.word_tools import convert_word_to_markdown
from .tools.excel_tools import convert_excel_to_markdown
from .tools.utility_tools import batch_convert_documents, get_system_status, validate_document

# 导入API处理器
from .api.handlers import (
    handle_pdf_analyze, handle_validate,
    handle_status, handle_formats, handle_docs, handle_openapi,
    handle_unified_convert
)

logger = get_logger(__name__)

def create_mcp_server() -> FastMCP:
    """
    创建并配置 FastMCP 服务器实例，并集成静态文件服务
    """
    mcp = FastMCP(
        name="any2markdown-mcp-server",
        port=settings.port,
        host=settings.host,
        debug=settings.debug,
        log_level="DEBUG" if settings.debug else "INFO"
    )

    # 注册所有 MCP 工具
    mcp.tool()(convert_pdf_to_markdown)
    mcp.tool()(analyze_pdf_structure)
    mcp.tool()(convert_word_to_markdown)
    mcp.tool()(convert_excel_to_markdown)
    mcp.tool()(batch_convert_documents)
    mcp.tool()(get_system_status)
    mcp.tool()(validate_document)

    static_dir = Path(settings.temp_image_dir).resolve()
    static_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"静态文件目录已确认: {static_dir}")

    @mcp.custom_route(path="/static/{file_path:path}", methods=["GET"])
    async def serve_static_files(request: Request):
        path_param = request.path_params.get("file_path", "")
        file_path = static_dir / path_param
        if file_path.is_file():
            mime_type, _ = mimetypes.guess_type(file_path)
            return Response(
                file_path.read_bytes(),
                media_type=mime_type or "application/octet-stream"
            )
        logger.warning("请求的静态文件未找到", path=str(file_path))
        return Response(content="Not Found", status_code=404)

    @mcp.custom_route(path="/health", methods=["GET"])
    async def health_check(request: Request):
        return Response(
            content='{"status":"ok","service":"any2markdown-mcp-server"}',
            media_type="application/json"
        )

    # 注册RESTful API路由
    # 统一转换端点 (支持multipart/form-data和JSON两种方式)
    @mcp.custom_route(path="/api/v1/convert", methods=["POST"])
    async def api_unified_convert(request: Request):
        return await handle_unified_convert(request)

    # 分析端点
    @mcp.custom_route(path="/api/v1/analyze/pdf", methods=["GET"])
    async def api_analyze_pdf(request: Request):
        return await handle_pdf_analyze(request)

    # 工具端点
    @mcp.custom_route(path="/api/v1/validate", methods=["POST"])
    async def api_validate(request: Request):
        return await handle_validate(request)

    # 系统端点
    @mcp.custom_route(path="/api/v1/status", methods=["GET"])
    async def api_status(request: Request):
        return await handle_status(request)

    @mcp.custom_route(path="/api/v1/formats", methods=["GET"])
    async def api_formats(request: Request):
        return await handle_formats(request)

    # 文档端点
    @mcp.custom_route(path="/api/v1/docs", methods=["GET"])
    async def api_docs(request: Request):
        return await handle_docs(request)

    @mcp.custom_route(path="/api/v1/openapi.json", methods=["GET"])
    async def api_openapi(request: Request):
        return await handle_openapi(request)

    # CORS预检请求处理
    @mcp.custom_route(path="/api/v1/{path:path}", methods=["OPTIONS"])
    async def api_options(request: Request):
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Request-ID"
            }
        )

    logger.info(f"FastMCP 服务器已创建，将在 {settings.host}:{settings.port} 启动")
    logger.info("已注册以下端点:")
    logger.info("  - MCP协议: /mcp")
    logger.info("  - 静态文件: /static")
    logger.info("  - RESTful API: /api/v1")
    logger.info("  - API文档: /api/v1/docs")
    
    return mcp