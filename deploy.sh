#!/bin/bash

# Any2Markdown MCP Server 部署脚本

set -e

echo "🚀 Any2Markdown MCP Server 部署脚本"
echo "=================================="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 检查.env文件
if [ ! -f .env ]; then
    echo "📝 创建.env配置文件..."
    cp env.example .env
    echo "✅ 已创建.env文件，请根据需要修改配置"
else
    echo "✅ 找到.env配置文件"
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p logs temp_images

# 询问部署类型
echo ""
echo "请选择部署类型:"
echo "1) CPU版本 (默认)"
echo "2) GPU版本 (需要NVIDIA GPU和nvidia-docker)"
echo "3) 开发模式 (直接运行Python)"
echo ""
read -p "请输入选择 [1]: " deploy_type
deploy_type=${deploy_type:-1}

case $deploy_type in
    1)
        echo "🔧 部署CPU版本..."
        docker-compose up -d any2markdown-mcp
        ;;
    2)
        echo "🔧 部署GPU版本..."
        # 检查nvidia-docker
        if ! docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi &> /dev/null; then
            echo "❌ GPU支持未正确配置，请安装nvidia-docker"
            exit 1
        fi
        docker-compose --profile gpu up -d any2markdown-mcp-gpu
        ;;
    3)
        echo "🔧 开发模式启动..."
        # 检查Python环境
        if ! command -v python3 &> /dev/null; then
            echo "❌ Python3未安装"
            exit 1
        fi
        
        # 安装依赖
        echo "📦 安装Python依赖..."
        pip install -r requirements.txt
        
        # 运行测试
        echo "🧪 运行测试..."
        python test_server.py
        
        # 启动服务器
        echo "🚀 启动开发服务器..."
        python run_server.py
        exit 0
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
if [ $deploy_type -eq 1 ]; then
    port=8080
else
    port=8081
fi

if curl -f http://localhost:$port/health &> /dev/null; then
    echo "✅ 服务启动成功！"
    echo "🌐 服务地址: http://localhost:$port"
    echo "📊 查看状态: docker-compose ps"
    echo "📝 查看日志: docker-compose logs -f"
else
    echo "❌ 服务启动失败，请检查日志:"
    docker-compose logs
    exit 1
fi

echo ""
echo "🎉 部署完成！"
echo ""
echo "常用命令:"
echo "  查看状态: docker-compose ps"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "" 