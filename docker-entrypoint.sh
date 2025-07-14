#!/bin/bash
set -e

# 颜色输出函数
print_info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

# 默认配置
DEFAULT_HOST=${HOST:-"0.0.0.0"}
DEFAULT_PORT=${PORT:-3000}
DEFAULT_WORKERS=${WORKERS:-4}
DEFAULT_WORKER_CLASS=${WORKER_CLASS:-"uvicorn.workers.UvicornWorker"}
DEFAULT_MAX_REQUESTS=${MAX_REQUESTS:-1000}
DEFAULT_MAX_REQUESTS_JITTER=${MAX_REQUESTS_JITTER:-100}
DEFAULT_KEEPALIVE=${KEEPALIVE:-5}
DEFAULT_LOG_LEVEL=${LOG_LEVEL:-"info"}
DEFAULT_ENVIRONMENT=${ENVIRONMENT:-"production"}

# 显示启动信息
print_info "🚀 Any2Markdown MCP Server Docker Entrypoint"
print_info "Environment: $DEFAULT_ENVIRONMENT"
print_info "Host: $DEFAULT_HOST"
print_info "Port: $DEFAULT_PORT"

# 确定工作目录
WORK_DIR=${PWD}
if [ -d "/app" ]; then
    WORK_DIR="/app"
fi

# 确保必要的目录存在
mkdir -p ${WORK_DIR}/logs
mkdir -p ${WORK_DIR}/temp_images
mkdir -p ${WORK_DIR}/uploads

# 确保目录权限正确（使用root权限）
chmod -R 755 ${WORK_DIR}/logs 2>/dev/null || true
chmod -R 755 ${WORK_DIR}/temp_images 2>/dev/null || true
chmod -R 755 ${WORK_DIR}/uploads 2>/dev/null || true

# 确保缓存目录权限正确
mkdir -p /root/.cache/marker /root/.cache/huggingface /root/.cache/torch /root/.cache/transformers
chmod -R 755 /root/.cache 2>/dev/null || true

# 检查Python环境
print_info "🐍 Checking Python environment..."
python --version
pip --version

# 检查模型和依赖
print_info "🔍 Checking marker-pdf installation..."
python -c "import marker; print('✅ marker-pdf is available')" 2>/dev/null || {
    print_warning "marker-pdf not found, please install it manually"
}

# 健康检查函数
health_check() {
    print_info "🏥 Running health check..."
    python -c "
import sys
try:
    from src.any2markdown_mcp.server import create_app
    print('✅ Server module imports successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
" 2>/dev/null || {
    print_warning "Health check failed, but continuing..."
}
}

# 执行健康检查
health_check

# 设置环境变量
export PYTHONPATH="${WORK_DIR}:$PYTHONPATH"
export PYTHONUNBUFFERED=1

# 根据环境选择启动方式
if [ "$DEFAULT_ENVIRONMENT" = "development" ]; then
    print_success "🔧 Development mode detected"
    print_info "Starting with hot-reload enabled..."
    
    exec uvicorn src.any2markdown_mcp.server:create_app \
        --factory \
        --host "$DEFAULT_HOST" \
        --port "$DEFAULT_PORT" \
        --reload \
        --reload-dir "src" \
        --log-level debug \
        --access-log \
        --use-colors
        
elif [ "$DEFAULT_ENVIRONMENT" = "testing" ]; then
    print_success "🧪 Testing mode detected"
    print_info "Starting with test configuration..."
    
    exec uvicorn src.any2markdown_mcp.server:create_app \
        --factory \
        --host "$DEFAULT_HOST" \
        --port "$DEFAULT_PORT" \
        --workers 1 \
        --log-level debug \
        --access-log
        
else
    print_success "🏭 Production mode detected"
    print_info "Starting with optimized production configuration..."
    print_info "Workers: $DEFAULT_WORKERS"
    print_info "Worker Class: $DEFAULT_WORKER_CLASS"
    print_info "Max Requests: $DEFAULT_MAX_REQUESTS"
    print_info "Keep Alive: $DEFAULT_KEEPALIVE seconds"
    
    # 生产模式使用Python直接运行服务器脚本
    print_info "使用Python直接启动服务器..."
    exec python run_server.py
fi 