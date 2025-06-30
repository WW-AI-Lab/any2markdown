# Any2Markdown MCP Server 技术设计详解

## 总体架构设计

### MCP协议层次
```
Client Application
    ↓ (MCP Client SDK)
HTTP/JSON-RPC Communication
    ↓ (Streamable HTTP Transport)
MCP Server (any2markdown)
    ↓ (Tool Handlers)
Document Processing Layer
    ↓ (Processors)
External Libraries & Models
```

### 核心技术栈
- **MCP Framework**: python-sdk 1.10.1+
- **Web Framework**: FastAPI (内置在MCP中)
- **异步处理**: asyncio, aiofiles
- **PDF处理**: marker-pdf, PyMuPDF, PyTorch, HuggingFace
- **Office文档**: python-docx, pandas, openpyxl
- **图片处理**: Pillow
- **数据格式**: JSON Schema, Base64 encoding
- **并发控制**: semaphore, task queues

## 详细实现设计

### 实现参考

本文档中的所有详细设计（尤其是 **文档处理器** 和 **模型管理** 部分）都应将 `any2markdown/examples/` 目录下的示例代码作为首要实现蓝本。这些示例代码是从旧版API中提取的、经过验证的核心逻辑，为新服务器的处理器模块（`processors`）提供了具体、可直接参考的实现。

- **PDF 处理器** (`PDFProcessor`) 的实现应基于 `examples/pdf_conversion_example.py`。
- **Word 处理器** (`WordProcessor`) 的实现应基于 `examples/word_conversion_example.py`。
- **Excel 处理器** (`ExcelProcessor`) 的实现应基于 `examples/excel_conversion_example.py`。
- **通用工具**（如分页）的实现应参考 `examples/utils_example.py`。

### 1. MCP Server 主架构

#### 服务器初始化流程
```python
# 服务器启动序列
1. 加载配置文件和环境变量
2. 初始化模型管理器 (预加载marker模型)
3. 注册所有MCP tools
4. 启动Streamable HTTP server
5. 处理客户端连接和工具调用
```

#### 核心服务器类设计
```python
class Any2MarkdownMCPServer:
    def __init__(self):
        self.app = mcp.Server("any2markdown")
        self.model_manager = ModelManager()
        self.processors = {}
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_JOBS)
    
    async def initialize(self):
        """初始化服务器和模型"""
        await self.model_manager.load_models()
        self.register_tools()
    
    def register_tools(self):
        """注册所有MCP tools"""
        # PDF工具
        self.app.tool("convert_pdf_to_markdown")(self.convert_pdf_to_markdown)
        self.app.tool("analyze_pdf_structure")(self.analyze_pdf_structure)
        
        # Word工具  
        self.app.tool("convert_word_to_markdown")(self.convert_word_to_markdown)
        
        # Excel工具
        self.app.tool("convert_excel_to_markdown")(self.convert_excel_to_markdown)
        
        # 批量和工具类
        self.app.tool("batch_convert_documents")(self.batch_convert_documents)
        self.app.tool("get_supported_formats")(self.get_supported_formats)
        self.app.tool("validate_document")(self.validate_document)
```

### 2. 文档处理器设计

#### PDF处理器架构
```python
class PDFProcessor:
    def __init__(self, model_manager):
        self.model_manager = model_manager
        self.marker_converter = None
        
    async def convert(self, file_content: bytes, options: dict) -> dict:
        """转换PDF文档"""
        # 1. 解码Base64内容
        # 2. 验证PDF格式
        # 3. (新增) 如果启用，预处理PDF以移除页眉页脚
        # 4. 检查页面范围
        # 5. 调用marker模型转换
        # 6. (新增) 提取图片，保存并生成URL
        # 7. 后处理和格式化
        # 8. 返回结构化结果
        
    async def analyze_structure(self, file_content: bytes) -> dict:
        """分析PDF结构"""
        # 使用PyMuPDF快速分析结构信息
```

#### Word处理器架构
```python
class WordProcessor:
    def __init__(self):
        self.supported_formats = ['.docx', '.doc']
        
    async def convert(self, file_content: bytes, options: dict) -> dict:
        """转换Word文档"""
        # 1. 使用python-docx解析
        # 2. (新增) 如果启用，识别并过滤页眉页脚内容
        # 3. 提取段落、表格
        # 4. (新增) 如果启用，提取图片，保存并生成URL
        # 5. 转换为Markdown格式
        # 6. 可选：按标题分割
```

#### Excel处理器架构
```python
class ExcelProcessor:
    def __init__(self):
        self.supported_formats = ['.xlsx', '.xls']
        
    async def convert(self, file_content: bytes, options: dict) -> dict:
        """转换Excel文档""" 
        # 1. 使用pandas读取Excel
        # 2. 处理多个工作表
        # 3. 转换为Markdown表格格式
        # 4. 处理大数据集分页
```

### 3. 模型管理系统

#### 模型管理器设计
```python
class ModelManager:
    def __init__(self):
        self.models = {}
        self.cache_dir = Path.home() / ".cache" / "marker"
        self.loaded = False
        
    async def load_models(self):
        """预加载marker模型"""
        if self.loaded:
            return
            
        # 加载检测模型
        self.models['detection'] = await self._load_detection_model()
        # 加载布局模型  
        self.models['layout'] = await self._load_layout_model()
        # 加载排序模型
        self.models['order'] = await self._load_order_model()
        # 加载OCR模型
        self.models['ocr'] = await self._load_ocr_model()
        
        self.loaded = True
        
    async def get_marker_converter(self):
        """获取marker转换器实例"""
        if not self.loaded:
            await self.load_models()
        return MarkerConverter(self.models)
```

### 4. 页眉页脚移除方案

#### PDF页眉页脚移除
PDF的页眉页脚识别较为复杂，我们将采用基于`PyMuPDF`的启发式方法。
1.  **区域定义**: 将页面顶部15%和底部15%定义为潜在的页眉/页脚区域。
2.  **内容识别**: 遍历文档前几页（如前5页），统计这些区域内重复出现的文本或图像。
3.  **内容删除**: 如果某个文本块或图像在多个页面的相同位置重复出现，则将其识别为页眉/页脚元素。在调用`marker`转换前，使用`PyMuPDF`的`redact_annot`功能将这些区域覆盖，从而在转换时忽略它们。
4.  **可配置**: 此功能应可通过`remove_header_footer`选项开关。

#### Word页眉页脚移除
Word文档的结构更清晰，可以直接利用`python-docx`的API。
1.  **访问节(Section)**: Word文档包含多个节，每个节可以有独立的页眉页脚。
2.  **迭代处理**: 遍历文档的所有`section`，访问其`header`和`footer`属性。
3.  **内容过滤**: 在文档内容转换为主循环时，跳过从`header`和`footer`对象中提取的内容。由于`python-docx`分别处理正文、页眉和页脚，我们只需在内容提取逻辑中不包含对后两者的调用即可。

### 5. 图片处理与静态服务架构

#### 兼容性设计
MCP服务器本质上是一个FastAPI应用。我们可以利用这一点来挂载静态文件服务，使其与MCP的`Streamable HTTP Transport`无缝协作。
```python
# server.py 核心结构
from fastapi.staticfiles import StaticFiles

class Any2MarkdownMCPServer:
    def __init__(self):
        self.app = mcp.Server("any2markdown")
        
        # 创建临时图片存储目录
        self.image_dir = Path("./temp_images")
        self.image_dir.mkdir(exist_ok=True)
        
        # 挂载静态文件服务
        # 注意: 此处需确保路径不会与MCP的/mcp端点冲突
        self.app.mount("/static", StaticFiles(directory=self.image_dir), name="static")
        
        # ... 其他初始化 ...
```
通过这种方式，MCP的RPC调用在`/mcp`端点处理，而图片请求则由FastAPI的`StaticFiles`在`/static`路径下处理，两者互不干扰。

#### 图片处理流程
1.  **提取**:
    *   **PDF**: 使用`PyMuPDF`的`page.get_images()`方法从PDF页面中提取原始图片数据。
    *   **Word**: 使用`python-docx`的`InlineShape`或`part.related_parts`来访问和提取嵌入的图片。
2.  **存储**:
    *   **会话目录**: 为每一次转换任务创建一个唯一的子目录，如`./temp_images/<session_id>/`，以隔离不同任务的图片。
    *   **命名**: 使用`hashlib`计算图片内容的SHA256哈希值作为文件名（如`<hash>.png`），以避免重复存储相同图片。
    *   **保存**: 使用`Pillow`库将提取的图片数据保存到指定路径，并可能进行格式标准化（如统一保存为PNG）。
3.  **URL生成**:
    *   生成图片的URL，格式为`{server_base_url}/static/<session_id>/{image_filename}`。
    *   这个URL将被嵌入到最终生成的Markdown文本中，例如`![alt text](/static/session123/abcde12345.png)`。
4.  **生命周期管理**:
    *   **清理机制**: 实现一个后台任务或在任务结束时触发的清理函数。
    *   **策略**: 删除与已完成的`session_id`相关的整个图片子目录，以释放磁盘空间。可以设置一个定时任务（如每小时执行一次），清理超过一定时间的临时目录。

### 6. 工具函数实现详解

#### Base64文件处理
```python
async def decode_file_content(file_content: str, filename: str) -> bytes:
    """解码Base64文件内容"""
    try:
        import base64
        return base64.b64decode(file_content)
    except Exception as e:
        raise ValueError(f"Invalid Base64 content: {e}")

async def validate_file_size(content: bytes, max_size: int = 100 * 1024 * 1024):
    """验证文件大小"""
    if len(content) > max_size:
        raise ValueError(f"File too large: {len(content)} bytes")
```

#### 分页处理算法
```python
def parse_page_range(page_range: str, total_pages: int) -> List[int]:
    """解析页面范围字符串"""
    if not page_range:
        return list(range(total_pages))
        
    pages = []
    for part in page_range.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            pages.extend(range(start, min(end + 1, total_pages)))
        else:
            page_num = int(part)
            if page_num < total_pages:
                pages.append(page_num)
    
    return sorted(set(pages))
```

#### 异步并发控制
```python
class ConcurrencyManager:
    def __init__(self, max_concurrent: int = 5):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_tasks = set()
        
    async def execute_with_limit(self, coro):
        """限制并发执行协程"""
        async with self.semaphore:
            task = asyncio.create_task(coro)
            self.active_tasks.add(task)
            try:
                result = await task
                return result
            finally:
                self.active_tasks.discard(task)
```

### 7. 错误处理和恢复机制

#### 错误分类系统
```python
class DocumentProcessingError(Exception):
    """文档处理错误基类"""
    def __init__(self, message: str, error_type: str, details: dict = None):
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        super().__init__(message)

class PDFProcessingError(DocumentProcessingError):
    """PDF处理特定错误"""
    pass

class ModelLoadError(DocumentProcessingError):
    """模型加载错误"""
    pass

class ValidationError(DocumentProcessingError):
    """输入验证错误"""
    pass
```

#### 三层容错处理
```python
async def convert_pdf_with_fallback(self, content: bytes, options: dict):
    """PDF转换三层容错"""
    errors = []
    
    # 第一层：完整marker处理
    try:
        return await self.full_marker_convert(content, options)
    except Exception as e:
        errors.append(f"Full marker failed: {e}")
        
    # 第二层：简化marker处理
    try:
        return await self.simple_marker_convert(content, options)
    except Exception as e:
        errors.append(f"Simple marker failed: {e}")
        
    # 第三层：基础文本提取
    try:
        return await self.basic_text_extract(content, options)
    except Exception as e:
        errors.append(f"Basic extract failed: {e}")
        
    # 所有方法都失败
    raise PDFProcessingError(
        "All conversion methods failed",
        "conversion_failure",
        {"attempts": errors}
    )
```

### 8. 性能优化策略

#### 内存管理
```python
class MemoryManager:
    def __init__(self):
        self.max_memory_usage = 2 * 1024 * 1024 * 1024  # 2GB
        self.current_usage = 0
        
    async def check_memory_usage(self):
        """检查内存使用情况"""
        import psutil
        process = psutil.Process()
        self.current_usage = process.memory_info().rss
        
        if self.current_usage > self.max_memory_usage:
            await self.cleanup_resources()
            
    async def cleanup_resources(self):
        """清理资源"""
        # 清理临时文件
        # 卸载不常用模型
        # 强制垃圾回收
```

#### 缓存策略
```python
class ResultCache:
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size
        self.access_times = {}
        
    def get_cache_key(self, content: bytes, options: dict) -> str:
        """生成缓存键"""
        import hashlib
        content_hash = hashlib.md5(content).hexdigest()
        options_hash = hashlib.md5(str(sorted(options.items())).encode()).hexdigest()
        return f"{content_hash}_{options_hash}"
        
    async def get_or_compute(self, key: str, compute_func):
        """获取缓存或计算"""
        if key in self.cache:
            self.access_times[key] = time.time()
            return self.cache[key]
            
        result = await compute_func()
        await self.store(key, result)
        return result
```

### 9. 配置和环境管理

#### 配置类设计
```python
@dataclass
class ServerConfig:
    # HTTP服务配置
    host: str = "0.0.0.0"
    port: int = 8080
    
    # 文件处理配置
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    max_concurrent_jobs: int = 5
    
    # 模型配置
    model_cache_dir: str = "~/.cache/marker"
    auto_load_models: bool = True
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "any2markdown-mcp.log"
    
    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        return cls(
            host=os.getenv("HTTP_HOST", cls.host),
            port=int(os.getenv("HTTP_PORT", cls.port)),
            max_file_size=int(os.getenv("MAX_FILE_SIZE", cls.max_file_size)),
            max_concurrent_jobs=int(os.getenv("MAX_CONCURRENT_JOBS", cls.max_concurrent_jobs)),
            model_cache_dir=os.getenv("MODEL_CACHE_DIR", cls.model_cache_dir),
            log_level=os.getenv("LOG_LEVEL", cls.log_level),
        )
```

### 10. 监控和日志系统

#### 结构化日志
```python
import structlog

logger = structlog.get_logger("any2markdown-mcp")

async def log_tool_execution(tool_name: str, args: dict, result: dict, duration: float):
    """记录工具执行日志"""
    logger.info(
        "tool_executed",
        tool_name=tool_name,
        file_type=args.get("filename", "").split(".")[-1] if "filename" in args else "unknown",
        success=result.get("success", False),
        duration_seconds=duration,
        file_size=len(args.get("file_content", "")),
        error=result.get("error"),
    )
```

#### 性能监控
```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_processing_time": 0,
            "processing_times": []
        }
        
    async def record_request(self, duration: float, success: bool):
        """记录请求性能"""
        self.metrics["total_requests"] += 1
        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
            
        self.metrics["processing_times"].append(duration)
        self.metrics["avg_processing_time"] = sum(self.metrics["processing_times"]) / len(self.metrics["processing_times"])
        
        # 保持最近1000次记录
        if len(self.metrics["processing_times"]) > 1000:
            self.metrics["processing_times"] = self.metrics["processing_times"][-1000:]
```

### 11. 测试策略

#### 单元测试框架
```python
import pytest
import asyncio
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_pdf_conversion():
    """测试PDF转换功能"""
    server = Any2MarkdownMCPServer()
    await server.initialize()
    
    # 准备测试数据
    with open("test.pdf", "rb") as f:
        content = base64.b64encode(f.read()).decode()
    
    args = {
        "file_content": content,
        "filename": "test.pdf",
        "options": {"output_format": "markdown"}
    }
    
    result = await server.convert_pdf_to_markdown(args)
    
    assert result["success"] == True
    assert "content" in result
    assert result["format"] == "markdown"
```

#### 集成测试
```python
@pytest.mark.asyncio 
async def test_full_workflow():
    """测试完整工作流程"""
    # 启动服务器
    server = Any2MarkdownMCPServer()
    await server.initialize()
    
    # 测试各种文档类型
    test_files = [
        ("test.pdf", "pdf"),
        ("test.docx", "word"), 
        ("test.xlsx", "excel")
    ]
    
    for filename, doc_type in test_files:
        with open(filename, "rb") as f:
            content = base64.b64encode(f.read()).decode()
            
        result = await server.call_appropriate_tool(doc_type, content, filename)
        assert result["success"] == True
```

### 12. 部署和运维

#### Docker部署配置
```dockerfile
FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制应用代码
COPY src/ ./src/
COPY examples/ ./examples/

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["python", "-m", "src.any2markdown_mcp.server"]
```

#### 健康检查
```python
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "models_loaded": model_manager.loaded,
        "uptime": time.time() - start_time,
        "memory_usage": get_memory_usage(),
        "active_jobs": len(concurrency_manager.active_tasks)
    }
```

这个技术设计文档为MCP server的实现提供了详细的技术指导，确保代码质量和系统稳定性。 