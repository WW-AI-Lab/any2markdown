"""
Any2Markdown Tools Module (函数式)

提供所有可注册的工具函数。
"""

from .tool_registry import register_tools_with_server

# 导入所有可注册的工具函数
from .pdf_tools import convert_pdf_to_markdown, analyze_pdf_structure
from .word_tools import convert_word_to_markdown
from .excel_tools import convert_excel_to_markdown
from .utility_tools import batch_convert_documents, get_system_status, validate_document

__all__ = [
    # 注册函数
    'register_tools_with_server',
    
    # PDF 工具
    'convert_pdf_to_markdown',
    'analyze_pdf_structure',
    
    # Word 工具 (注意：函数名可能与其他模块冲突，Python会处理好，但导出时需注意)
    # 为清晰起见，可以在导入时使用 as 重命名，但此处保持原样
    'convert_word_to_markdown',
    
    # Excel 工具
    'convert_excel_to_markdown',

    # 实用工具
    'batch_convert_documents',
    'get_system_status',
    'validate_document',
]