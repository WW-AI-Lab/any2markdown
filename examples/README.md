# Any2Markdown 示例代码和教程

本目录包含了Any2Markdown MCP Server的各种使用示例和教程。

## 📁 目录结构

```
examples/
├── README.md                    # 本文件
├── 🌐 restful-api/              # RESTful API 示例
│   ├── python/                  # Python 客户端示例
│   ├── javascript/              # JavaScript 客户端示例
│   ├── curl/                    # cURL 命令示例
│   └── postman/                 # Postman 集合
├── 🔧 mcp-protocol/             # MCP 协议示例
│   ├── python-client/           # Python MCP 客户端
│   ├── claude-integration/      # Claude Desktop 集成
│   └── vscode-extension/        # VS Code 扩展示例
├── 🚀 deployment/               # 部署示例
│   ├── docker/                  # Docker 部署
│   ├── kubernetes/              # Kubernetes 部署
│   └── cloud/                   # 云平台部署
└── 📚 tutorials/                # 教程文档
    ├── getting-started.md       # 快速入门
    ├── advanced-usage.md        # 高级用法
    └── troubleshooting.md       # 故障排除
```

## 🚀 快速开始

### 1. RESTful API 示例

最简单的方式是使用RESTful API：

```bash
# 进入API示例目录
cd restful-api/curl

# 运行基础示例
./basic-examples.sh

# 运行高级示例
./advanced-examples.sh
```

### 2. MCP 协议示例

如果你想使用MCP协议：

```bash
# 进入MCP示例目录
cd mcp-protocol/python-client

# 安装依赖
pip install -r requirements.txt

# 运行示例
python basic_client.py
```

### 3. 部署示例

快速部署服务器：

```bash
# Docker 部署
cd deployment/docker
docker-compose up -d

# Kubernetes 部署
cd deployment/kubernetes
kubectl apply -f any2markdown-deployment.yaml
```

## 📖 教程指南

1. **[快速入门](tutorials/getting-started.md)** - 5分钟上手指南
2. **[高级用法](tutorials/advanced-usage.md)** - 深入功能探索
3. **[故障排除](tutorials/troubleshooting.md)** - 常见问题解决

## 🛠️ 示例说明

### RESTful API 示例

- **Python 客户端**: 使用 `requests` 库的完整示例
- **JavaScript 客户端**: 浏览器和Node.js环境示例
- **cURL 命令**: 各种场景的命令行示例
- **Postman 集合**: 可直接导入的API测试集合

### MCP 协议示例

- **Python 客户端**: 使用官方 `mcp` 库的示例
- **Claude 集成**: 在Claude Desktop中使用的配置
- **VS Code 扩展**: 编辑器集成示例

### 部署示例

- **Docker**: 单容器和多容器部署
- **Kubernetes**: 生产级别的K8s部署
- **云平台**: AWS、Azure、GCP部署指南

## 🤝 贡献示例

欢迎贡献更多示例！请遵循以下指南：

1. 在相应目录下创建示例
2. 包含完整的README说明
3. 提供依赖安装说明
4. 包含预期输出示例
5. 添加错误处理和注释

## 📞 获取帮助

如果在使用示例时遇到问题：

1. 查看 [故障排除指南](tutorials/troubleshooting.md)
2. 检查 [主项目文档](../docs/)
3. 提交 [GitHub Issue](https://github.com/WW-AI-Lab/any2markdown/issues) 