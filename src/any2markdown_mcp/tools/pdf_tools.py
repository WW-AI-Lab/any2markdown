"""
PDF处理工具 (函数式实现)
"""
import base64
from typing import List, Optional, Literal, Dict, Any

import structlog
from pydantic import Field

from ..processors import PDFProcessor
from ..config import settings
from .base_tool import file_content_field

logger = structlog.get_logger(__name__)


def _detect_language_from_text(text: str) -> List[str]:
    """
    自动检测文本语言
    
    Args:
        text: 要检测的文本
        
    Returns:
        检测到的语言代码列表
    """
    if not text or len(text.strip()) < 10:
        # 文本太短，返回默认语言
        return ["en"]
    
    try:
        # 尝试使用langdetect库进行语言检测
        try:
            from langdetect import detect, detect_langs
            detected = detect(text)
            
            # 映射langdetect的语言代码到OCR支持的语言代码
            language_mapping = {
                'zh-cn': 'zh',
                'zh': 'zh', 
                'en': 'en',
                'ja': 'ja',
                'ko': 'ko',
                'fr': 'fr',
                'de': 'de',
                'es': 'es',
                'it': 'it',
                'pt': 'pt',
                'ru': 'ru',
                'ar': 'ar',
                'hi': 'hi',
                'th': 'th',
                'vi': 'vi'
            }
            
            mapped_lang = language_mapping.get(detected, 'en')
            logger.info("语言检测成功", detected_language=detected, mapped_language=mapped_lang)
            return [mapped_lang]
            
        except ImportError:
            # 如果langdetect不可用，尝试使用简单的字符检测
            logger.warning("langdetect库不可用，使用简单字符检测")
            return _simple_language_detection(text)
            
    except Exception as e:
        logger.warning("语言检测失败，使用默认语言", error=str(e))
        return ["en"]


def _simple_language_detection(text: str) -> List[str]:
    """
    基于字符的简单语言检测
    
    Args:
        text: 要检测的文本
        
    Returns:
        检测到的语言代码列表
    """
    # 统计不同语言字符的出现次数
    char_counts = {
        'zh': 0,  # 中文
        'ja': 0,  # 日文
        'ko': 0,  # 韩文
        'ar': 0,  # 阿拉伯文
        'ru': 0,  # 俄文
        'en': 0   # 英文/拉丁文
    }
    
    for char in text[:1000]:  # 只检查前1000个字符
        code_point = ord(char)
        
        # 中文字符范围
        if (0x4E00 <= code_point <= 0x9FFF or  # CJK统一汉字
            0x3400 <= code_point <= 0x4DBF):   # CJK扩展A
            char_counts['zh'] += 1
            
        # 日文字符范围
        elif (0x3040 <= code_point <= 0x309F or  # 平假名
              0x30A0 <= code_point <= 0x30FF):   # 片假名
            char_counts['ja'] += 1
            
        # 韩文字符范围
        elif (0xAC00 <= code_point <= 0xD7AF or  # 韩文音节
              0x1100 <= code_point <= 0x11FF):   # 韩文字母
            char_counts['ko'] += 1
            
        # 阿拉伯文字符范围
        elif (0x0600 <= code_point <= 0x06FF or  # 基本阿拉伯文
              0x0750 <= code_point <= 0x077F):   # 阿拉伯文补充
            char_counts['ar'] += 1
            
        # 西里尔字符范围（俄文等）
        elif (0x0400 <= code_point <= 0x04FF):
            char_counts['ru'] += 1
            
        # 拉丁字符范围（英文等）
        elif (0x0000 <= code_point <= 0x007F or  # 基本拉丁文
              0x0080 <= code_point <= 0x00FF):   # 拉丁文补充
            char_counts['en'] += 1
    
    # 找出字符数最多的语言
    max_lang = max(char_counts.items(), key=lambda x: x[1])
    
    if max_lang[1] > 0:
        logger.info("简单语言检测完成", detected_language=max_lang[0], char_count=max_lang[1])
        return [max_lang[0]]
    else:
        return ["en"]  # 默认英文


async def convert_pdf_to_markdown(
    file_content: str = file_content_field,
    filename: str = "document.pdf",
    output_format: Literal["markdown", "html", "json"] = "markdown",
    paginate_output: bool = True,
    extract_images: bool = True,
    remove_header_footer: bool = True,
    start_page: int = 0,
    end_page: Optional[int] = None,
    languages: Optional[List[str]] = None,
    batch_multiplier: int = 2,
    include_content: bool = False
) -> dict:
    """
    将PDF文档转换为Markdown格式。

    Args:
        file_content: Base64编码的PDF文件内容。
        filename: 原始文件名。
        output_format: 输出格式 (markdown/html/json)。
        paginate_output: 是否分页输出。
        extract_images: 是否提取图片并生成URL。
        remove_header_footer: 是否移除页眉页脚。
        start_page: 起始页码 (从0开始)。
        end_page: 结束页码 (不包含，None表示到最后一页)。
        languages: OCR识别语言列表，如果为None则自动检测。
        batch_multiplier: 批处理倍数。
        include_content: 是否在响应中包含markdown_content字段。

    Returns:
        转换后的Markdown内容（JSON格式）。
    """
    logger.info("开始执行PDF到Markdown的转换", filename=filename)

    try:
        processor = PDFProcessor(settings.model_dump())
        decoded_content = processor.decode_base64_content(file_content)
        
        # 如果没有指定语言，进行自动语言检测
        if languages is None:
            # 先快速提取一些文本进行语言检测
            try:
                import pymupdf
                temp_pdf_path = await processor.save_temp_file(decoded_content, suffix=".pdf")
                doc = pymupdf.open(str(temp_pdf_path))
                
                # 提取前几页的文本进行语言检测
                sample_text = ""
                for page_num in range(min(3, len(doc))):  # 最多检查前3页
                    page = doc[page_num]
                    page_text = page.get_text()
                    sample_text += page_text[:500]  # 每页最多取500字符
                    if len(sample_text) > 1000:  # 总共最多1000字符用于检测
                        break
                
                doc.close()
                await processor.cleanup_temp_files([str(temp_pdf_path)])
                
                # 自动检测语言
                detected_languages = _detect_language_from_text(sample_text)
                languages = detected_languages
                logger.info("自动检测到的语言", languages=languages)
                
            except Exception as e:
                logger.warning("语言自动检测失败，使用默认语言", error=str(e))
                languages = ["en"]
        
        # 构建选项字典
        options = {
            "output_format": output_format,
            "paginate_output": paginate_output,
            "extract_images": extract_images,
            "remove_header_footer": remove_header_footer,
            "start_page": start_page,
            "end_page": end_page,
            "languages": languages,
            "batch_multiplier": batch_multiplier
        }
        
        result = await processor.convert(decoded_content, options)

        # 构建标准JSON响应
        response = {
            "metadata": result.get("metadata", {}),
            "conversion_info": {
                "status": "success",
                "filename": filename,
                "format": result.get("format", "markdown"),
                "processor": "PDFProcessor",
                "detected_languages": languages,
                "auto_detected": languages != ["en"] if languages else False
            }
        }
        
        # 根据include_content参数决定是否包含markdown_content字段
        if include_content:
            response["markdown_content"] = result.get("content", "")
        
        logger.info("PDF转换成功", filename=filename, include_content=include_content)
        return response
        
    except Exception as e:
        logger.error("PDF转换过程中发生错误", exc_info=True)
        # 返回错误响应
        error_response = {
            "metadata": {},
            "conversion_info": {
                "status": "error",
                "filename": filename,
                "error": str(e),
                "processor": "PDFProcessor"
            }
        }
        
        # 错误时也根据include_content参数决定是否包含字段
        if include_content:
            error_response["markdown_content"] = ""
            
        return error_response


async def analyze_pdf_structure(
    file_content: str = file_content_field,
    filename: str = "document.pdf"
) -> dict:
    """
    分析PDF文档结构并提供元数据。
    """
    logger.info("开始执行PDF结构分析", filename=filename)

    try:
        processor = PDFProcessor(settings.model_dump())
        decoded_content = processor.decode_base64_content(file_content)
        temp_pdf_path = await processor.save_temp_file(decoded_content, suffix=".pdf")

        try:
            pdf_info = await processor._analyze_pdf_structure(temp_pdf_path)
            
            # 构建标准JSON响应
            response = {
                "page_count": pdf_info.get("page_count", 0),
                "metadata": pdf_info.get("metadata", {}),
                "structure_info": {
                    "has_images": pdf_info.get("has_images", False),
                    "has_tables": pdf_info.get("has_tables", False),
                    "text_density": pdf_info.get("text_density", []),
                    "page_sizes": pdf_info.get("page_sizes", []),
                    "filename": filename,
                    "analysis_status": "success"
                }
            }
            
            logger.info("PDF分析成功", filename=filename)
            return response
            
        finally:
            await processor.cleanup_temp_files([str(temp_pdf_path)])
            
    except Exception as e:
        logger.error("PDF分析过程中发生错误", exc_info=True)
        # 返回错误响应
        error_response = {
            "page_count": 0,
            "metadata": {},
            "structure_info": {
                "has_images": False,
                "has_tables": False,
                "text_density": [],
                "page_sizes": [],
                "filename": filename,
                "analysis_status": "error",
                "error": str(e)
            }
        }
        return error_response


def _format_analysis_result(pdf_info: Dict[str, Any], filename: str = "document.pdf") -> str:
    """格式化分析结果"""
    lines = [
        f"# PDF Document Analysis: {filename}",
        "",
        f"**File:** {filename}",
        f"**Page Count:** {pdf_info.get('page_count', 0)}",
        f"**Has Images:** {'Yes' if pdf_info.get('has_images', False) else 'No'}",
        f"**Has Tables:** {'Yes' if pdf_info.get('has_tables', False) else 'No'}",
        ""
    ]
    metadata = pdf_info.get('metadata', {})
    if metadata:
        lines.append("## Document Metadata")
        for key, value in metadata.items():
            if value:
                lines.append(f"**{key.title()}:** {value}")
        lines.append("")
    page_sizes = pdf_info.get('page_sizes', [])
    if page_sizes:
        lines.append("## Page Information")
        for i, size in enumerate(page_sizes[:5]):
            lines.append(f"**Page {i+1}:** {size['width']:.1f} x {size['height']:.1f} points")
        if len(page_sizes) > 5:
            lines.append(f"... and {len(page_sizes) - 5} more pages")
        lines.append("")
    text_density = pdf_info.get('text_density', [])
    if text_density:
        avg_density = sum(text_density) / len(text_density)
        lines.append("## Text Analysis")
        lines.append(f"**Average Text Density:** {avg_density:.2%}")
        lines.append("")

    return "\n".join(lines) 