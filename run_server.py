#!/usr/bin/env python3
"""
Any2Markdown MCP Server 启动脚本 (基于 FastMCP)
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.any2markdown_mcp.server import create_mcp_server
from src.any2markdown_mcp.config import settings
from src.any2markdown_mcp.logger import setup_logging

if __name__ == "__main__":
    # 检查环境变量配置
    env_file = project_root / ".env"
    if not env_file.exists():
        print("警告: .env文件不存在，将使用默认配置")
        print(f"请复制 {project_root / 'env.example'} 到 {env_file} 并根据需要修改配置")

    # 配置日志系统
    setup_logging(log_level=settings.log_level, log_file=settings.log_file, debug=settings.debug)

    # 创建 FastMCP 服务器实例
    mcp_server = create_mcp_server()

    # 启动服务器 (FastMCP 内部处理所有传输层逻辑)
    print(f"启动 MCP 服务器在 {settings.host}:{settings.port}")
    mcp_server.run(transport="streamable-http") 