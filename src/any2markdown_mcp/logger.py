"""
日志系统模块

配置和管理Any2Markdown MCP Server的日志系统
使用structlog提供结构化日志
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import structlog
from structlog.stdlib import LoggerFactory


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    debug: bool = False
) -> None:
    """
    设置日志系统
    
    Args:
        log_level: 日志级别
        log_file: 日志文件路径
        debug: 是否启用调试模式
    """
    # 配置标准库日志
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )
    
    # 配置处理器链
    processors = [
        # 添加时间戳
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if debug:
        # 调试模式：更详细的输出
        processors.extend([
            structlog.processors.CallsiteParameterAdder(
                parameters=[structlog.processors.CallsiteParameter.FILENAME,
                          structlog.processors.CallsiteParameter.FUNC_NAME,
                          structlog.processors.CallsiteParameter.LINENO]
            ),
        ])
    
    # 添加最终渲染器
    if sys.stdout.isatty():
        # 终端模式：彩色输出
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        # 非终端模式：JSON输出
        processors.append(structlog.processors.JSONRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # 配置文件日志
    if log_file:
        setup_file_logging(log_file, log_level)
    
    # 获取根日志记录器并记录启动信息
    logger = structlog.get_logger("any2markdown_mcp")
    logger.info("Logging system initialized", 
                level=log_level, 
                file=log_file, 
                debug=debug)


def setup_file_logging(log_file: str, log_level: str) -> None:
    """
    设置文件日志
    
    Args:
        log_file: 日志文件路径
        log_level: 日志级别
    """
    from logging.handlers import RotatingFileHandler
    
    # 确保日志目录存在
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 创建文件处理器
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    
    # 设置文件日志格式
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 添加到根日志记录器
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        配置好的日志记录器
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """日志记录器混入类"""
    
    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """获取当前类的日志记录器"""
        return structlog.get_logger(self.__class__.__name__)


# 预定义的日志记录器
server_logger = structlog.get_logger("server")
processor_logger = structlog.get_logger("processor")
tool_logger = structlog.get_logger("tool")
model_logger = structlog.get_logger("model") 