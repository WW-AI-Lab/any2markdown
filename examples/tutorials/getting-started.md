# Any2Markdown 快速入门指南

欢迎使用 Any2Markdown MCP Server！本指南将在5分钟内带您上手使用。

## 🎯 目标

完成本指南后，您将能够：
- ✅ 成功启动 Any2Markdown 服务器
- ✅ 使用 RESTful API 转换您的第一个文档
- ✅ 理解基本的配置选项
- ✅ 知道如何获取帮助

## 📋 前置要求

- Python 3.9+ 
- 4GB+ 内存
- 基本的命令行知识

## 🚀 第一步：安装和启动

### 1.1 克隆项目

```bash
git clone https://github.com/WW-AI-Lab/any2markdown.git
cd any2markdown
```

### 1.2 安装依赖

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 1.3 启动服务器

```bash
# 方式1: 直接启动（推荐新手）
python run_server.py

# 方式2: 使用部署脚本
./deploy.sh source
```

看到以下输出表示启动成功：
```
启动 MCP 服务器在 0.0.0.0:3000
FastMCP 服务器已创建，将在 0.0.0.0:3000 启动
```

### 1.4 验证服务

打开新终端，测试服务是否正常：
```bash
curl http://localhost:3000/api/v1/status
```

应该看到类似输出：
```json
{
  "success": true,
  "data": {
    "service": "any2markdown",
    "status": "healthy"
  }
}
```

## 📄 第二步：转换您的第一个文档

### 2.1 准备测试文档

找一个PDF、Word或Excel文档，或者下载示例文件：
```bash
# 创建示例目录
mkdir -p examples/sample-files

# 下载示例文档（可选）
# 或者复制您自己的文档到该目录
```

### 2.2 使用文件上传方式转换

```bash
# 转换PDF文档
curl -X POST "http://localhost:3000/api/v1/convert" \
  -F "file=@your-document.pdf" \
  -F "extract_images=true" \
  -F "include_content=true"

# 转换Word文档
curl -X POST "http://localhost:3000/api/v1/convert" \
  -F "file=@your-document.docx" \
  -F "preserve_formatting=true" \
  -F "include_content=true"
```

### 2.3 理解响应结果

成功的响应包含：
```json
{
  "success": true,
  "data": {
    "markdown_content": "# 文档标题\n\n转换后的内容...",
    "metadata": {
      "source_type": "pdf",
      "total_pages": 5,
      "images_extracted": 2,
      "processing_time": 3.45
    },
    "images": [
      {
        "filename": "image_1.png",
        "url": "http://localhost:3000/static/image_1.png"
      }
    ]
  }
}
```

## 🔧 第三步：常用配置选项

### 3.1 控制输出内容

```bash
# 只获取元数据，不获取转换内容（适合大文档）
curl -X POST "http://localhost:3000/api/v1/convert" \
  -F "file=@document.pdf" \
  -F "include_content=false"

# 指定页面范围（仅PDF）
curl -X POST "http://localhost:3000/api/v1/convert" \
  -F "file=@document.pdf" \
  -F "start_page=0" \
  -F "end_page=5"
```

### 3.2 图片处理

```bash
# 提取图片
curl -X POST "http://localhost:3000/api/v1/convert" \
  -F "file=@document.pdf" \
  -F "extract_images=true"

# 不提取图片（更快）
curl -X POST "http://localhost:3000/api/v1/convert" \
  -F "file=@document.pdf" \
  -F "extract_images=false"
```

### 3.3 输出格式

```bash
# Markdown格式（默认）
curl -X POST "http://localhost:3000/api/v1/convert" \
  -F "file=@document.pdf" \
  -F "output_format=markdown"

# HTML格式
curl -X POST "http://localhost:3000/api/v1/convert" \
  -F "file=@document.pdf" \
  -F "output_format=html"
```

## 🌐 第四步：使用Web界面

打开浏览器访问：
- **API文档**: http://localhost:3000/api/v1/docs
- **OpenAPI规范**: http://localhost:3000/api/v1/openapi.json

在API文档页面，您可以：
- 📖 查看完整的API说明
- 🧪 直接测试API端点
- 📥 下载API规范文件

## 🐛 第五步：故障排除

### 5.1 常见问题

**问题**: 服务启动失败
```bash
# 检查端口占用
lsof -i :3000

# 修改端口
MCP_SERVER_PORT=8080 python run_server.py
```

**问题**: 转换失败
```bash
# 检查文件格式
file your-document.pdf

# 查看详细错误
curl -v "http://localhost:3000/api/v1/convert" -F "file=@document.pdf"
```

**问题**: 内存不足
```bash
# 减少并发任务
export MAX_CONCURRENT_JOBS=1
python run_server.py
```

### 5.2 获取帮助

- 📚 查看完整文档: `docs/`目录
- 🐛 报告问题: GitHub Issues
- 💬 社区讨论: GitHub Discussions

## 🎉 下一步

恭喜！您已经成功完成了快速入门。接下来可以：

1. **深入学习**: 阅读 [高级用法指南](advanced-usage.md)
2. **集成应用**: 查看 [Python客户端示例](../restful-api/python/)
3. **部署生产**: 参考 [部署指南](../deployment/)
4. **MCP协议**: 尝试 [MCP客户端示例](../mcp-protocol/)

## 📊 性能提示

- 🚀 **大文档**: 设置 `include_content=false` 只获取元数据
- 🖼️ **图片处理**: 不需要图片时设置 `extract_images=false`
- 📄 **PDF优化**: 使用 `start_page` 和 `end_page` 处理部分页面
- ⚡ **批量处理**: 使用多文件上传一次处理多个文档

---

**需要帮助？** 查看 [故障排除指南](troubleshooting.md) 或提交 [GitHub Issue](https://github.com/WW-AI-Lab/any2markdown/issues)。 