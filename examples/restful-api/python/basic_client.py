#!/usr/bin/env python3
"""
Any2Markdown RESTful API Python 客户端示例

演示如何使用Python requests库调用Any2Markdown API
"""

import requests
import base64
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class Any2MarkdownClient:
    """Any2Markdown API 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api/v1"
    
    def convert_file_upload(self, 
                           file_path: str, 
                           **options) -> Dict[str, Any]:
        """
        使用文件上传方式转换文档
        
        Args:
            file_path: 文档文件路径
            **options: 转换选项
        
        Returns:
            API响应数据
        """
        url = f"{self.api_base}/convert"
        
        # 准备文件
        files = {'file': open(file_path, 'rb')}
        
        # 准备表单数据
        data = {}
        for key, value in options.items():
            if isinstance(value, bool):
                data[key] = 'true' if value else 'false'
            elif isinstance(value, list):
                data[key] = ','.join(map(str, value))
            else:
                data[key] = str(value)
        
        try:
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
            return response.json()
        finally:
            files['file'].close()
    
    def convert_base64(self, 
                      file_path: str, 
                      filename: Optional[str] = None,
                      **options) -> Dict[str, Any]:
        """
        使用base64编码方式转换文档
        
        Args:
            file_path: 文档文件路径
            filename: 文件名（用于类型检测）
            **options: 转换选项
        
        Returns:
            API响应数据
        """
        url = f"{self.api_base}/convert"
        
        # 读取并编码文件
        with open(file_path, 'rb') as f:
            file_content = base64.b64encode(f.read()).decode('utf-8')
        
        # 准备请求数据
        if filename is None:
            filename = os.path.basename(file_path)
        
        payload = {
            "files": [{
                "filename": filename,
                "file_content": file_content,
                "options": options
            }]
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        url = f"{self.api_base}/status"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_supported_formats(self) -> Dict[str, Any]:
        """获取支持的格式"""
        url = f"{self.api_base}/formats"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

def main():
    """示例用法"""
    client = Any2MarkdownClient()
    
    # 检查服务状态
    print("🔍 检查服务状态...")
    try:
        status = client.get_status()
        print(f"✅ 服务状态: {status['data']['status']}")
        print(f"📊 系统信息: CPU {status['data']['system_info']['cpu_usage']}%, "
              f"内存 {status['data']['system_info']['memory_usage']}%")
    except Exception as e:
        print(f"❌ 服务连接失败: {e}")
        return
    
    # 示例文件路径（请替换为实际文件）
    test_files = [
        "sample.pdf",
        "sample.docx", 
        "sample.xlsx"
    ]
    
    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"⚠️  跳过不存在的文件: {file_path}")
            continue
        
        print(f"\n📄 转换文件: {file_path}")
        
        try:
            # 方式1: 文件上传
            print("  🔄 使用文件上传方式...")
            result1 = client.convert_file_upload(
                file_path,
                extract_images=True,
                include_content=False,  # 只获取元数据，不获取内容
                output_format="markdown"
            )
            
            if result1.get('success'):
                metadata = result1['data']['metadata']
                print(f"  ✅ 转换成功!")
                print(f"     - 文件类型: {metadata['source_type']}")
                print(f"     - 处理时间: {metadata['processing_time']:.2f}秒")
                if 'total_pages' in metadata:
                    print(f"     - 总页数: {metadata['total_pages']}")
                if 'images_extracted' in metadata:
                    print(f"     - 提取图片: {metadata['images_extracted']}张")
            else:
                print(f"  ❌ 转换失败: {result1.get('message', '未知错误')}")
            
            # 方式2: Base64编码（仅对小文件演示）
            file_size = os.path.getsize(file_path)
            if file_size < 1024 * 1024:  # 小于1MB
                print("  🔄 使用Base64编码方式...")
                result2 = client.convert_base64(
                    file_path,
                    extract_images=True,
                    include_content=True,  # 获取完整内容
                    output_format="markdown"
                )
                
                if result2.get('success'):
                    content_length = len(result2['data'].get('markdown_content', ''))
                    print(f"  ✅ Base64转换成功! 内容长度: {content_length}字符")
                else:
                    print(f"  ❌ Base64转换失败: {result2.get('message', '未知错误')}")
            else:
                print(f"  ⚠️  文件过大({file_size/1024/1024:.1f}MB)，跳过Base64方式")
                
        except Exception as e:
            print(f"  ❌ 转换过程出错: {e}")
    
    # 获取支持的格式
    print(f"\n📋 支持的格式:")
    try:
        formats = client.get_supported_formats()
        for fmt in formats['data']['supported_formats']:
            print(f"  - {fmt}")
    except Exception as e:
        print(f"❌ 获取格式列表失败: {e}")

if __name__ == "__main__":
    main() 