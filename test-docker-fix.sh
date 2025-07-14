#!/bin/bash

# Any2Markdown MCP Server Docker 权限修复测试脚本

echo "🧪 测试 Docker 权限修复..."

# 清理旧容器
echo "🧹 清理旧容器..."
docker stop any2markdown 2>/dev/null || true
docker rm any2markdown 2>/dev/null || true

# 创建本地目录（如果不存在）
echo "📁 创建本地模型缓存目录..."
mkdir -p ./models/marker
mkdir -p ./models/huggingface  
mkdir -p ./models/torch
mkdir -p ./models/transformers
mkdir -p ./logs
mkdir -p ./temp_images
mkdir -p ./uploads

# 构建镜像
echo "🔨 构建 Docker 镜像..."
docker build -t any2markdown-mcp .

if [ $? -ne 0 ]; then
    echo "❌ Docker 构建失败"
    exit 1
fi

echo "✅ Docker 镜像构建成功"

# 测试直接 docker run
echo "🚀 测试直接 docker run..."
docker run -d \
    --name any2markdown \
    -p 3000:3000 \
    -v ./logs:/app/logs \
    -v ./temp_images:/app/temp_images \
    -v ./uploads:/app/uploads \
    -v ./models/marker:/root/.cache/marker \
    -v ./models/huggingface:/root/.cache/huggingface \
    -v ./models/torch:/root/.cache/torch \
    -v ./models/transformers:/root/.cache/transformers \
    any2markdown-mcp

# 等待容器启动
echo "⏳ 等待容器启动..."
sleep 10

# 检查容器状态
echo "🔍 检查容器状态..."
if docker ps | grep -q any2markdown; then
    echo "✅ 容器启动成功"
    
    # 检查日志中是否有权限错误
    echo "📋 检查权限错误..."
    if docker logs any2markdown 2>&1 | grep -i "permission denied"; then
        echo "❌ 发现权限错误:"
        docker logs any2markdown 2>&1 | grep -i "permission denied"
        exit 1
    else
        echo "✅ 未发现权限错误"
    fi
    
    # 检查缓存目录是否可访问
    echo "🗂️  测试缓存目录访问..."
    docker exec any2markdown ls -la /root/.cache/ || {
        echo "❌ 无法访问缓存目录"
        exit 1
    }
    
    echo "✅ 缓存目录访问正常"
    
else
    echo "❌ 容器启动失败"
    echo "📋 容器日志:"
    docker logs any2markdown
    exit 1
fi

# 清理测试容器
echo "🧹 清理测试容器..."
docker stop any2markdown
docker rm any2markdown

echo ""
echo "🎉 权限修复测试完成！"
echo "现在可以使用以下命令启动服务:"
echo "  直接 Docker: docker run -d -p 3000:3000 -v ./models/huggingface:/root/.cache/huggingface any2markdown-mcp"
echo "  Docker Compose: docker-compose up -d" 