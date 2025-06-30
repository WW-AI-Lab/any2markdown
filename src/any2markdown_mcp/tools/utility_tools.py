"""
实用工具 (函数式实现)
"""

import asyncio
import base64
import json
import time
import platform
import psutil
from typing import Any, Dict, List, Literal

import structlog
from pydantic import BaseModel, Field

from ..processors import PDFProcessor, WordProcessor, ExcelProcessor
from ..config import settings
from .base_tool import file_content_field

logger = structlog.get_logger(__name__)

# --- Models for Batch Conversion ---

class DocumentToConvert(BaseModel):
    file_content: str = file_content_field
    file_type: Literal["pdf", "docx", "doc", "xlsx", "xls"]
    filename: str = "document"
    options: Dict[str, Any] = Field(default_factory=dict)

class GlobalConversionOptions(BaseModel):
    output_format: Literal["markdown", "html", "json"] = "markdown"
    max_concurrent: int = 3

class BatchConversionResult(BaseModel):
    successful_conversions: List[Dict]
    failed_conversions: List[Dict]

# --- Tool Implementations ---

async def batch_convert_documents(
    documents: List[DocumentToConvert],
    global_options: GlobalConversionOptions = Field(default_factory=GlobalConversionOptions)
) -> BatchConversionResult:
    """
    批量转换不同类型的多个文档。
    """
    logger.info("开始批量转换", doc_count=len(documents), options=global_options.model_dump())
    if not documents:
        raise ValueError("No documents provided for conversion.")

    semaphore = asyncio.Semaphore(global_options.max_concurrent)
    tasks = [
        _convert_single_document(semaphore, i, doc)
        for i, doc in enumerate(documents)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successful = []
    failed = []
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            failed.append({"index": i, "filename": documents[i].filename, "error": str(res)})
        else:
            successful.append({"index": i, "filename": documents[i].filename, "result": res})
    
    return BatchConversionResult(successful_conversions=successful, failed_conversions=failed)

async def _convert_single_document(
    semaphore: asyncio.Semaphore, index: int, doc: DocumentToConvert
) -> Dict[str, Any]:
    async with semaphore:
        logger.info(f"开始转换文档 {index}: {doc.filename}")
        file_ext = doc.file_type
        processor_map = {
            "pdf": PDFProcessor,
            "docx": WordProcessor, "doc": WordProcessor,
            "xlsx": ExcelProcessor, "xls": ExcelProcessor,
        }
        processor_class = processor_map.get(file_ext)
        if not processor_class:
            raise ValueError(f"Unsupported file type: {file_ext}")

        processor = processor_class(settings.model_dump())
        decoded_content = processor.decode_base64_content(doc.file_content)
        result = await processor.convert(decoded_content, doc.options)
        return result

async def get_system_status() -> dict:
    """
    获取系统状态，包括模型信息和资源使用情况。
    """
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    
    status = {
        "timestamp": time.time(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "cpu": {
            "physical_cores": psutil.cpu_count(logical=False),
            "total_cores": psutil.cpu_count(logical=True),
            "usage_percent": cpu_usage,
        },
        "memory": {
            "total_gb": round(memory_info.total / (1024**3), 2),
            "available_gb": round(memory_info.available / (1024**3), 2),
            "used_percent": memory_info.percent,
        },
        "mcp_server_config": {
            "host": settings.host,
            "port": settings.port,
            "log_level": settings.log_level,
            "max_concurrent_jobs": settings.max_concurrent_jobs,
        },
    }
    logger.info("获取系统状态", status=status)
    return status

async def validate_document(
    file_content: str = file_content_field,
    filename: str = ""
) -> dict:
    """
    验证文档是否可以被处理并提供元数据。
    """
    logger.info("开始验证文档", filename=filename)
    
    try:
        if not filename:
            raise ValueError("Filename is required for validation.")

        file_ext = filename.split('.')[-1].lower()
        if not settings.is_file_type_allowed(filename):
            raise ValueError(f"File type '{file_ext}' is not allowed.")

        decoded_content = base64.b64decode(file_content)
        
        if not settings.validate_file_size(len(decoded_content)):
            raise ValueError(f"File size exceeds maximum allowed size of {settings.max_file_size} bytes.")

        validation_map = {
            "pdf": PDFProcessor,
            "docx": WordProcessor, "doc": WordProcessor,
            "xlsx": ExcelProcessor, "xls": ExcelProcessor,
        }
        processor_class = validation_map.get(file_ext)
        
        if not processor_class:
            raise ValueError(f"No validator available for file type: {file_ext}")

        processor = processor_class(settings.model_dump())
        
        # 构建基本文档元数据
        basic_metadata = {
            "filename": filename,
            "file_type": file_ext,
            "file_size": len(decoded_content),
            "file_size_mb": round(len(decoded_content) / (1024 * 1024), 2)
        }
        
        # 构建标准JSON响应  
        response = {
            "is_valid": True,
            "file_type": file_ext,
            "metadata": basic_metadata
        }
        
        logger.info("文档验证成功", filename=filename, file_type=file_ext)
        return response
        
    except Exception as e:
        logger.error("文档验证失败", filename=filename, error=str(e))
        # 返回错误响应
        error_response = {
            "is_valid": False,
            "file_type": filename.split('.')[-1].lower() if filename else "unknown",
            "metadata": {
                "filename": filename,
                "error": str(e),
                "validation_status": "failed"
            }
        }
        return error_response 