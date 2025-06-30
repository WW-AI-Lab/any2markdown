#!/bin/bash

# 模型缓存目录设置脚本
# 用于初始化模型缓存目录结构

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Any2Markdown 模型缓存目录设置 ===${NC}"

# 默认缓存目录
DEFAULT_CACHE_ROOT="./models"
CACHE_ROOT="${1:-$DEFAULT_CACHE_ROOT}"

echo -e "${YELLOW}缓存根目录: $CACHE_ROOT${NC}"

# 创建缓存目录结构
CACHE_DIRS=(
    "$CACHE_ROOT/marker"
    "$CACHE_ROOT/huggingface/hub"
    "$CACHE_ROOT/huggingface/assets"
    "$CACHE_ROOT/torch"
    "$CACHE_ROOT/transformers"
)

echo -e "${YELLOW}创建缓存目录结构...${NC}"
for dir in "${CACHE_DIRS[@]}"; do
    if mkdir -p "$dir"; then
        echo -e "${GREEN}✓ 创建目录: $dir${NC}"
    else
        echo -e "${RED}✗ 创建目录失败: $dir${NC}"
        exit 1
    fi
done

# 创建说明文件
cat > "$CACHE_ROOT/README.md" << 'EOF'
# 模型缓存目录说明

这个目录用于存储Any2Markdown系统使用的各种机器学习模型缓存。

## 目录结构

- `marker/` - Marker-PDF模型缓存
- `huggingface/` - Hugging Face模型缓存
  - `hub/` - 模型仓库缓存
  - `assets/` - 资产文件缓存
- `torch/` - PyTorch模型缓存
- `transformers/` - Transformers库模型缓存

## 使用说明

### 本地开发
设置环境变量指向这些目录：
```bash
export MODEL_CACHE_DIR=/path/to/models/marker
export HF_HOME=/path/to/models/huggingface
export TORCH_HOME=/path/to/models/torch
export TRANSFORMERS_CACHE=/path/to/models/transformers
```

### Docker部署
使用volume挂载持久化模型数据：
```bash
docker run -v ./models/marker:/home/appuser/.cache/marker \
           -v ./models/huggingface:/home/appuser/.cache/huggingface \
           -v ./models/torch:/home/appuser/.cache/torch \
           -v ./models/transformers:/home/appuser/.cache/transformers \
           any2markdown:latest
```

### Docker Compose
已在docker-compose.yml中配置了相应的volume挂载。

## 注意事项

1. 首次运行时，系统会自动下载所需模型，可能需要较长时间
2. 模型文件较大，建议确保有足够的磁盘空间（建议至少10GB）
3. 网络环境需要能够访问Hugging Face Hub
4. 如果使用GPU，确保CUDA环境正确配置
EOF

echo -e "${GREEN}✓ 创建说明文件: $CACHE_ROOT/README.md${NC}"

# 设置权限（如果需要）
if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "cygwin" ]]; then
    chmod -R 755 "$CACHE_ROOT"
    echo -e "${GREEN}✓ 设置目录权限${NC}"
fi

# 输出环境变量建议
echo -e "\n${YELLOW}=== 环境变量配置建议 ===${NC}"
echo -e "将以下环境变量添加到您的 .env 文件中："
echo ""
echo "MODEL_CACHE_DIR=$(realpath "$CACHE_ROOT/marker")"
echo "HF_HOME=$(realpath "$CACHE_ROOT/huggingface")"
echo "HF_HUB_CACHE=$(realpath "$CACHE_ROOT/huggingface/hub")"
echo "HF_ASSETS_CACHE=$(realpath "$CACHE_ROOT/huggingface/assets")"
echo "TORCH_HOME=$(realpath "$CACHE_ROOT/torch")"
echo "TRANSFORMERS_CACHE=$(realpath "$CACHE_ROOT/transformers")"
echo ""

# 检查磁盘空间
if command -v df &> /dev/null; then
    AVAILABLE_SPACE=$(df -h "$(dirname "$CACHE_ROOT")" | awk 'NR==2 {print $4}')
    echo -e "${YELLOW}当前可用磁盘空间: $AVAILABLE_SPACE${NC}"
    echo -e "${YELLOW}建议确保至少有10GB可用空间用于模型缓存${NC}"
fi

echo -e "\n${GREEN}=== 设置完成！ ===${NC}"
echo -e "缓存目录已创建在: $(realpath "$CACHE_ROOT")"
echo -e "您现在可以启动Any2Markdown服务，系统将自动使用这些缓存目录。" 