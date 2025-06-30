"""
Word处理工具 (函数式实现)
"""
import base64
from typing import Optional, Literal

import structlog
from pydantic import Field

from ..processors import WordProcessor
from ..config import settings
from .base_tool import file_content_field

logger = structlog.get_logger(__name__)

async def convert_word_to_markdown(
    file_content: str = file_content_field,
    filename: str = "document.docx",
    output_format: Literal["markdown", "html", "json"] = "markdown",
    extract_images: bool = True,
    remove_header_footer: bool = True,
    paginate_output: bool = True,
    preserve_formatting: bool = True,
    include_content: bool = False
) -> dict:
    """
    将Word文档转换为Markdown格式。

    Args:
        file_content: Base64编码的Word文件内容。
        filename: 原始文件名。
        output_format: 输出格式 (markdown/html/json)。
        extract_images: 是否提取图片并生成URL。
        remove_header_footer: 是否移除页眉页脚。
        paginate_output: 是否分页输出。
        preserve_formatting: 是否保持格式。
        include_content: 是否在响应中包含markdown_content字段。

    Returns:
        转换后的Markdown内容（JSON格式）。
    """
    # 构建选项字典
    options = {
        "output_format": output_format,
        "extract_images": extract_images,
        "remove_header_footer": remove_header_footer,
        "paginate_output": paginate_output,
        "preserve_formatting": preserve_formatting
    }
    
    logger.info("开始执行Word到Markdown的转换", filename=filename)

    try:
        processor = WordProcessor(settings.model_dump())
        decoded_content = processor.decode_base64_content(file_content)
        
        logger.info("文件内容已解码", file_size=len(decoded_content))

        result = await processor.convert(decoded_content, options)

        # 构建标准JSON响应
        response = {
            "metadata": result.get("metadata", {}),
            "conversion_info": {
                "status": "success",
                "filename": filename,
                "format": result.get("format", "markdown"),
                "processor": "WordProcessor"
            }
        }
        
        # 根据include_content参数决定是否包含markdown_content字段
        if include_content:
            response["markdown_content"] = result.get("content", "")
        
        logger.info("Word转换成功", filename=filename, include_content=include_content)
        return response

    except Exception as e:
        logger.error("Word转换过程中发生错误", error=str(e), exc_info=True)
        # 返回错误响应
        error_response = {
            "metadata": {},
            "conversion_info": {
                "status": "error",
                "filename": filename,
                "error": str(e),
                "processor": "WordProcessor"
            }
        }
        
        # 错误时也根据include_content参数决定是否包含字段
        if include_content:
            error_response["markdown_content"] = ""
            
        return error_response 