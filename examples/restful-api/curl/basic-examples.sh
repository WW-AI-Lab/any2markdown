#!/bin/bash

# Any2Markdown RESTful API - 基础 cURL 示例
# 演示如何使用cURL命令行工具调用API

set -e

API_BASE="http://localhost:3000/api/v1"
SAMPLE_DIR="../../sample-files"

echo "🚀 Any2Markdown API 基础示例"
echo "================================"

# 检查服务状态
echo ""
echo "🔍 1. 检查服务状态"
echo "--------------------"
curl -s "${API_BASE}/status" | jq '.'

# 获取支持的格式
echo ""
echo "📋 2. 获取支持的格式"
echo "---------------------"
curl -s "${API_BASE}/formats" | jq '.data.supported_formats'

# 文件上传示例
echo ""
echo "📄 3. 文件上传转换示例"
echo "----------------------"

# PDF 文件上传示例
if [ -f "${SAMPLE_DIR}/sample.pdf" ]; then
    echo "📕 转换PDF文件..."
    curl -X POST "${API_BASE}/convert" \
        -F "file=@${SAMPLE_DIR}/sample.pdf" \
        -F "extract_images=true" \
        -F "include_content=false" \
        -F "output_format=markdown" \
        -F "start_page=0" \
        -F "end_page=2" | jq '.data.metadata'
else
    echo "⚠️  未找到示例PDF文件: ${SAMPLE_DIR}/sample.pdf"
fi

# Word 文件上传示例
if [ -f "${SAMPLE_DIR}/sample.docx" ]; then
    echo ""
    echo "📘 转换Word文件..."
    curl -X POST "${API_BASE}/convert" \
        -F "file=@${SAMPLE_DIR}/sample.docx" \
        -F "extract_images=true" \
        -F "include_content=false" \
        -F "preserve_formatting=true" | jq '.data.metadata'
else
    echo "⚠️  未找到示例Word文件: ${SAMPLE_DIR}/sample.docx"
fi

# Excel 文件上传示例
if [ -f "${SAMPLE_DIR}/sample.xlsx" ]; then
    echo ""
    echo "📗 转换Excel文件..."
    curl -X POST "${API_BASE}/convert" \
        -F "file=@${SAMPLE_DIR}/sample.xlsx" \
        -F "include_formulas=true" \
        -F "include_content=false" | jq '.data.metadata'
else
    echo "⚠️  未找到示例Excel文件: ${SAMPLE_DIR}/sample.xlsx"
fi

# 多文件上传示例
echo ""
echo "📚 4. 多文件批量转换示例"
echo "------------------------"

if [ -f "${SAMPLE_DIR}/sample.pdf" ] && [ -f "${SAMPLE_DIR}/sample.docx" ]; then
    echo "📦 批量转换多个文件..."
    curl -X POST "${API_BASE}/convert" \
        -F "file1=@${SAMPLE_DIR}/sample.pdf" \
        -F "file2=@${SAMPLE_DIR}/sample.docx" \
        -F "extract_images=true" \
        -F "include_content=false" \
        -F "output_format=markdown" | jq '.data | length'
else
    echo "⚠️  需要多个示例文件进行批量转换测试"
fi

echo ""
echo "✅ 基础示例完成！"
echo ""
echo "💡 提示:"
echo "   - 使用 jq 工具美化JSON输出"
echo "   - 设置 include_content=true 可获取完整转换内容"
echo "   - 查看高级示例: ./advanced-examples.sh" 