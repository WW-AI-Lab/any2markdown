"""
工具注册与发现 (函数式, for mcp==1.10.0)

该模块负责发现所有工具函数，并将其注册到 MCP Server 实例上。
它通过实现 list_tools 和 call_tool 两个处理器来工作。
"""

import inspect
import pkgutil
import importlib
import asyncio
import json
from typing import Dict, Any, List, Callable, Awaitable

from mcp.server.lowlevel.server import Server
import mcp.types as types
from mcp import McpError

from ..logger import get_logger

logger = get_logger(__name__)

# 一个简单的缓存来存储发现的工具函数
_tool_functions: Dict[str, Callable[..., Awaitable[Any]]] = {}
_tool_definitions: List[types.Tool] = []

def _create_tool_definition(name: str, func: Callable) -> types.Tool:
    """
    从函数创建工具定义。这是一个简化版本，实际应用中可能需要更复杂的逻辑。
    """
    sig = inspect.signature(func)
    doc = func.__doc__ or f"Tool: {name}"
    
    # 简单的参数处理 - 假设所有参数都是字符串类型
    properties = {}
    required = []
    
    for param_name, param in sig.parameters.items():
        if param.annotation != inspect.Parameter.empty:
            # 尝试从类型注解推断参数类型
            param_type = "string"  # 默认类型
            if param.annotation == int:
                param_type = "integer"
            elif param.annotation == bool:
                param_type = "boolean"
            elif param.annotation == float:
                param_type = "number"
        else:
            param_type = "string"
        
        properties[param_name] = {"type": param_type}
        
        # 如果没有默认值，则为必需参数
        if param.default == inspect.Parameter.empty:
            required.append(param_name)
    
    return types.Tool(
        name=name,
        description=doc.split('\n')[0] if doc else f"Tool: {name}",
        inputSchema={
            "type": "object",
            "properties": properties,
            "required": required
        }
    )

def _discover_and_cache_tools():
    """
    发现所有工具模块中的函数并缓存它们的定义和实现。
    这个函数只应该在启动时被调用一次。
    """
    if _tool_functions:  # 如果已经发现过，则直接返回
        return

    logger.info("开始首次发现并缓存所有工具...")
    package = importlib.import_module('src.any2markdown_mcp.tools')
    
    for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
        if "base_tool" in module_name or "tool_registry" in module_name:
            continue
            
        try:
            module = importlib.import_module(module_name)
            for name, func in inspect.getmembers(module, inspect.iscoroutinefunction):
                if name.startswith('_'):
                    continue
                
                logger.info(f"在 {module_name} 中发现工具: {name}")
                _tool_functions[name] = func
                
                # 从函数签名和docstring生成工具定义
                try:
                    tool_def = _create_tool_definition(name, func)
                    _tool_definitions.append(tool_def)
                    logger.info(f"为工具 '{name}' 生成了定义。")
                except Exception as e:
                     logger.error(f"为工具 '{name}' 生成定义时出错: {e}. 可能缺少类型提示或docstring。")

        except Exception as e:
            logger.error(f"加载模块 {module_name} 时出错: {e}", exc_info=True)

    logger.info(f"工具发现完成。共找到 {len(_tool_definitions)} 个工具。")


def register_tools_with_server(server: Server):
    """
    将发现的工具注册到 Server 实例上。
    """
    # 确保工具已经被发现和缓存
    _discover_and_cache_tools()

    @server.list_tools()
    async def list_tools_handler() -> list[types.Tool]:
        """
        提供所有可用工具的列表。
        """
        logger.info(f"正在提供工具列表，共 {len(_tool_definitions)} 个工具。")
        return _tool_definitions

    @server.call_tool()
    async def call_tool_handler(name: str, arguments: dict | None) -> list[types.ContentBlock]:
        """
        根据名称和参数调用一个工具。
        """
        logger.info(f"接收到工具调用请求: {name}, 参数: {arguments}")
        
        tool_func = _tool_functions.get(name)
        if not tool_func:
            logger.error(f"未找到名为 '{name}' 的工具。")
            raise McpError(f"Tool not found: {name}")

        try:
            # 确保参数不为None
            args = arguments or {}
            result = await tool_func(**args)

            # 将结果包装在 TextContent 中
            if isinstance(result, str):
                 return [types.TextContent(type="text", text=result)]
            elif isinstance(result, dict):
                 return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                 return [types.TextContent(type="text", text=str(result))]

        except Exception as e:
            logger.error(f"执行工具 '{name}' 时出错: {e}", exc_info=True)
            # MCP Server 会自动处理异常
            raise 