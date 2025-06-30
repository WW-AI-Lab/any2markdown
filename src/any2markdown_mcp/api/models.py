"""
API 数据模型

定义RESTful API的请求和响应数据结构
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field
import uuid


class APIResponse(BaseModel):
    """统一的API响应格式"""
    success: bool = Field(description="操作是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")
    message: str = Field(description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间戳")
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="请求ID")


class APIError(BaseModel):
    """API错误信息"""
    code: str = Field(description="错误代码")
    message: str = Field(description="错误消息")
    details: Optional[Union[str, Dict[str, Any]]] = Field(None, description="错误详情")


class APIErrorResponse(BaseModel):
    """API错误响应格式"""
    success: bool = Field(False, description="操作失败")
    error: APIError = Field(description="错误信息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间戳")
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="请求ID")


# 统一转换请求模型
class UnifiedConvertOptions(BaseModel):
    """统一转换选项"""
    output_format: Literal["markdown", "html", "json"] = Field(default="markdown", description="输出格式")
    extract_images: bool = Field(default=True, description="是否提取图片")
    remove_header_footer: bool = Field(default=True, description="是否移除页眉页脚")
    include_content: bool = Field(default=True, description="是否包含markdown内容")
    
    # PDF特定选项
    paginate_output: Optional[bool] = Field(None, description="是否分页输出(PDF)")
    start_page: Optional[int] = Field(None, description="起始页码(PDF)")
    end_page: Optional[int] = Field(None, description="结束页码(PDF)")
    languages: Optional[List[str]] = Field(None, description="语言列表(PDF)")
    
    # Word特定选项
    preserve_formatting: Optional[bool] = Field(None, description="是否保留格式(Word)")
    
    # Excel特定选项
    include_formulas: Optional[bool] = Field(None, description="是否包含公式(Excel)")
    sheet_names: Optional[List[str]] = Field(None, description="指定工作表名称(Excel)")


class ConvertFileInfo(BaseModel):
    """转换文件信息"""
    filename: str = Field(description="文件名")
    file_content: Optional[str] = Field(None, description="Base64编码的文件内容(JSON方式)")
    options: Optional[UnifiedConvertOptions] = Field(None, description="文件特定选项")


class UnifiedConvertRequest(BaseModel):
    """统一转换请求(JSON方式)"""
    files: List[ConvertFileInfo] = Field(description="文件列表")
    global_options: Optional[UnifiedConvertOptions] = Field(None, description="全局选项")


# 保留旧模型以兼容现有代码
class DocumentInfo(BaseModel):
    """批量转换中的单个文档信息(已废弃，使用ConvertFileInfo)"""
    file_content: str = Field(description="Base64编码的文件内容")
    filename: str = Field(description="文件名")
    options: Optional[Dict[str, Any]] = Field(None, description="文档特定选项")


class BatchConvertRequest(BaseModel):
    """批量转换请求(已废弃，使用UnifiedConvertRequest)"""
    documents: List[DocumentInfo] = Field(description="文档列表")
    global_options: Optional[Dict[str, Any]] = Field(None, description="全局选项")


class ValidateRequest(BaseModel):
    """文档验证请求"""
    file_content: str = Field(description="Base64编码的文件内容")
    filename: str = Field(description="文件名")


# 响应数据模型
class ImageInfo(BaseModel):
    """图片信息"""
    filename: str = Field(description="图片文件名")
    url: str = Field(description="图片URL")
    size: int = Field(description="图片大小(字节)")
    page: Optional[int] = Field(None, description="页码")
    index: int = Field(description="图片索引")


class ConvertMetadata(BaseModel):
    """转换元数据"""
    total_pages: Optional[int] = Field(None, description="总页数")
    images_extracted: int = Field(description="提取的图片数量")
    detected_language: Optional[str] = Field(None, description="检测到的语言")
    processing_time: float = Field(description="处理时间(秒)")
    file_size: int = Field(description="文件大小(字节)")
    options_used: Dict[str, Any] = Field(description="使用的选项")


class ConvertResult(BaseModel):
    """转换结果"""
    markdown_content: Optional[str] = Field(None, description="Markdown内容")
    metadata: ConvertMetadata = Field(description="转换元数据")
    images: List[ImageInfo] = Field(default=[], description="图片列表")


class BatchConvertResult(BaseModel):
    """批量转换结果"""
    filename: str = Field(description="文件名")
    success: bool = Field(description="是否成功")
    data: Optional[ConvertResult] = Field(None, description="转换结果")
    error: Optional[str] = Field(None, description="错误信息")


class BatchConvertSummary(BaseModel):
    """批量转换汇总"""
    total: int = Field(description="总文档数")
    successful: int = Field(description="成功数")
    failed: int = Field(description="失败数")
    processing_time: float = Field(description="总处理时间")


class BatchConvertData(BaseModel):
    """批量转换数据"""
    results: List[BatchConvertResult] = Field(description="转换结果列表")
    summary: BatchConvertSummary = Field(description="转换汇总")


class StructureAnalysis(BaseModel):
    """结构分析结果"""
    headers: int = Field(description="标题数量")
    paragraphs: int = Field(description="段落数量")
    images: int = Field(description="图片数量")
    tables: int = Field(description="表格数量")


class PDFAnalysisResult(BaseModel):
    """PDF分析结果"""
    total_pages: int = Field(description="总页数")
    has_images: bool = Field(description="是否包含图片")
    has_tables: bool = Field(description="是否包含表格")
    estimated_processing_time: float = Field(description="预估处理时间")
    detected_language: Optional[str] = Field(None, description="检测到的语言")
    file_size: int = Field(description="文件大小")
    structure_analysis: StructureAnalysis = Field(description="结构分析")


class ValidationResult(BaseModel):
    """验证结果"""
    is_valid: bool = Field(description="是否有效")
    file_type: str = Field(description="文件类型")
    file_size: int = Field(description="文件大小")
    estimated_processing_time: float = Field(description="预估处理时间")
    supported_features: List[str] = Field(description="支持的功能")
    warnings: List[str] = Field(default=[], description="警告信息")


class SystemInfo(BaseModel):
    """系统信息"""
    cpu_usage: float = Field(description="CPU使用率")
    memory_usage: float = Field(description="内存使用率")
    disk_usage: float = Field(description="磁盘使用率")


class StatusResult(BaseModel):
    """系统状态结果"""
    service: str = Field(description="服务名称")
    version: str = Field(description="版本号")
    status: str = Field(description="状态")
    uptime: int = Field(description="运行时间(秒)")
    system_info: SystemInfo = Field(description="系统信息")
    active_jobs: int = Field(description="活跃任务数")
    total_processed: int = Field(description="总处理数")
    supported_formats: List[str] = Field(description="支持的格式")


class FormatInfo(BaseModel):
    """格式信息"""
    extension: str = Field(description="文件扩展名")
    mime_type: str = Field(description="MIME类型")
    max_size: str = Field(description="最大文件大小")
    features: List[str] = Field(description="支持的功能")


class FormatsResult(BaseModel):
    """支持格式结果"""
    input_formats: List[FormatInfo] = Field(description="输入格式")
    output_formats: List[str] = Field(description="输出格式")


# 错误代码枚举
class ErrorCode:
    """API错误代码"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    PROCESSING_FAILED = "PROCESSING_FAILED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    UNAUTHORIZED = "UNAUTHORIZED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# HTTP状态码映射
STATUS_CODE_MAP = {
    ErrorCode.VALIDATION_ERROR: 400,
    ErrorCode.UNSUPPORTED_FORMAT: 400,
    ErrorCode.FILE_TOO_LARGE: 413,
    ErrorCode.PROCESSING_FAILED: 422,
    ErrorCode.RATE_LIMIT_EXCEEDED: 429,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.INTERNAL_ERROR: 500,
} 