# MCP 工具设计文档

本文档定义了 Any2Markdown MCP Server 通过 MCP 协议暴露的工具接口。重构后，所有工具都遵循 MCP 标准，通过 `FastMCP` 框架自动生成对应的端点。

## 1. 调用方式

客户端通过 MCP 协议与服务端交互。工具调用的通用格式如下：

```python
import asyncio
from mcp.client.stdio import stdio_client

async def main():
    # 使用 stdio 传输连接 MCP 服务器
    async with stdio_client(["python", "run_server.py"]) as (read, write):
        async with ClientSession(read, write) as session:
            # 调用工具
            result = await session.call_tool("convert_pdf_to_markdown", {
                "file_content": "base64_encoded_content",
                "filename": "document.pdf",
                "output_format": "markdown",
                "extract_images": True,
                "include_content": True  # 控制是否返回markdown_content字段
            })
            print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

## 2. 工具接口清单

以下是项目当前提供的所有工具及其参数和返回值的详细列表。

### 2.1. PDF 转换工具 (`pdf_tools.py`)

#### 2.1.1. `convert_pdf_to_markdown`

将PDF文档转换为Markdown格式，支持自动语言检测。

**参数：**

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `file_content` | `str` | 必需 | Base64编码的PDF文件内容 |
| `filename` | `str` | `"document.pdf"` | 原始文件名 |
| `output_format` | `Literal["markdown", "html", "json"]` | `"markdown"` | 输出格式 |
| `paginate_output` | `bool` | `True` | 是否分页输出 |
| `extract_images` | `bool` | `True` | 是否提取图片并生成URL |
| `remove_header_footer` | `bool` | `True` | 是否移除页眉页脚 |
| `start_page` | `int` | `0` | 起始页码（从0开始） |
| `end_page` | `Optional[int]` | `None` | 结束页码（不包含，None表示到最后一页） |
| `languages` | `Optional[List[str]]` | `None` | OCR识别语言列表，**如果为None则自动检测** |
| `batch_multiplier` | `int` | `2` | 批处理倍数 |
| `include_content` | `bool` | `False` | **是否在响应中包含markdown_content字段** |

**语言自动检测功能：**
- 当 `languages` 参数为 `None` 时，系统会自动提取PDF前几页的文本进行语言检测
- 支持基于 `langdetect` 库的高精度检测和基于字符Unicode范围的简单检测
- 支持检测：中文(zh)、英文(en)、日文(ja)、韩文(ko)、法文(fr)、德文(de)、西班牙文(es)、意大利文(it)、葡萄牙文(pt)、俄文(ru)、阿拉伯文(ar)、印地文(hi)、泰文(th)、越南文(vi)等

**返回值：**

```json
{
  "metadata": {
    "source_type": "pdf",
    "page_count": 10,
    "images": [...],
    "file_size": 1024000,
    "options_used": {...}
  },
  "conversion_info": {
    "status": "success",
    "filename": "document.pdf",
    "format": "markdown",
    "processor": "PDFProcessor",
    "detected_languages": ["zh"],
    "auto_detected": true
  },
  "markdown_content": "..."  // 仅当include_content=True时包含
}
```

#### 2.1.2. `analyze_pdf_structure`

分析PDF文档结构，不进行转换。

**参数：**

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `file_content` | `str` | 必需 | Base64编码的PDF文件内容 |
| `filename` | `str` | `"document.pdf"` | 原始文件名 |

**返回值：**

```json
{
  "page_count": 10,
  "metadata": {...},
  "structure_info": {
    "has_images": true,
    "has_tables": false,
    "text_density": [100, 150, 200],
    "page_sizes": [{"width": 595, "height": 842}],
    "filename": "document.pdf",
    "analysis_status": "success"
  }
}
```

### 2.2. Word 转换工具 (`word_tools.py`)

#### 2.2.1. `convert_word_to_markdown`

将Word文档转换为Markdown格式。

**参数：**

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `file_content` | `str` | 必需 | Base64编码的Word文件内容 |
| `filename` | `str` | `"document.docx"` | 原始文件名 |
| `output_format` | `Literal["markdown", "html", "json"]` | `"markdown"` | 输出格式 |
| `extract_images` | `bool` | `True` | 是否提取图片并生成URL |
| `remove_header_footer` | `bool` | `True` | 是否移除页眉页脚 |
| `paginate_output` | `bool` | `True` | 是否分页输出 |
| `preserve_formatting` | `bool` | `True` | 是否保持格式 |
| `include_content` | `bool` | `False` | **是否在响应中包含markdown_content字段** |

**返回值：**

```json
{
  "metadata": {
    "source_type": "word",
    "paragraph_count": 25,
    "table_count": 3,
    "images": [...],
    "file_size": 512000,
    "options_used": {...}
  },
  "conversion_info": {
    "status": "success",
    "filename": "document.docx",
    "format": "markdown",
    "processor": "WordProcessor"
  },
  "markdown_content": "..."  // 仅当include_content=True时包含
}
```

### 2.3. Excel 转换工具 (`excel_tools.py`)

#### 2.3.1. `convert_excel_to_markdown`

将Excel文档转换为Markdown格式。

**参数：**

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `file_content` | `str` | 必需 | Base64编码的Excel文件内容 |
| `filename` | `str` | `"document.xlsx"` | 原始文件名 |
| `output_format` | `Literal["markdown", "html", "json"]` | `"markdown"` | 输出格式 |
| `sheet_names` | `Optional[List[str]]` | `None` | 要转换的工作表名称列表，None表示转换所有工作表 |
| `include_formulas` | `bool` | `False` | 是否包含公式 |
| `paginate_output` | `bool` | `True` | 是否分页输出 |
| `include_content` | `bool` | `False` | **是否在响应中包含markdown_content字段** |

**返回值：**

```json
{
  "metadata": {
    "source_type": "excel",
    "sheet_count": 3,
    "total_rows": 1000,
    "total_columns": 20,
    "file_size": 256000,
    "options_used": {...}
  },
  "conversion_info": {
    "status": "success",
    "filename": "document.xlsx",
    "format": "markdown",
    "processor": "ExcelProcessor"
  },
  "markdown_content": "..."  // 仅当include_content=True时包含
}
```

### 2.4. 实用工具 (`utility_tools.py`)

#### 2.4.1. `get_system_status`

获取系统状态信息。

**参数：** 无

**返回值：**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "available_processors": ["PDFProcessor", "WordProcessor", "ExcelProcessor"],
  "system_info": {
    "python_version": "3.11.0",
    "platform": "darwin",
    "memory_usage": "256MB",
    "disk_space": "10GB"
  }
}
```

#### 2.4.2. `validate_document`

验证文档格式和大小。

**参数：**

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `file_content` | `str` | 必需 | Base64编码的文件内容 |
| `filename` | `str` | 必需 | 文件名 |

**返回值：**

```json
{
  "is_valid": true,
  "file_type": "pdf",
  "metadata": {
    "filename": "document.pdf",
    "file_type": "pdf",
    "file_size": 1024000,
    "file_size_mb": 1.0
  }
}
```

#### 2.4.3. `batch_convert_documents`

批量转换多个文档。

**参数：**

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `documents` | `List[DocumentToConvert]` | 必需 | 要转换的文档列表 |
| `max_concurrent` | `int` | `3` | 最大并发数 |

其中 `DocumentToConvert` 结构：

```json
{
  "file_content": "base64_encoded_content",
  "filename": "document.pdf",
  "file_type": "pdf",
  "options": {
    "output_format": "markdown",
    "extract_images": true,
    "include_content": false
  }
}
```

**返回值：**

```json
{
  "results": [
    {
      "filename": "document1.pdf",
      "status": "success",
      "result": {...}
    },
    {
      "filename": "document2.docx",
      "status": "error",
      "error": "File too large"
    }
  ],
  "summary": {
    "total": 2,
    "successful": 1,
    "failed": 1,
    "processing_time": "5.2s"
  }
}
```

## 3. 重要功能特性

### 3.1. 内容输出控制

所有转换工具都支持 `include_content` 参数：

- **默认值：`False`** - 不返回 `markdown_content` 字段，节省传输带宽
- **设置为 `True`** - 在响应中包含完整的转换内容
- **适用场景：**
  - `False`：仅需要元数据和转换状态信息
  - `True`：需要获取完整的转换内容

### 3.2. PDF自动语言检测

PDF转换工具支持智能语言检测：

- **自动检测：** 当 `languages=None` 时自动识别文档语言
- **检测策略：**
  1. 优先使用 `langdetect` 库进行高精度检测
  2. 降级使用基于Unicode字符范围的简单检测
  3. 最终降级使用默认英文
- **支持语言：** 15+ 种主要语言
- **检测范围：** 文档前3页，最多1000字符

### 3.3. 错误处理

所有工具都提供统一的错误处理：

```json
{
  "metadata": {},
  "conversion_info": {
    "status": "error",
    "filename": "document.pdf",
    "error": "具体错误信息",
    "processor": "PDFProcessor"
  },
  "markdown_content": ""  // 仅当include_content=True时包含
}
```

### 3.4. 性能优化

- **并发控制：** 批量转换支持可配置的并发数
- **内存管理：** 大文件自动分页处理
- **缓存机制：** 重复文档转换结果缓存
- **带宽优化：** 可选的内容输出控制

## 4. 使用建议

### 4.1. 最佳实践

1. **文件大小控制：** 建议单个文件不超过100MB
2. **语言检测：** PDF转换时推荐使用自动语言检测
3. **内容获取：** 仅在必要时设置 `include_content=True`
4. **批量处理：** 大量文档转换使用批量接口
5. **错误重试：** 实现适当的重试机制

### 4.2. 性能考虑

- **网络传输：** 使用 `include_content=False` 减少传输数据量
- **处理时间：** 复杂文档（多图片、大页数）处理时间较长
- **并发限制：** 避免过高的并发请求导致资源竞争

## 5. 版本信息

- **当前版本：** 2.0.0
- **MCP协议版本：** 1.0
- **最后更新：** 2024-12-28

## 6. 更新日志

### v2.0.0 (2024-12-28)
- ✨ 新增 `include_content` 参数控制输出内容
- ✨ 新增 PDF 自动语言检测功能
- 🔧 将 `languages` 参数改为可选，支持自动检测
- 📚 完善了API文档和错误处理
- 🚀 优化了网络传输性能 