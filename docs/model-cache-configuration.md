# 模型缓存配置指南

Any2Markdown 使用 marker-pdf 进行 PDF 转换，该工具依赖多个机器学习模型。为了提高性能并避免重复下载，系统支持配置模型缓存目录。

## 📋 模型缓存概述

### 使用的模型类型

1. **Marker-PDF 模型**
   - 用于 PDF 文档解析和转换
   - 包括 OCR、版面分析等模型
   - 缓存位置：`MODEL_CACHE_DIR`

2. **Hugging Face 模型**
   - Transformers 模型（文本处理）
   - Tokenizers（文本分词）
   - 缓存位置：`HF_HOME`

3. **PyTorch 模型**
   - 预训练的深度学习模型
   - 缓存位置：`TORCH_HOME`

4. **其他依赖模型**
   - 各种 NLP 和 CV 模型
   - 缓存位置：`TRANSFORMERS_CACHE`

## ⚙️ 配置方法

### 1. 环境变量配置

在 `.env` 文件中设置：

```bash
# Marker-PDF 模型缓存
MODEL_CACHE_DIR=/path/to/models/marker

# Hugging Face 模型缓存
HF_HOME=/path/to/models/huggingface
HF_HUB_CACHE=/path/to/models/huggingface/hub
HF_ASSETS_CACHE=/path/to/models/huggingface/assets

# PyTorch 模型缓存
TORCH_HOME=/path/to/models/torch

# Transformers 模型缓存
TRANSFORMERS_CACHE=/path/to/models/transformers

# 下载配置
HF_HUB_ENABLE_HF_TRANSFER=false  # 使用 hf_transfer 加速下载
HF_HUB_DISABLE_PROGRESS_BARS=false  # 显示下载进度条
HF_HUB_DISABLE_TELEMETRY=true  # 禁用遥测数据收集
```

### 2. 配置文件设置

在 `config.toml` 中配置：

```toml
[models]
# 基础配置
cache_dir = "/path/to/models/marker"
enable_gpu = true
preload_models = true

# Hugging Face 配置
hf_home = "/path/to/models/huggingface"
hf_hub_cache = "/path/to/models/huggingface/hub"
hf_assets_cache = "/path/to/models/huggingface/assets"
torch_home = "/path/to/models/torch"
transformers_cache = "/path/to/models/transformers"

# 下载选项
hf_hub_enable_hf_transfer = false
hf_hub_disable_progress_bars = false
hf_hub_disable_telemetry = true
```

## 🐳 Docker 部署配置

### 1. 使用 Docker Compose（推荐）

`docker-compose.yml` 已预配置模型缓存挂载：

```yaml
services:
  any2markdown-mcp:
    volumes:
      # 模型缓存目录挂载
      - ./models/marker:/home/appuser/.cache/marker
      - ./models/huggingface:/home/appuser/.cache/huggingface
      - ./models/torch:/home/appuser/.cache/torch
      - ./models/transformers:/home/appuser/.cache/transformers
```

启动前初始化目录：

```bash
# 创建缓存目录结构
./scripts/setup_model_cache.sh

# 启动服务
docker-compose up -d
```

### 2. 手动 Docker 运行

```bash
# 创建本地缓存目录
mkdir -p models/{marker,huggingface,torch,transformers}

# 运行容器并挂载缓存目录
docker run -d \
  --name any2markdown \
  -p 3000:3000 \
  -v $(pwd)/models/marker:/home/appuser/.cache/marker \
  -v $(pwd)/models/huggingface:/home/appuser/.cache/huggingface \
  -v $(pwd)/models/torch:/home/appuser/.cache/torch \
  -v $(pwd)/models/transformers:/home/appuser/.cache/transformers \
  -e MODEL_CACHE_DIR=/home/appuser/.cache/marker \
  -e HF_HOME=/home/appuser/.cache/huggingface \
  any2markdown:latest
```

### 3. GPU 环境配置

对于 GPU 加速环境，需要额外配置：

```bash
# 使用 GPU 版本的 Docker Compose
docker-compose --profile gpu up -d

# 或手动运行 GPU 容器
docker run -d \
  --name any2markdown-gpu \
  --gpus all \
  -p 3000:3000 \
  -v $(pwd)/models:/home/appuser/.cache \
  -e USE_GPU=true \
  -e CUDA_VISIBLE_DEVICES=0 \
  any2markdown:latest
```

## 📁 目录结构

使用 `setup_model_cache.sh` 脚本会创建如下目录结构：

```
models/
├── marker/                 # Marker-PDF 模型缓存
├── huggingface/           # Hugging Face 模型缓存
│   ├── hub/              # 模型仓库缓存
│   └── assets/           # 资产文件缓存
├── torch/                # PyTorch 模型缓存
├── transformers/         # Transformers 库缓存
└── README.md            # 缓存目录说明
```

## 🚀 首次启动

### 模型下载过程

首次启动时，系统会自动下载所需模型：

1. **下载时间**：根据网络速度，可能需要 10-30 分钟
2. **下载大小**：约 3-5GB 模型文件
3. **下载来源**：主要从 Hugging Face Hub 下载

### 监控下载进度

```bash
# 查看容器日志
docker logs -f any2markdown

# 监控缓存目录大小变化
watch -n 10 'du -sh models/*'

# 检查网络活动
docker stats any2markdown
```

## 🔧 故障排除

### 常见问题

#### 1. 网络连接问题

```bash
# 错误：无法连接到 Hugging Face Hub
# 解决：配置代理或使用镜像源

# 设置代理
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# 使用国内镜像（如果可用）
export HF_ENDPOINT=https://hf-mirror.com
```

#### 2. 磁盘空间不足

```bash
# 检查可用空间
df -h

# 清理旧的模型缓存
docker system prune -a
rm -rf models/huggingface/hub/models--*/.cache
```

#### 3. 权限问题

```bash
# 修复目录权限
sudo chown -R $USER:$USER models/
chmod -R 755 models/
```

#### 4. 模型加载失败

```bash
# 清理损坏的缓存
rm -rf models/huggingface/hub/models--*/snapshots/*/
docker restart any2markdown
```

### 调试命令

```bash
# 检查环境变量
docker exec any2markdown env | grep -E "(HF_|TORCH_|MODEL_|TRANSFORMERS_)"

# 验证缓存目录
docker exec any2markdown ls -la /home/appuser/.cache/

# 测试模型加载
docker exec any2markdown python -c "
import torch
from transformers import AutoTokenizer
print('PyTorch version:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())
"
```

## 📊 性能优化

### 缓存策略

1. **SSD 存储**：将缓存目录放在 SSD 上以提高 I/O 性能
2. **预加载模型**：设置 `preload_models = true` 在启动时加载模型
3. **内存缓存**：为模型分配足够的系统内存

### 网络优化

```bash
# 启用 hf_transfer 以加速下载（需要安装 hf_transfer）
pip install hf_transfer
export HF_HUB_ENABLE_HF_TRANSFER=1

# 并行下载
export HF_HUB_ENABLE_PARALLEL_DOWNLOAD=1
```

### 容器资源配置

```yaml
# docker-compose.yml 中的资源限制
deploy:
  resources:
    limits:
      memory: 8G      # 为模型加载分配足够内存
      cpus: '4.0'
    reservations:
      memory: 4G
      cpus: '2.0'
```

## 🔒 安全考虑

### 缓存目录安全

```bash
# 设置适当的文件权限
chmod 700 models/
chown -R appuser:appuser models/

# 在生产环境中，考虑使用只读挂载
docker run -v $(pwd)/models:/home/appuser/.cache:ro
```

### 网络安全

```bash
# 限制容器网络访问
docker run --network=custom-network \
  --dns=8.8.8.8 \
  any2markdown:latest
```

## 📈 监控和维护

### 缓存大小监控

```bash
#!/bin/bash
# monitor_cache.sh - 监控缓存大小的脚本

echo "模型缓存使用情况："
echo "==================="
du -sh models/* 2>/dev/null | sort -hr

echo -e "\n磁盘空间使用："
echo "=================="
df -h | grep -E "(Filesystem|/dev/)"

echo -e "\n容器资源使用："
echo "=================="
docker stats --no-stream any2markdown 2>/dev/null || echo "容器未运行"
```

### 定期清理

```bash
#!/bin/bash
# cleanup_cache.sh - 清理过期缓存

# 清理 Hugging Face 临时文件
find models/huggingface -name "*.tmp" -mtime +7 -delete

# 清理 PyTorch 临时文件  
find models/torch -name "*.tmp" -mtime +7 -delete

# 压缩日志文件
gzip logs/*.log.1 2>/dev/null

echo "缓存清理完成"
```

## 📚 参考资源

- [Marker-PDF 官方文档](https://github.com/VikParuchuri/marker)
- [Hugging Face 缓存文档](https://huggingface.co/docs/huggingface_hub/guides/manage-cache)
- [PyTorch 模型缓存](https://pytorch.org/docs/stable/hub.html#caching-logic)
- [Docker Volume 最佳实践](https://docs.docker.com/storage/volumes/) 