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
PIP_INDEX_URL="${PIP_INDEX_URL:-}"
PULL_AFTER_PUSH="${PULL_AFTER_PUSH:-1}"

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

# 根据公网IP归属地选择更快的 Python 依赖源
select_pip_mirror() {
    echo_info "检测公网网络归属地并选择依赖源..."

    # 允许外部手动覆盖
    if [ -n "$PIP_INDEX_URL" ]; then
        echo_info "使用外部指定依赖源: ${PIP_INDEX_URL}"
        return
    fi

    local geo_json country_code
    geo_json="$(curl -sS https://ipwho.is || true)"
    if command -v jq >/dev/null 2>&1; then
        country_code="$(echo "$geo_json" | jq -r '.country_code // empty' 2>/dev/null || true)"
    else
        country_code="$(echo "$geo_json" | sed -n 's/.*"country_code":"\([A-Z][A-Z]\)".*/\1/p' | head -n1)"
    fi

    if [ "$country_code" = "CN" ]; then
        PIP_INDEX_URL="https://repo.huaweicloud.com/repository/pypi/simple"
    else
        # 当前实际网络归属地为美国，优先官方 PyPI
        PIP_INDEX_URL="https://pypi.org/simple"
    fi

    echo_info "地理归属地: ${country_code:-unknown}"
    echo_info "构建依赖源: ${PIP_INDEX_URL}"
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
        --build-arg "PIP_INDEX_URL=${PIP_INDEX_URL}" \
        --push \
        --progress=plain \
        .
    
    echo_success "镜像构建和推送完成"
}

# 验证镜像
verify_image() {
    echo_info "验证推送的镜像..."

    local max_retries=12
    local retry=1
    local sleep_seconds=5

    while [ "$retry" -le "$max_retries" ]; do
        if docker buildx imagetools inspect "${FULL_IMAGE_NAME}" &> /dev/null || docker manifest inspect "${FULL_IMAGE_NAME}" &> /dev/null; then
            echo_success "镜像验证成功（第 ${retry}/${max_retries} 次）"
            echo_info "镜像详细信息："

            if docker manifest inspect "${FULL_IMAGE_NAME}" | jq -r '.manifests[] | "Platform: \(.platform.os)/\(.platform.architecture)"' 2>/dev/null; then
                true
            else
                docker buildx imagetools inspect "${FULL_IMAGE_NAME}" || true
            fi
            return
        fi

        echo_warning "镜像暂未可见（第 ${retry}/${max_retries} 次），${sleep_seconds}s 后重试..."
        sleep "${sleep_seconds}"
        retry=$((retry + 1))
    done

    echo_error "镜像验证失败：推送成功但仓库侧在重试窗口内仍未查询到 manifest"
    echo_info "可手动执行: docker buildx imagetools inspect ${FULL_IMAGE_NAME}"
    exit 1
}

pull_image_to_local() {
    if [ "${PULL_AFTER_PUSH}" != "1" ]; then
        echo_info "跳过本地拉取（PULL_AFTER_PUSH=${PULL_AFTER_PUSH}）"
        return
    fi

    echo_info "拉取镜像到本地（当前架构）..."
    docker pull "${FULL_IMAGE_NAME}"
    echo_success "本地镜像拉取完成"
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
    echo "  PIP_INDEX_URL      手动指定构建依赖源（默认按公网归属地自动选择）"
    echo "  PULL_AFTER_PUSH    推送后是否拉取到本地(1/0，默认: 1)"
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
    select_pip_mirror
    login_registry
    build_and_push
    verify_image
    pull_image_to_local
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
