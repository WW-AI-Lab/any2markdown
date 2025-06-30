# RESTful API 设计文档

## 1. 概述

Any2Markdown MCP Server 提供统一的RESTful API接口，支持将PDF、Word、Excel文档转换为Markdown格式。新的设计采用**单一端点**模式，通过`/api/v1/convert`端点处理所有类型的文档转换，支持两种调用方式：

1. **文件上传方式** (multipart/form-data) - 直接上传文件
2. **JSON方式** (application/json) - 使用base64编码的文件内容

## 2. 设计原则

### 2.1 统一性
- 所有文档类型使用同一个API端点
- 统一的请求和响应格式
- 自动文件类型检测

### 2.2 灵活性
- 支持单文件和多文件转换
- 支持文件特定选项和全局选项
- 支持多种输出格式

### 2.3 易用性
- 标准的HTTP multipart/form-data支持
- 清晰的错误信息
- 完整的API文档

## 3. API端点

### 3.1 统一转换端点

**端点**: `POST /api/v1/convert`

**功能**: 
- 支持PDF、Word、Excel文档转换
- 自动文件类型检测
- 单文件或多文件处理
- 两种调用方式：文件上传和JSON

#### 3.1.1 文件上传方式 (multipart/form-data)

**Content-Type**: `multipart/form-data`

**表单字段**:

**文件字段**:
- `file` - 单文件上传
- `file1`, `file2`, `file3`, ... - 多文件上传

**选项字段** (所有可选):
- `output_format` - 输出格式 (markdown/html/json，默认markdown)
- `extract_images` - 是否提取图片 (true/false，默认true)
- `remove_header_footer` - 是否移除页眉页脚 (true/false，默认true)
- `include_content` - 是否包含转换内容 (true/false，默认true)

**PDF特定选项**:
- `paginate_output` - 是否分页输出 (true/false，默认true)
- `start_page` - 起始页码 (数字，默认0)
- `end_page` - 结束页码 (数字，可选)
- `languages` - 语言列表 (逗号分隔，如"zh,en"，默认"auto")

**Word特定选项**:
- `preserve_formatting` - 是否保留格式 (true/false，默认true)

**Excel特定选项**:
- `include_formulas` - 是否包含公式 (true/false，默认true)
- `sheet_names` - 工作表名称 (逗号分隔，可选)

**单文件上传示例**:
```bash
curl -X POST "http://localhost:3000/api/v1/convert" \
  -F "file=@document.pdf" \
  -F "output_format=markdown" \
  -F "extract_images=true" \
  -F "include_content=false" \
  -F "start_page=0" \
  -F "end_page=5" \
  -F "languages=zh,en"
```

**多文件上传示例**:
```bash
curl -X POST "http://localhost:3000/api/v1/convert" \
  -F "file1=@document.pdf" \
  -F "file2=@report.docx" \
  -F "file3=@data.xlsx" \
  -F "output_format=markdown" \
  -F "extract_images=true" \
  -F "include_content=false"
```

#### 3.1.2 JSON方式 (application/json)

**Content-Type**: `application/json`

**请求体结构**:
```json
{
  "files": [
    {
      "filename": "document.pdf",
      "file_content": "base64-encoded-content",
      "options": {
        "output_format": "markdown",
        "extract_images": true,
        "start_page": 0,
        "end_page": 5,
        "languages": ["zh", "en"]
      }
    }
  ],
  "global_options": {
    "remove_header_footer": true,
    "include_content": false
  }
}
```

**字段说明**:
- `files` (必需) - 文件列表
  - `filename` (必需) - 文件名，用于确定文件类型
  - `file_content` (必需) - Base64编码的文件内容
  - `options` (可选) - 文件特定选项
- `global_options` (可选) - 全局选项，会被文件特定选项覆盖

**单文件JSON示例**:
```bash
curl -X POST "http://localhost:3000/api/v1/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "files": [
      {
        "filename": "document.pdf",
        "file_content": "JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwo...",
        "options": {
          "output_format": "markdown",
          "extract_images": true,
          "include_content": false
        }
      }
    ]
  }'
```

**多文件JSON示例**:
```bash
curl -X POST "http://localhost:3000/api/v1/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "files": [
      {
        "filename": "doc1.pdf",
        "file_content": "base64-content-1",
        "options": {
          "start_page": 0,
          "end_page": 2
        }
      },
      {
        "filename": "doc2.docx", 
        "file_content": "base64-content-2",
        "options": {
          "preserve_formatting": true
        }
      }
    ],
    "global_options": {
      "output_format": "markdown",
      "extract_images": true,
      "include_content": false
    }
  }'
```

### 3.2 响应格式

#### 3.2.1 单文件转换成功响应
```json
{
  "success": true,
  "data": {
    "markdown_content": "# 文档标题\n\n内容...",
    "metadata": {
      "source_type": "pdf",
      "total_pages": 10,
      "images_extracted": 5,
      "detected_language": "zh",
      "processing_time": 3.45,
      "file_size": 1024000,
      "options_used": {
        "output_format": "markdown",
        "extract_images": true,
        "start_page": 0,
        "end_page": 5
      }
    },
    "images": [
      {
        "filename": "pdf_123456_page_1_img_1.png",
        "url": "http://host:port/static/pdf_123456_page_1_img_1.png",
        "size": 15234,
        "page": 1,
        "index": 1
      }
    ],
    "conversion_info": {
      "status": "success",
      "filename": "document.pdf",
      "format": "markdown",
      "processor": "PDFProcessor"
    }
  },
  "message": "文件转换成功",
  "timestamp": "2024-12-28T10:30:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### 3.2.2 多文件转换成功响应
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "markdown_content": "...",
        "metadata": { /* 转换元数据 */ },
        "images": [ /* 图片列表 */ ],
        "conversion_info": {
          "status": "success",
          "filename": "doc1.pdf",
          "format": "markdown",
          "processor": "PDFProcessor"
        }
      },
      {
        "conversion_info": {
          "status": "error",
          "filename": "doc2.docx",
          "error": "不支持的文件格式"
        },
        "metadata": {}
      }
    ],
    "summary": {
      "total": 2,
      "successful": 1,
      "failed": 1,
      "processing_time": 8.23
    }
  },
  "message": "批量转换完成: 1成功, 1失败",
  "timestamp": "2024-12-28T10:30:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### 3.2.3 错误响应
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": {
      "validation_errors": [
        {
          "field": "file",
          "message": "至少需要上传一个文件",
          "type": "missing"
        }
      ]
    }
  },
  "timestamp": "2024-12-28T10:30:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 3.3 其他端点

#### 3.3.1 PDF结构分析
**端点**: `GET /api/v1/analyze/pdf`

**查询参数**:
- `file_content` (必需) - Base64编码的PDF内容
- `filename` (可选) - 文件名，默认"document.pdf"

#### 3.3.2 文档验证
**端点**: `POST /api/v1/validate`

**请求体**:
```json
{
  "file_content": "base64-encoded-content",
  "filename": "document.pdf"
}
```

#### 3.3.3 系统状态
**端点**: `GET /api/v1/status`

#### 3.3.4 支持格式
**端点**: `GET /api/v1/formats`

#### 3.3.5 API文档
**端点**: `GET /api/v1/docs` - Swagger UI界面
**端点**: `GET /api/v1/openapi.json` - OpenAPI规范

## 4. 错误处理

### 4.1 HTTP状态码

| 状态码 | 说明 | 描述 |
|--------|------|------|
| `200` | 成功 | 操作成功完成 |
| `400` | 请求错误 | 参数验证失败、文件格式错误 |
| `401` | 未授权 | API密钥无效或缺失 |
| `413` | 文件过大 | 文件大小超过限制 |
| `422` | 处理失败 | 文档转换失败 |
| `429` | 请求过多 | 触发限流 |
| `500` | 服务器错误 | 内部错误 |

### 4.2 错误代码

- `VALIDATION_ERROR` - 参数验证失败
- `UNSUPPORTED_FORMAT` - 不支持的文件格式
- `FILE_TOO_LARGE` - 文件大小超过限制
- `PROCESSING_FAILED` - 文档转换失败
- `RATE_LIMIT_EXCEEDED` - 触发限流
- `UNAUTHORIZED` - 未授权访问
- `INTERNAL_ERROR` - 内部服务器错误

## 5. 支持的文件格式

### 5.1 输入格式

| 格式 | 扩展名 | MIME类型 | 最大大小 | 支持功能 |
|------|--------|----------|----------|----------|
| PDF | `.pdf` | `application/pdf` | 100MB | 文本、图片、表格、页眉页脚 |
| Word | `.docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | 50MB | 文本、图片、公式、页眉页脚 |
| Word | `.doc` | `application/msword` | 50MB | 文本、图片、基础格式 |
| Excel | `.xlsx` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | 30MB | 文本、图片、公式、图表 |
| Excel | `.xls` | `application/vnd.ms-excel` | 30MB | 文本、基础公式 |

### 5.2 输出格式

- `markdown` - Markdown格式 (默认)
- `html` - HTML格式
- `json` - JSON格式

## 6. 使用示例

### 6.1 HTML表单集成

```html
<!DOCTYPE html>
<html>
<head>
    <title>文档转换</title>
</head>
<body>
    <h1>Any2Markdown 转换器</h1>
    
    <!-- 单文件上传 -->
    <form action="/api/v1/convert" method="post" enctype="multipart/form-data">
        <div>
            <label>选择文件:</label>
            <input type="file" name="file" accept=".pdf,.docx,.doc,.xlsx,.xls" required>
        </div>
        <div>
            <label>输出格式:</label>
            <select name="output_format">
                <option value="markdown">Markdown</option>
                <option value="html">HTML</option>
                <option value="json">JSON</option>
            </select>
        </div>
        <div>
            <label>
                <input type="checkbox" name="extract_images" value="true" checked>
                提取图片
            </label>
        </div>
        <div>
            <label>
                <input type="checkbox" name="include_content" value="false">
                仅返回元数据
            </label>
        </div>
        <button type="submit">转换</button>
    </form>
    
    <!-- 多文件上传 -->
    <form action="/api/v1/convert" method="post" enctype="multipart/form-data">
        <h2>批量转换</h2>
        <div>
            <label>文件1:</label>
            <input type="file" name="file1" accept=".pdf,.docx,.doc,.xlsx,.xls">
        </div>
        <div>
            <label>文件2:</label>
            <input type="file" name="file2" accept=".pdf,.docx,.doc,.xlsx,.xls">
        </div>
        <div>
            <label>文件3:</label>
            <input type="file" name="file3" accept=".pdf,.docx,.doc,.xlsx,.xls">
        </div>
        <div>
            <label>
                <input type="checkbox" name="include_content" value="false" checked>
                仅返回元数据
            </label>
        </div>
        <button type="submit">批量转换</button>
    </form>
</body>
</html>
```

### 6.2 JavaScript/Ajax集成

```javascript
// 单文件上传
async function convertSingleFile(file, options = {}) {
    const formData = new FormData();
    formData.append('file', file);
    
    // 添加选项
    Object.entries(options).forEach(([key, value]) => {
        formData.append(key, value);
    });
    
    try {
        const response = await fetch('/api/v1/convert', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('转换成功:', result.data);
            return result.data;
        } else {
            console.error('转换失败:', result.error);
            throw new Error(result.error.message);
        }
    } catch (error) {
        console.error('请求失败:', error);
        throw error;
    }
}

// 多文件上传
async function convertMultipleFiles(files, options = {}) {
    const formData = new FormData();
    
    // 添加文件
    files.forEach((file, index) => {
        formData.append(`file${index + 1}`, file);
    });
    
    // 添加全局选项
    Object.entries(options).forEach(([key, value]) => {
        formData.append(key, value);
    });
    
    try {
        const response = await fetch('/api/v1/convert', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('批量转换完成:', result.data);
            return result.data;
        } else {
            console.error('批量转换失败:', result.error);
            throw new Error(result.error.message);
        }
    } catch (error) {
        console.error('请求失败:', error);
        throw error;
    }
}

// JSON方式转换
async function convertWithJSON(fileData) {
    try {
        const response = await fetch('/api/v1/convert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(fileData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('JSON转换成功:', result.data);
            return result.data;
        } else {
            console.error('JSON转换失败:', result.error);
            throw new Error(result.error.message);
        }
    } catch (error) {
        console.error('请求失败:', error);
        throw error;
    }
}

// 使用示例
document.getElementById('fileInput').addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (file) {
        try {
            const result = await convertSingleFile(file, {
                output_format: 'markdown',
                extract_images: 'true',
                include_content: 'false'
            });
            
            console.log('转换结果:', result);
            // 处理转换结果
        } catch (error) {
            alert('转换失败: ' + error.message);
        }
    }
});
```

### 6.3 Python集成

```python
import requests
import base64
import json

class Any2MarkdownClient:
    def __init__(self, base_url="http://localhost:3000"):
        self.base_url = base_url
        self.convert_url = f"{base_url}/api/v1/convert"
    
    def convert_file_upload(self, file_path, **options):
        """文件上传方式转换"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = options
            
            response = requests.post(self.convert_url, files=files, data=data)
            return response.json()
    
    def convert_multiple_files(self, file_paths, **options):
        """多文件上传转换"""
        files = {}
        for i, file_path in enumerate(file_paths, 1):
            files[f'file{i}'] = open(file_path, 'rb')
        
        try:
            response = requests.post(self.convert_url, files=files, data=options)
            return response.json()
        finally:
            # 关闭文件
            for f in files.values():
                f.close()
    
    def convert_json(self, files_data, global_options=None):
        """JSON方式转换"""
        payload = {
            "files": files_data,
            "global_options": global_options or {}
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(self.convert_url, json=payload, headers=headers)
        return response.json()
    
    def convert_file_to_base64(self, file_path):
        """将文件转换为base64编码"""
        with open(file_path, 'rb') as f:
            return base64.b64encode(f.read()).decode()

# 使用示例
client = Any2MarkdownClient()

# 单文件上传
result = client.convert_file_upload(
    'document.pdf',
    output_format='markdown',
    extract_images='true',
    include_content='false'
)

# 多文件上传
result = client.convert_multiple_files(
    ['doc1.pdf', 'doc2.docx', 'data.xlsx'],
    output_format='markdown',
    include_content='false'
)

# JSON方式
files_data = [
    {
        "filename": "document.pdf",
        "file_content": client.convert_file_to_base64("document.pdf"),
        "options": {
            "start_page": 0,
            "end_page": 5
        }
    }
]

result = client.convert_json(
    files_data,
    global_options={
        "output_format": "markdown",
        "extract_images": True,
        "include_content": False
    }
)

print(json.dumps(result, indent=2, ensure_ascii=False))
```

## 7. 性能和限制

### 7.1 文件大小限制
- PDF: 最大100MB
- Word: 最大50MB  
- Excel: 最大30MB

### 7.2 并发限制
- 同时处理请求数: 10个
- 单个请求超时: 300秒

### 7.3 速率限制
- 每分钟最大请求数: 60次
- 每小时最大请求数: 1000次

## 8. 安全考虑

### 8.1 文件验证
- 严格的文件类型检查
- 文件大小限制
- 恶意文件检测

### 8.2 输入清理
- 文件名清理
- 参数验证
- XSS防护

### 8.3 错误处理
- 不暴露内部错误信息
- 统一的错误响应格式
- 详细的日志记录

## 9. 部署和配置

### 9.1 环境变量
```bash
# 服务配置
HOST=0.0.0.0
PORT=3000
DEBUG=false

# 文件处理
TEMP_IMAGE_DIR=./temp_images
MAX_FILE_SIZE=104857600  # 100MB

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=./logs/api.log
```

### 9.2 Docker部署
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 3000

CMD ["python", "run_server.py"]
```

### 9.3 nginx配置
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # 静态文件服务
    location /static/ {
        proxy_pass http://localhost:3000;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
```

## 10. 总结

新的统一API设计具有以下优势：

1. **简化接口** - 单一端点处理所有转换需求
2. **灵活调用** - 支持文件上传和JSON两种方式
3. **自动检测** - 根据文件扩展名自动选择处理器
4. **批量处理** - 原生支持多文件转换
5. **标准兼容** - 符合RESTful设计原则和HTTP标准
6. **易于集成** - 支持HTML表单、Ajax、各种编程语言
7. **完整文档** - 提供详细的API文档和使用示例

这种设计使API更加直观和易用，同时保持了强大的功能和灵活性。 