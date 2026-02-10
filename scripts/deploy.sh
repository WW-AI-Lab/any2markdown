#!/bin/bash

# Any2Markdown MCP Server 部署脚本
# 支持源码部署和Docker部署两种方式

set -e

# 默认 PyPI 镜像（可通过环境变量 PIP_INDEX_URL 覆盖）
DEFAULT_PIP_INDEX_URL="https://repo.huaweicloud.com/repository/pypi/simple"
PIP_INDEX_URL="${PIP_INDEX_URL:-$DEFAULT_PIP_INDEX_URL}"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
Any2Markdown MCP Server 部署脚本

用法: $0 [选项] <部署方式>

部署方式:
  source        源码部署（推荐开发环境）
  docker        Docker容器部署（推荐生产环境）
  docker-gpu    Docker GPU版本部署（需要NVIDIA GPU）

选项:
  -h, --help    显示此帮助信息
  -p, --port    指定端口号（默认: 3000）
  -e, --env     指定环境文件路径（默认: .env）
  --no-gpu      禁用GPU支持（仅源码部署）
  --dev         开发模式（启用调试日志）

环境变量:
  PIP_INDEX_URL 指定依赖安装镜像源（默认: https://repo.huaweicloud.com/repository/pypi/simple）

示例:
  $0 source                    # 源码部署，使用默认配置
  $0 docker -p 8080           # Docker部署，使用8080端口
  $0 docker-gpu --dev         # GPU Docker部署，开发模式
  $0 source --no-gpu -e .env.prod  # 源码部署，禁用GPU，使用生产环境配置

EOF
}

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查Python版本
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 未安装"
        exit 1
    fi
    
    # 修复版本比较逻辑
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    major_version=$(echo "$python_version" | cut -d. -f1)
    minor_version=$(echo "$python_version" | cut -d. -f2)
    
    # 检查是否满足Python 3.10-3.13要求
    if [[ $major_version -lt 3 ]] || [[ $major_version -eq 3 && $minor_version -lt 10 ]] || [[ $major_version -eq 3 && $minor_version -ge 14 ]]; then
        log_error "Python版本必须在 3.10-3.13 范围内，当前版本: $python_version"
        exit 1
    fi
    
    log_success "Python版本检查通过: $python_version"
}

# 检查并创建虚拟环境
check_and_create_venv() {
    log_info "检查Python虚拟环境..."
    
    if [[ ! -d ".venv" ]]; then
        log_info "虚拟环境不存在，正在创建..."
        python3 -m venv .venv
        if [[ $? -ne 0 ]]; then
            log_error "创建虚拟环境失败"
            exit 1
        fi
        log_success "虚拟环境创建成功"
    else
        log_info "虚拟环境已存在"
    fi
    
    # 激活虚拟环境
    log_info "激活虚拟环境..."
    source .venv/bin/activate
    
    # 验证虚拟环境
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        log_error "虚拟环境激活失败"
        exit 1
    fi
    
    log_success "虚拟环境激活成功: $VIRTUAL_ENV"
}

# 检查并创建环境配置文件
check_and_create_env() {
    log_info "检查环境配置文件..."
    
    if [[ ! -f ".env" ]]; then
        if [[ -f "env.example" ]]; then
            log_info "环境文件不存在，从 env.example 复制..."
            cp env.example .env
            if [[ $? -ne 0 ]]; then
                log_error "复制环境文件失败"
                exit 1
            fi
            log_success "环境文件创建成功"
        else
            log_error "env.example 文件不存在，无法创建环境配置"
            exit 1
        fi
    else
        log_info "环境配置文件已存在"
    fi
}

# 检查Docker要求
check_docker_requirements() {
    log_info "检查Docker环境..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装"
        exit 1
    fi
    
    # 检查Docker是否运行
    if ! docker info &> /dev/null; then
        log_error "Docker 服务未运行"
        exit 1
    fi
    
    log_success "Docker环境检查通过"
}

# 设置环境配置
setup_environment() {
    local env_file=${ENV_FILE:-.env}
    
    log_info "设置环境配置..."
    
    # 更新端口配置
    if [[ -n "$PORT" ]]; then
        log_info "设置端口为: $PORT"
        sed -i.bak "s/MCP_SERVER_PORT=.*/MCP_SERVER_PORT=$PORT/" "$env_file"
    fi
    
    # 开发模式配置
    if [[ "$DEV_MODE" == "true" ]]; then
        log_info "启用开发模式"
        sed -i.bak "s/LOG_LEVEL=.*/LOG_LEVEL=DEBUG/" "$env_file"
        sed -i.bak "s/DEBUG=.*/DEBUG=true/" "$env_file"
    fi
    
    # GPU配置
    if [[ "$NO_GPU" == "true" ]]; then
        log_info "禁用GPU支持"
        sed -i.bak "s/USE_GPU=.*/USE_GPU=false/" "$env_file"
    fi
    
    log_success "环境配置完成"
}

# 源码部署
deploy_source() {
    log_info "开始源码部署..."
    
    check_requirements
    check_and_create_venv
    check_and_create_env
    setup_environment
    
    # 安装依赖
    log_info "安装Python依赖..."
    log_info "使用镜像源: $PIP_INDEX_URL"
    pip install -i "$PIP_INDEX_URL" --upgrade pip
    pip install -i "$PIP_INDEX_URL" -r requirements.txt
    
    # 创建必要目录
    mkdir -p logs temp_images
    
    # 启动服务器
    log_info "启动MCP服务器..."
    log_info "服务器将在 http://localhost:${PORT:-3000} 启动"
    log_info "API文档: http://localhost:${PORT:-3000}/api/v1/docs"
    
    # 检查是否在开发模式
    if [[ "$DEV_MODE" == "true" ]]; then
        log_info "开发模式：前台运行，按 Ctrl+C 停止服务器"
        python run_server.py
    else
        log_info "生产模式：后台运行"
        nohup python run_server.py > server.log 2>&1 &
        server_pid=$!
        log_info "服务器已启动，PID: $server_pid"
        log_info "日志文件: server.log"
        
        # 等待服务器启动
        sleep 5
        
        # 检查服务器是否成功启动
        if curl -s http://localhost:${PORT:-3000}/health > /dev/null; then
            log_success "服务器启动成功！"
            log_info "服务地址: http://localhost:${PORT:-3000}"
            log_info "API文档: http://localhost:${PORT:-3000}/api/v1/docs"
            log_info "查看日志: tail -f server.log"
            log_info "停止服务: kill $server_pid"
        else
            log_error "服务器启动失败，请检查日志"
            tail -20 server.log
            exit 1
        fi
    fi
}

# Docker部署
deploy_docker() {
    local gpu_support=${1:-false}
    
    log_info "开始Docker部署..."
    
    check_docker_requirements
    setup_environment
    
    # 构建镜像
    log_info "构建Docker镜像..."
    docker-compose build any2markdown-mcp
    
    # 启动服务
    if [[ "$gpu_support" == "true" ]]; then
        log_info "启动GPU版本Docker容器..."
        docker-compose --profile gpu up -d any2markdown-mcp-gpu
        container_name="any2markdown-gpu"
        port=${PORT:-3001}
    else
        log_info "启动标准Docker容器..."
        docker-compose up -d any2markdown-mcp
        container_name="any2markdown"
        port=${PORT:-3000}
    fi
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    if docker ps | grep -q "$container_name"; then
        log_success "Docker容器启动成功"
        log_info "服务地址: http://localhost:$port"
        log_info "API文档: http://localhost:$port/api/v1/docs"
        log_info "健康检查: http://localhost:$port/health"
        
        # 显示日志
        log_info "容器日志 (按 Ctrl+C 停止显示):"
        docker-compose logs -f
    else
        log_error "Docker容器启动失败"
        docker-compose logs
        exit 1
    fi
}

# 停止服务
stop_services() {
    log_info "停止所有服务..."
    
    # 停止Docker服务
    if command -v docker-compose &> /dev/null; then
        docker-compose down
    fi
    
    # 停止源码服务（通过进程名）
    pkill -f "python.*run_server.py" || true
    
    log_success "服务已停止"
}

# 清理资源
cleanup() {
    log_info "清理资源..."
    
    # 清理Docker资源
    if command -v docker &> /dev/null; then
        docker system prune -f
    fi
    
    # 清理临时文件
    rm -rf temp_images/*
    rm -rf logs/*.log.bak
    rm -f .env.bak
    
    log_success "清理完成"
}

# 显示服务状态
show_status() {
    log_info "服务状态:"
    
    # Docker状态
    if command -v docker-compose &> /dev/null; then
        echo "Docker容器:"
        docker-compose ps
    fi
    
    # 源码进程状态
    echo -e "\n源码进程:"
    pgrep -f "python.*run_server.py" || echo "无运行中的源码进程"
    
    # 端口占用情况
    echo -e "\n端口占用:"
    netstat -tlnp 2>/dev/null | grep ":3000\|:3001" || echo "端口3000/3001未被占用"
}

# 解析命令行参数
PORT=""
ENV_FILE=""
NO_GPU="false"
DEV_MODE="false"
DEPLOY_MODE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -e|--env)
            ENV_FILE="$2"
            shift 2
            ;;
        --no-gpu)
            NO_GPU="true"
            shift
            ;;
        --dev)
            DEV_MODE="true"
            shift
            ;;
        source|docker|docker-gpu)
            DEPLOY_MODE="$1"
            shift
            ;;
        stop)
            stop_services
            exit 0
            ;;
        status)
            show_status
            exit 0
            ;;
        cleanup)
            cleanup
            exit 0
            ;;
        *)
            log_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检查部署方式
if [[ -z "$DEPLOY_MODE" ]]; then
    log_error "请指定部署方式: source, docker, 或 docker-gpu"
    show_help
    exit 1
fi

# 执行部署
case $DEPLOY_MODE in
    source)
        deploy_source
        ;;
    docker)
        deploy_docker false
        ;;
    docker-gpu)
        deploy_docker true
        ;;
    *)
        log_error "无效的部署方式: $DEPLOY_MODE"
        exit 1
        ;;
esac 
