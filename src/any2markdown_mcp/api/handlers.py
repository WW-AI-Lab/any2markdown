"""
API 处理器

实现所有RESTful API端点的处理逻辑
"""

import time
import psutil
from pathlib import Path
from typing import Dict, Any, Optional, List
import uuid
import base64

from fastapi import Request, Response, UploadFile, Form, File

from .models import (
    BatchConvertRequest, ValidateRequest,
    ConvertResult, BatchConvertData, PDFAnalysisResult,
    ValidationResult, StatusResult, FormatsResult,
    FormatInfo, SystemInfo, UnifiedConvertOptions, UnifiedConvertRequest
)
from .utils import (
    parse_request_body, format_api_response, format_error_response,
    create_json_response, extract_request_id, log_api_request, log_api_response,
    map_batch_request_to_mcp_params, map_validate_request_to_mcp_params, 
    validate_file_size, validate_file_format
)
from ..tools.pdf_tools import convert_pdf_to_markdown, analyze_pdf_structure
from ..tools.word_tools import convert_word_to_markdown
from ..tools.excel_tools import convert_excel_to_markdown
from ..tools.utility_tools import batch_convert_documents, get_system_status, validate_document
from ..logger import get_logger
from ..config import settings

logger = get_logger(__name__)

# 服务启动时间
_start_time = time.time()
_total_processed = 0


# 旧的处理器函数已移除，现在使用统一的handle_unified_convert


async def handle_batch_convert(request: Request) -> Response:
    """处理批量转换API"""
    start_time = time.time()
    request_id = extract_request_id(request)
    log_api_request(request, request_id)
    
    try:
        # 解析请求体
        batch_request = await parse_request_body(request, BatchConvertRequest)
        
        # 验证每个文档
        for doc in batch_request.documents:
            validate_file_size(doc.file_content)
            # 从文件名推断格式并验证
            file_ext = doc.filename.lower().split('.')[-1]
            if file_ext == 'pdf':
                validate_file_format(doc.filename, ["pdf"])
            elif file_ext in ['docx', 'doc']:
                validate_file_format(doc.filename, ["docx", "doc"])
            elif file_ext in ['xlsx', 'xls']:
                validate_file_format(doc.filename, ["xlsx", "xls"])
            else:
                validate_file_format(doc.filename, ["pdf", "docx", "doc", "xlsx", "xls"])
        
        # 映射参数并调用MCP工具
        mcp_params = map_batch_request_to_mcp_params(batch_request)
        result = await batch_convert_documents(**mcp_params)
        
        # 格式化响应
        response_data = format_api_response(
            data=result,
            message="批量转换完成",
            request_id=request_id
        )
        
        processing_time = time.time() - start_time
        log_api_response(request_id, 200, processing_time)
        
        global _total_processed
        _total_processed += len(batch_request.documents)
        
        return create_json_response(response_data)
        
    except Exception as e:
        error_data, status_code = format_error_response(
            e, request_id, include_traceback=settings.debug
        )
        processing_time = time.time() - start_time
        log_api_response(request_id, status_code, processing_time)
        
        return create_json_response(error_data, status_code)


async def handle_pdf_analyze(request: Request) -> Response:
    """处理PDF分析API"""
    start_time = time.time()
    request_id = extract_request_id(request)
    log_api_request(request, request_id)
    
    try:
        # 从查询参数获取文件内容和文件名
        file_content = request.query_params.get("file_content")
        filename = request.query_params.get("filename", "document.pdf")
        
        if not file_content:
            raise ValueError("缺少必需参数: file_content")
        
        # 验证文件
        validate_file_size(file_content)
        validate_file_format(filename, ["pdf"])
        
        # 调用MCP工具
        result = await analyze_pdf_structure(
            file_content=file_content,
            filename=filename
        )
        
        # 格式化响应
        response_data = format_api_response(
            data=result,
            message="PDF分析完成",
            request_id=request_id
        )
        
        processing_time = time.time() - start_time
        log_api_response(request_id, 200, processing_time)
        
        return create_json_response(response_data)
        
    except Exception as e:
        error_data, status_code = format_error_response(
            e, request_id, include_traceback=settings.debug
        )
        processing_time = time.time() - start_time
        log_api_response(request_id, status_code, processing_time)
        
        return create_json_response(error_data, status_code)


async def handle_validate(request: Request) -> Response:
    """处理文档验证API"""
    start_time = time.time()
    request_id = extract_request_id(request)
    log_api_request(request, request_id)
    
    try:
        # 解析请求体
        validate_request = await parse_request_body(request, ValidateRequest)
        
        # 映射参数并调用MCP工具
        mcp_params = map_validate_request_to_mcp_params(validate_request)
        result = await validate_document(**mcp_params)
        
        # 格式化响应
        response_data = format_api_response(
            data=result,
            message="文档验证完成",
            request_id=request_id
        )
        
        processing_time = time.time() - start_time
        log_api_response(request_id, 200, processing_time)
        
        return create_json_response(response_data)
        
    except Exception as e:
        error_data, status_code = format_error_response(
            e, request_id, include_traceback=settings.debug
        )
        processing_time = time.time() - start_time
        log_api_response(request_id, status_code, processing_time)
        
        return create_json_response(error_data, status_code)


async def handle_status(request: Request) -> Response:
    """处理系统状态API"""
    start_time = time.time()
    request_id = extract_request_id(request)
    log_api_request(request, request_id)
    
    try:
        # 获取系统信息
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 计算运行时间
        uptime = int(time.time() - _start_time)
        
        # 构建状态数据
        status_data = {
            "service": "any2markdown-mcp-server",
            "version": "1.0.0",
            "status": "healthy",
            "uptime": uptime,
            "system_info": {
                "cpu_usage": round(cpu_percent, 1),
                "memory_usage": round(memory.percent, 1),
                "disk_usage": round(disk.percent, 1)
            },
            "active_jobs": 0,  # TODO: 实现任务跟踪
            "total_processed": _total_processed,
            "supported_formats": ["pdf", "docx", "doc", "xlsx", "xls"]
        }
        
        # 格式化响应
        response_data = format_api_response(
            data=status_data,
            message="系统状态正常",
            request_id=request_id
        )
        
        processing_time = time.time() - start_time
        log_api_response(request_id, 200, processing_time)
        
        return create_json_response(response_data)
        
    except Exception as e:
        error_data, status_code = format_error_response(
            e, request_id, include_traceback=settings.debug
        )
        processing_time = time.time() - start_time
        log_api_response(request_id, status_code, processing_time)
        
        return create_json_response(error_data, status_code)


async def handle_formats(request: Request) -> Response:
    """处理支持格式API"""
    start_time = time.time()
    request_id = extract_request_id(request)
    log_api_request(request, request_id)
    
    try:
        # 构建格式数据
        formats_data = {
            "input_formats": [
                {
                    "extension": "pdf",
                    "mime_type": "application/pdf",
                    "max_size": "100MB",
                    "features": ["text", "images", "tables", "headers", "footers"]
                },
                {
                    "extension": "docx",
                    "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "max_size": "50MB",
                    "features": ["text", "images", "equations", "headers", "footers"]
                },
                {
                    "extension": "doc",
                    "mime_type": "application/msword",
                    "max_size": "50MB",
                    "features": ["text", "images", "basic_formatting"]
                },
                {
                    "extension": "xlsx",
                    "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "max_size": "30MB",
                    "features": ["text", "images", "formulas", "charts"]
                },
                {
                    "extension": "xls",
                    "mime_type": "application/vnd.ms-excel",
                    "max_size": "30MB",
                    "features": ["text", "basic_formulas"]
                }
            ],
            "output_formats": ["markdown", "html", "json"]
        }
        
        # 格式化响应
        response_data = format_api_response(
            data=formats_data,
            message="支持格式列表",
            request_id=request_id
        )
        
        processing_time = time.time() - start_time
        log_api_response(request_id, 200, processing_time)
        
        return create_json_response(response_data)
        
    except Exception as e:
        error_data, status_code = format_error_response(
            e, request_id, include_traceback=settings.debug
        )
        processing_time = time.time() - start_time
        log_api_response(request_id, status_code, processing_time)
        
        return create_json_response(error_data, status_code)


async def handle_docs(request: Request) -> Response:
    """处理API文档页面"""
    # 简单的Swagger UI HTML页面
    swagger_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Any2Markdown API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css" />
        <style>
            html {{
                box-sizing: border-box;
                overflow: -moz-scrollbars-vertical;
                overflow-y: scroll;
            }}
            *, *:before, *:after {{
                box-sizing: inherit;
            }}
            body {{
                margin:0;
                background: #fafafa;
            }}
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
        <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {{
                const ui = SwaggerUIBundle({{
                    url: '/api/v1/openapi.json',
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout"
                }});
            }};
        </script>
    </body>
    </html>
    """
    
    return Response(content=swagger_html, media_type="text/html")


async def handle_openapi(request: Request) -> Response:
    """处理OpenAPI规范"""
    # 生成OpenAPI规范
    openapi_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Any2Markdown API",
            "description": "将PDF、Word、Excel文档转换为Markdown格式的RESTful API",
            "version": "1.0.0",
            "contact": {
                "name": "Any2Markdown MCP Server",
                "url": f"http://{settings.host}:{settings.port}"
            }
        },
        "servers": [
            {
                "url": f"http://{settings.host}:{settings.port}/api/v1",
                "description": "开发服务器"
            }
        ],
        "paths": {
            "/convert": {
                "post": {
                    "summary": "统一文档转换",
                    "description": "支持PDF、Word、Excel文档转换，可以单文件或多文件上传，支持JSON和multipart/form-data两种方式",
                    "tags": ["转换"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UnifiedConvertRequest"},
                                "examples": {
                                    "single_file": {
                                        "summary": "单文件转换",
                                        "value": {
                                            "files": [
                                                {
                                                    "filename": "document.pdf",
                                                    "file_content": "base64-encoded-content",
                                                    "options": {
                                                        "output_format": "markdown",
                                                        "extract_images": True
                                                    }
                                                }
                                            ]
                                        }
                                    },
                                    "multi_file": {
                                        "summary": "多文件转换",
                                        "value": {
                                            "files": [
                                                {
                                                    "filename": "doc1.pdf",
                                                    "file_content": "base64-content-1"
                                                },
                                                {
                                                    "filename": "doc2.docx",
                                                    "file_content": "base64-content-2"
                                                }
                                            ],
                                            "global_options": {
                                                "output_format": "markdown",
                                                "include_content": False
                                            }
                                        }
                                    }
                                }
                            },
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "file": {
                                            "type": "string",
                                            "format": "binary",
                                            "description": "单文件上传"
                                        },
                                        "file1": {
                                            "type": "string", 
                                            "format": "binary",
                                            "description": "多文件上传字段1"
                                        },
                                        "file2": {
                                            "type": "string",
                                            "format": "binary", 
                                            "description": "多文件上传字段2"
                                        },
                                        "output_format": {
                                            "type": "string",
                                            "enum": ["markdown", "html", "json"],
                                            "default": "markdown"
                                        },
                                        "extract_images": {
                                            "type": "boolean",
                                            "default": True
                                        },
                                        "include_content": {
                                            "type": "boolean",
                                            "default": True
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "转换成功",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIResponse"}
                                }
                            }
                        },
                        "400": {
                            "description": "请求错误",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/analyze/pdf": {
                "get": {
                    "summary": "PDF结构分析",
                    "tags": ["分析"],
                    "parameters": [
                        {
                            "name": "file_content",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Base64编码的PDF内容"
                        },
                        {
                            "name": "filename",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string", "default": "document.pdf"},
                            "description": "文件名"
                        }
                    ],
                    "responses": {
                        "200": {"description": "分析完成"},
                        "400": {"description": "请求错误"}
                    }
                }
            },
            "/validate": {
                "post": {
                    "summary": "文档验证",
                    "tags": ["工具"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ValidateRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "验证完成"},
                        "400": {"description": "请求错误"}
                    }
                }
            },
            "/status": {
                "get": {
                    "summary": "系统状态",
                    "tags": ["系统"],
                    "responses": {
                        "200": {"description": "状态正常"}
                    }
                }
            },
            "/formats": {
                "get": {
                    "summary": "支持格式列表",
                    "tags": ["系统"],
                    "responses": {
                        "200": {"description": "格式列表"}
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "UnifiedConvertRequest": {
                    "type": "object",
                    "required": ["files"],
                    "properties": {
                        "files": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/ConvertFileInfo"},
                            "description": "要转换的文件列表"
                        },
                        "global_options": {
                            "$ref": "#/components/schemas/UnifiedConvertOptions",
                            "description": "全局转换选项"
                        }
                    }
                },
                "ConvertFileInfo": {
                    "type": "object",
                    "required": ["filename"],
                    "properties": {
                        "filename": {"type": "string", "description": "文件名"},
                        "file_content": {"type": "string", "description": "Base64编码的文件内容(JSON方式必需)"},
                        "options": {
                            "$ref": "#/components/schemas/UnifiedConvertOptions",
                            "description": "文件特定选项"
                        }
                    }
                },
                "UnifiedConvertOptions": {
                    "type": "object",
                    "properties": {
                        "output_format": {"type": "string", "enum": ["markdown", "html", "json"], "default": "markdown"},
                        "extract_images": {"type": "boolean", "default": True},
                        "remove_header_footer": {"type": "boolean", "default": True},
                        "include_content": {"type": "boolean", "default": True},
                        "paginate_output": {"type": "boolean", "description": "是否分页输出(PDF)"},
                        "start_page": {"type": "integer", "description": "起始页码(PDF)"},
                        "end_page": {"type": "integer", "description": "结束页码(PDF)"},
                        "languages": {"type": "array", "items": {"type": "string"}, "description": "语言列表(PDF)"},
                        "preserve_formatting": {"type": "boolean", "description": "是否保留格式(Word)"},
                        "include_formulas": {"type": "boolean", "description": "是否包含公式(Excel)"},
                        "sheet_names": {"type": "array", "items": {"type": "string"}, "description": "指定工作表名称(Excel)"}
                    }
                },
                "ValidateRequest": {
                    "type": "object",
                    "required": ["file_content", "filename"],
                    "properties": {
                        "file_content": {"type": "string"},
                        "filename": {"type": "string"}
                    }
                },
                "APIResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {"type": "object"},
                        "message": {"type": "string"},
                        "timestamp": {"type": "string", "format": "date-time"},
                        "request_id": {"type": "string"}
                    }
                },
                "APIErrorResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "default": False},
                        "error": {"$ref": "#/components/schemas/APIError"},
                        "timestamp": {"type": "string", "format": "date-time"},
                        "request_id": {"type": "string"}
                    }
                },
                "APIError": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "message": {"type": "string"},
                        "details": {"oneOf": [{"type": "string"}, {"type": "object"}]}
                    }
                }
            }
        }
    }
    
    return create_json_response(openapi_spec)


# 旧的文件上传处理器已移除，现在使用统一的handle_unified_convert


# 统一转换处理器
async def handle_unified_convert(request: Request) -> Response:
    """处理统一转换API - 支持多文件上传和JSON方式"""
    start_time = time.time()
    request_id = extract_request_id(request)
    log_api_request(request, request_id)
    
    try:
        content_type = request.headers.get("content-type", "")
        
        if content_type.startswith("multipart/form-data"):
            # multipart/form-data 文件上传方式
            return await _handle_multipart_convert(request, request_id, start_time)
        else:
            # JSON 方式
            return await _handle_json_convert(request, request_id, start_time)
            
    except Exception as e:
        error_data, status_code = format_error_response(
            e, request_id, include_traceback=settings.debug
        )
        processing_time = time.time() - start_time
        log_api_response(request_id, status_code, processing_time)
        
        return create_json_response(error_data, status_code)


async def _handle_multipart_convert(request: Request, request_id: str, start_time: float) -> Response:
    """处理multipart/form-data文件上传"""
    # 解析multipart数据
    form = await request.form()
    
    # 获取上传的文件
    files = []
    file_fields = [key for key in form.keys() if key.startswith('file')]
    
    if not file_fields:
        # 检查是否有单个文件字段
        if 'file' in form:
            file_fields = ['file']
        else:
            raise ValueError("至少需要上传一个文件")
    
    # 解析全局选项
    global_options = _parse_form_options(form)
    
    # 处理每个文件
    results = []
    for field_name in file_fields:
        file = form.get(field_name)
        if not file or not hasattr(file, 'filename'):
            continue
            
        # 读取文件内容
        file_content = await file.read()
        file_b64 = base64.b64encode(file_content).decode()
        
        # 验证文件
        validate_file_size(file_b64)
        
        # 根据文件扩展名确定类型和调用相应的转换函数
        result = await _convert_single_file(
            filename=file.filename,
            file_content=file_b64,
            options=global_options,
            request_id=request_id
        )
        results.append(result)
    
    # 构建响应
    if len(results) == 1:
        # 单文件：直接返回结果
        response_data = format_api_response(
            data=results[0],
            message="文件转换成功",
            request_id=request_id
        )
    else:
        # 多文件：返回批量结果
        successful = sum(1 for r in results if r.get('conversion_info', {}).get('status') == 'success')
        failed = len(results) - successful
        
        batch_data = {
            "results": results,
            "summary": {
                "total": len(results),
                "successful": successful,
                "failed": failed,
                "processing_time": time.time() - start_time
            }
        }
        
        response_data = format_api_response(
            data=batch_data,
            message=f"批量转换完成: {successful}成功, {failed}失败",
            request_id=request_id
        )
    
    processing_time = time.time() - start_time
    log_api_response(request_id, 200, processing_time)
    
    global _total_processed
    _total_processed += len(results)
    
    return create_json_response(response_data)


async def _handle_json_convert(request: Request, request_id: str, start_time: float) -> Response:
    """处理JSON方式转换"""
    # 解析请求体
    convert_request = await parse_request_body(request, UnifiedConvertRequest)
    
    # 验证文件
    for file_info in convert_request.files:
        if not file_info.file_content:
            raise ValueError(f"文件 {file_info.filename} 缺少file_content")
        validate_file_size(file_info.file_content)
    
    # 处理每个文件
    results = []
    for file_info in convert_request.files:
        # 合并选项：文件选项覆盖全局选项
        merged_options = convert_request.global_options or UnifiedConvertOptions()
        if file_info.options:
            # 合并选项
            for field, value in file_info.options.dict(exclude_unset=True).items():
                setattr(merged_options, field, value)
        
        result = await _convert_single_file(
            filename=file_info.filename,
            file_content=file_info.file_content,
            options=merged_options,
            request_id=request_id
        )
        results.append(result)
    
    # 构建响应
    if len(results) == 1:
        # 单文件：直接返回结果
        response_data = format_api_response(
            data=results[0],
            message="文件转换成功",
            request_id=request_id
        )
    else:
        # 多文件：返回批量结果
        successful = sum(1 for r in results if r.get('conversion_info', {}).get('status') == 'success')
        failed = len(results) - successful
        
        batch_data = {
            "results": results,
            "summary": {
                "total": len(results),
                "successful": successful,
                "failed": failed,
                "processing_time": time.time() - start_time
            }
        }
        
        response_data = format_api_response(
            data=batch_data,
            message=f"批量转换完成: {successful}成功, {failed}失败",
            request_id=request_id
        )
    
    processing_time = time.time() - start_time
    log_api_response(request_id, 200, processing_time)
    
    global _total_processed
    _total_processed += len(results)
    
    return create_json_response(response_data)


async def _convert_single_file(filename: str, file_content: str, options, request_id: str) -> Dict[str, Any]:
    """转换单个文件"""
    try:
        # 根据文件扩展名确定文件类型
        file_ext = filename.lower().split('.')[-1]
        
        if file_ext == 'pdf':
            validate_file_format(filename, ["pdf"])
            
            # 准备PDF参数
            pdf_params = {
                "file_content": file_content,
                "filename": filename,
                "output_format": options.output_format,
                "paginate_output": options.paginate_output if options.paginate_output is not None else True,
                "extract_images": options.extract_images,
                "remove_header_footer": options.remove_header_footer,
                "start_page": options.start_page if options.start_page is not None else 0,
                "end_page": options.end_page,
                "languages": options.languages if options.languages else ["auto"],
                "include_content": options.include_content
            }
            
            result = await convert_pdf_to_markdown(**pdf_params)
            
        elif file_ext in ['docx', 'doc']:
            validate_file_format(filename, ["docx", "doc"])
            
            # 准备Word参数
            word_params = {
                "file_content": file_content,
                "filename": filename,
                "output_format": options.output_format,
                "extract_images": options.extract_images,
                "remove_header_footer": options.remove_header_footer,
                "preserve_formatting": options.preserve_formatting if options.preserve_formatting is not None else True,
                "include_content": options.include_content
            }
            
            result = await convert_word_to_markdown(**word_params)
            
        elif file_ext in ['xlsx', 'xls']:
            validate_file_format(filename, ["xlsx", "xls"])
            
            # 准备Excel参数
            excel_params = {
                "file_content": file_content,
                "filename": filename,
                "output_format": options.output_format,
                "sheet_names": options.sheet_names,
                "include_formulas": options.include_formulas if options.include_formulas is not None else True,
                "include_content": options.include_content
            }
            
            result = await convert_excel_to_markdown(**excel_params)
            
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")
        
        return result
        
    except Exception as e:
        logger.error(f"[{request_id}] 文件 {filename} 转换失败: {str(e)}")
        return {
            "conversion_info": {
                "status": "error",
                "filename": filename,
                "error": str(e)
            },
            "metadata": {}
        }


def _parse_form_options(form) -> 'UnifiedConvertOptions':
    """从表单数据解析转换选项"""
    def get_bool(key: str, default: bool = True) -> bool:
        value = form.get(key)
        if value is None:
            return default
        return str(value).lower() in ('true', '1', 'yes', 'on')
    
    def get_int(key: str, default: Optional[int] = None) -> Optional[int]:
        value = form.get(key)
        if value is None or value == '':
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def get_str_list(key: str) -> Optional[List[str]]:
        value = form.get(key)
        if not value:
            return None
        return [item.strip() for item in str(value).split(',') if item.strip()]
    
    return UnifiedConvertOptions(
        output_format=form.get("output_format", "markdown"),
        extract_images=get_bool("extract_images", True),
        remove_header_footer=get_bool("remove_header_footer", True),
        include_content=get_bool("include_content", True),
        # PDF特定选项
        paginate_output=get_bool("paginate_output", True) if form.get("paginate_output") else None,
        start_page=get_int("start_page", 0) if form.get("start_page") else None,
        end_page=get_int("end_page") if form.get("end_page") else None,
        languages=get_str_list("languages"),
        # Word特定选项
        preserve_formatting=get_bool("preserve_formatting", True) if form.get("preserve_formatting") else None,
        # Excel特定选项
        include_formulas=get_bool("include_formulas", True) if form.get("include_formulas") else None,
        sheet_names=get_str_list("sheet_names")
    ) 