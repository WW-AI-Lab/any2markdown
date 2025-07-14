#!/bin/bash

# Any2Markdown MCP Server 多平台 Docker 镜像构建和推送脚本
# 目标平台：linux/amd64 (x86_64), linux/arm64 (ARM)
# 推送到：ccr.ccs.tencentyun.com/yfgaia/

set -e

# 配置变量
REGISTRY="ccr.ccs.tencentyun.com"
NAMESPACE="yfgaia"
IMAGE_NAME="any2markdown-mcp-server"
TAG="${1:-latest}"
FULL_IMAGE_NAME="${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:${TAG}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查必要工具
check_requirements() {
    echo_info "检查构建环境..."
    
    if ! command -v docker &> /dev/null; then
        echo_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    # 检查 Docker Buildx
    if ! docker buildx version &> /dev/null; then
        echo_error "Docker Buildx 未安装，请升级 Docker 到最新版本"
        exit 1
    fi
    
    echo_success "构建环境检查通过"
}

# 创建并使用 buildx builder
setup_buildx() {
    echo_info "设置 Docker Buildx..."
    
    # 创建新的 builder 实例（如果不存在）
    if ! docker buildx ls | grep -q "multiarch-builder"; then
        echo_info "创建多架构构建器..."
        docker buildx create --name multiarch-builder --driver docker-container --bootstrap
    fi
    
    # 使用该 builder
    docker buildx use multiarch-builder
    
    # 启动 builder
    docker buildx inspect --bootstrap
    
    echo_success "Buildx 设置完成"
}

# 登录腾讯云镜像仓库
login_registry() {
    echo_info "登录腾讯云容器镜像仓库..."
    
    if [ -z "$DOCKER_USERNAME" ] || [ -z "$DOCKER_PASSWORD" ]; then
        echo_warning "未设置环境变量 DOCKER_USERNAME 和 DOCKER_PASSWORD"
        echo_info "请输入腾讯云镜像仓库凭据："
        read -p "用户名: " username
        read -s -p "密码: " password
        echo
        
        echo "$password" | docker login "$REGISTRY" --username "$username" --password-stdin
    else
        echo "$DOCKER_PASSWORD" | docker login "$REGISTRY" --username "$DOCKER_USERNAME" --password-stdin
    fi
    
    echo_success "登录成功"
}

# 构建并推送多平台镜像
build_and_push() {
    echo_info "开始构建多平台镜像..."
    echo_info "镜像名称: ${FULL_IMAGE_NAME}"
    echo_info "目标平台: linux/amd64, linux/arm64"
    
    # 切换到项目根目录
    cd "$(dirname "$0")/.."
    
    # 构建并推送多平台镜像
    docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --tag "${FULL_IMAGE_NAME}" \
        --push \
        --progress=plain \
        .
    
    echo_success "镜像构建和推送完成"
}

# 验证镜像
verify_image() {
    echo_info "验证推送的镜像..."
    
    # 检查镜像是否存在
    if docker manifest inspect "${FULL_IMAGE_NAME}" &> /dev/null; then
        echo_success "镜像验证成功"
        
        # 显示镜像信息
        echo_info "镜像详细信息："
        docker manifest inspect "${FULL_IMAGE_NAME}" | jq -r '.manifests[] | "Platform: \(.platform.os)/\(.platform.architecture)"'
    else
        echo_error "镜像验证失败"
        exit 1
    fi
}

# 清理
cleanup() {
    echo_info "清理构建环境..."
    
    # 可选：删除 builder（如果需要）
    # docker buildx rm multiarch-builder
    
    echo_success "清理完成"
}

# 显示使用说明
show_usage() {
    echo "用法: $0 [TAG]"
    echo ""
    echo "参数:"
    echo "  TAG    镜像标签 (默认: latest)"
    echo ""
    echo "环境变量 (可选):"
    echo "  DOCKER_USERNAME    腾讯云镜像仓库用户名"
    echo "  DOCKER_PASSWORD    腾讯云镜像仓库密码"
    echo ""
    echo "示例:"
    echo "  $0                 # 构建 latest 标签"
    echo "  $0 v1.0.0         # 构建 v1.0.0 标签"
    echo ""
}

# 主函数
main() {
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_usage
        exit 0
    fi
    
    echo_info "=== Any2Markdown MCP Server 多平台 Docker 构建 ==="
    echo_info "目标镜像: ${FULL_IMAGE_NAME}"
    echo ""
    
    check_requirements
    setup_buildx
    login_registry
    build_and_push
    verify_image
    cleanup
    
    echo ""
    echo_success "=== 构建完成 ==="
    echo_info "镜像已成功推送到: ${FULL_IMAGE_NAME}"
    echo_info "支持平台: linux/amd64, linux/arm64"
    echo ""
    echo_info "拉取命令:"
    echo "  docker pull ${FULL_IMAGE_NAME}"
    echo ""
    echo_info "运行命令:"
    echo "  docker run -d -p 3000:3000 --name any2markdown-mcp-server ${FULL_IMAGE_NAME}"
}

# 错误处理
trap 'echo_error "构建过程中发生错误，退出码: $?"' ERR

# 执行主函数
main "$@" 