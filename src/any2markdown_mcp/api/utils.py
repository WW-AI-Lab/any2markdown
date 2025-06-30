"""
API 工具函数

提供参数映射、响应格式化、错误处理等工具函数
"""

import json
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Response, Request
from pydantic import ValidationError

from .models import (
    APIResponse, APIErrorResponse, APIError, ErrorCode, STATUS_CODE_MAP,
    BatchConvertRequest, ValidateRequest
)
from ..logger import get_logger
from ..exceptions import MCPError, ToolError, ValidationError as MCPValidationError, ConversionError

logger = get_logger(__name__)


def generate_request_id() -> str:
    """生成请求ID"""
    return str(uuid.uuid4())


def format_api_response(
    data: Any,
    message: str = "操作成功",
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    格式化API成功响应
    
    Args:
        data: 响应数据
        message: 响应消息
        request_id: 请求ID
        
    Returns:
        格式化的响应字典
    """
    response = APIResponse(
        success=True,
        data=data,
        message=message,
        request_id=request_id or generate_request_id()
    )
    return response.model_dump()


def format_error_response(
    error: Exception,
    request_id: Optional[str] = None,
    include_traceback: bool = False
) -> tuple[Dict[str, Any], int]:
    """
    格式化API错误响应
    
    Args:
        error: 异常对象
        request_id: 请求ID
        include_traceback: 是否包含堆栈跟踪
        
    Returns:
        (响应字典, HTTP状态码)
    """
    # 确定错误代码和消息
    if isinstance(error, ValidationError):
        error_code = ErrorCode.VALIDATION_ERROR
        error_message = "请求参数验证失败"
        error_details = {
            "validation_errors": [
                {
                    "field": ".".join(str(loc) for loc in err["loc"]),
                    "message": err["msg"],
                    "type": err["type"]
                }
                for err in error.errors()
            ]
        }
    elif isinstance(error, MCPValidationError):
        error_code = ErrorCode.VALIDATION_ERROR
        error_message = str(error)
        error_details = None
    elif isinstance(error, ConversionError):
        error_code = ErrorCode.PROCESSING_FAILED
        error_message = "文档转换失败"
        error_details = str(error)
    elif isinstance(error, ToolError):
        error_code = ErrorCode.PROCESSING_FAILED
        error_message = "工具执行失败"
        error_details = str(error)
    elif isinstance(error, MCPError):
        error_code = ErrorCode.INTERNAL_ERROR
        error_message = "MCP服务器错误"
        error_details = str(error)
    else:
        error_code = ErrorCode.INTERNAL_ERROR
        error_message = "内部服务器错误"
        error_details = str(error) if include_traceback else None
    
    # 添加堆栈跟踪（仅在调试模式下）
    if include_traceback:
        if isinstance(error_details, dict):
            error_details["traceback"] = traceback.format_exc()
        else:
            error_details = {
                "message": error_details or str(error),
                "traceback": traceback.format_exc()
            }
    
    # 创建错误响应
    api_error = APIError(
        code=error_code,
        message=error_message,
        details=error_details
    )
    
    error_response = APIErrorResponse(
        error=api_error,
        request_id=request_id or generate_request_id()
    )
    
    # 获取HTTP状态码
    status_code = STATUS_CODE_MAP.get(error_code, 500)
    
    # 记录错误日志
    logger.error(
        "API错误",
        error_code=error_code,
        error_message=error_message,
        status_code=status_code,
        request_id=error_response.request_id,
        exc_info=True
    )
    
    return error_response.model_dump(), status_code


# 旧的映射函数已移除，现在使用统一的转换逻辑


def map_batch_request_to_mcp_params(request: BatchConvertRequest) -> Dict[str, Any]:
    """
    将批量转换请求映射为MCP参数
    
    Args:
        request: 批量转换请求
        
    Returns:
        MCP参数字典
    """
    documents = []
    for doc in request.documents:
        documents.append({
            "file_content": doc.file_content,
            "filename": doc.filename,
            "options": doc.options or {}
        })
    
    return {
        "documents": documents,
        "global_options": request.global_options or {}
    }


def map_validate_request_to_mcp_params(request: ValidateRequest) -> Dict[str, Any]:
    """
    将验证请求映射为MCP参数
    
    Args:
        request: 验证请求
        
    Returns:
        MCP参数字典
    """
    return {
        "file_content": request.file_content,
        "filename": request.filename
    }


async def parse_request_body(request: Request, model_class) -> Any:
    """
    解析请求体并验证
    
    Args:
        request: FastAPI请求对象
        model_class: Pydantic模型类
        
    Returns:
        验证后的模型实例
        
    Raises:
        ValidationError: 参数验证失败
    """
    try:
        body = await request.json()
        return model_class(**body)
    except json.JSONDecodeError as e:
        raise ValidationError([{
            "loc": ["body"],
            "msg": f"无效的JSON格式: {str(e)}",
            "type": "json_invalid"
        }])
    except Exception as e:
        raise ValidationError([{
            "loc": ["body"],
            "msg": f"请求体解析失败: {str(e)}",
            "type": "body_invalid"
        }])


class DateTimeEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理datetime对象"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def create_json_response(data: Dict[str, Any], status_code: int = 200) -> Response:
    """
    创建JSON响应
    
    Args:
        data: 响应数据
        status_code: HTTP状态码
        
    Returns:
        FastAPI响应对象
    """
    content = json.dumps(data, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
    return Response(
        content=content,
        media_type="application/json",
        status_code=status_code,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
    )


def extract_request_id(request: Request) -> Optional[str]:
    """
    从请求中提取请求ID
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        请求ID或None
    """
    # 从Header中获取
    request_id = request.headers.get("X-Request-ID")
    if request_id:
        return request_id
    
    # 从查询参数中获取
    request_id = request.query_params.get("request_id")
    if request_id:
        return request_id
    
    # 生成新的请求ID
    return generate_request_id()


def validate_file_size(file_content: str, max_size: int = 100 * 1024 * 1024) -> None:
    """
    验证文件大小
    
    Args:
        file_content: Base64编码的文件内容
        max_size: 最大文件大小（字节）
        
    Raises:
        ValidationError: 文件过大
    """
    # 估算Base64解码后的文件大小
    estimated_size = len(file_content) * 3 // 4
    
    if estimated_size > max_size:
        raise ValidationError([{
            "loc": ["file_content"],
            "msg": f"文件大小超过限制。最大允许: {max_size // (1024*1024)}MB，当前: {estimated_size // (1024*1024)}MB",
            "type": "file_too_large"
        }])


def validate_file_format(filename: str, allowed_formats: List[str]) -> None:
    """
    验证文件格式
    
    Args:
        filename: 文件名
        allowed_formats: 允许的格式列表
        
    Raises:
        ValidationError: 不支持的文件格式
    """
    if not filename:
        raise ValidationError([{
            "loc": ["filename"],
            "msg": "文件名不能为空",
            "type": "filename_required"
        }])
    
    file_ext = filename.lower().split('.')[-1]
    if file_ext not in allowed_formats:
        raise ValidationError([{
            "loc": ["filename"],
            "msg": f"不支持的文件格式: {file_ext}。支持的格式: {', '.join(allowed_formats)}",
            "type": "unsupported_format"
        }])


def log_api_request(request: Request, request_id: str) -> None:
    """
    记录API请求日志
    
    Args:
        request: FastAPI请求对象
        request_id: 请求ID
    """
    logger.info(
        "API请求",
        method=request.method,
        url=str(request.url),
        user_agent=request.headers.get("user-agent"),
        request_id=request_id
    )


def log_api_response(request_id: str, status_code: int, processing_time: float) -> None:
    """
    记录API响应日志
    
    Args:
        request_id: 请求ID
        status_code: HTTP状态码
        processing_time: 处理时间（秒）
    """
    logger.info(
        "API响应",
        request_id=request_id,
        status_code=status_code,
        processing_time=processing_time
    ) 