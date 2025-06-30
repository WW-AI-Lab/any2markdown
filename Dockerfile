# Any2Markdown MCP Server Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 直接配置pip使用阿里云源（避免系统包管理器问题）
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.timeout 120 && \
    pip config set global.trusted-host mirrors.aliyun.com && \
    pip config set install.trusted-host mirrors.aliyun.com

# 复制依赖文件
COPY requirements-prod.txt ./requirements.txt
COPY pyproject.toml ./

# 安装Python依赖（使用生产环境精简依赖）
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn uvicorn[standard]

# 复制项目文件
COPY src/ ./src/
COPY run_server.py ./
COPY env.example ./
COPY docker-entrypoint.sh ./

# 设置脚本执行权限
RUN chmod +x docker-entrypoint.sh

# 创建必要的目录
RUN mkdir -p logs temp_images uploads

# 创建非root用户（安全最佳实践）
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

# 创建模型缓存目录（支持挂载）
RUN mkdir -p /app/models/cache \
    /app/models/huggingface \
    /app/models/torch \
    /app/models/transformers \
    /home/appuser/.cache/marker \
    /home/appuser/.cache/huggingface \
    /home/appuser/.cache/torch \
    /home/appuser/.cache/transformers

# 设置目录权限
RUN chown -R appuser:appuser /app /home/appuser
USER appuser

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=3000
ENV ENVIRONMENT=production
ENV LOG_LEVEL=info
ENV MAX_CONCURRENT_JOBS=3
ENV WORKERS=4
ENV WORKER_CLASS=uvicorn.workers.UvicornWorker
ENV MAX_REQUESTS=1000
ENV MAX_REQUESTS_JITTER=100
ENV KEEPALIVE=5

# 模型缓存配置（可通过docker run -e 覆盖）
ENV MODEL_CACHE_DIR=/home/appuser/.cache/marker
ENV HF_HOME=/home/appuser/.cache/huggingface
ENV HF_HUB_CACHE=/home/appuser/.cache/huggingface/hub
ENV HF_ASSETS_CACHE=/home/appuser/.cache/huggingface/assets
ENV TORCH_HOME=/home/appuser/.cache/torch
ENV TRANSFORMERS_CACHE=/home/appuser/.cache/transformers
ENV HF_HUB_DISABLE_TELEMETRY=true
ENV HF_HUB_DISABLE_PROGRESS_BARS=false

# 声明挂载点（用于模型缓存持久化）
VOLUME ["/home/appuser/.cache/marker", "/home/appuser/.cache/huggingface", "/home/appuser/.cache/torch", "/home/appuser/.cache/transformers"]

# 暴露端口
EXPOSE 3000

# 简化健康检查（不依赖curl）
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:3000/api/v1/status', timeout=5)" || exit 1

# 使用优化的入口脚本
ENTRYPOINT ["./docker-entrypoint.sh"] 