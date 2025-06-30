"""
文档处理器基类

定义所有文档处理器的通用接口和功能
"""

import asyncio
import base64
import hashlib
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import uuid

import structlog
from PIL import Image

logger = structlog.get_logger(__name__)


class BaseProcessor(ABC):
    """文档处理器基类"""
    
    def __init__(self, config):
        self.config = config
        
        # 处理Config对象或字典
        if hasattr(config, 'temp_image_dir'):
            # Config对象
            self.temp_image_dir = Path(config.temp_image_dir).resolve()
            self.supported_image_formats = getattr(config, 'supported_image_formats', ["png", "jpg", "jpeg", "gif", "bmp", "webp"])
            self.image_max_size = getattr(config, 'image_max_size', 10 * 1024 * 1024)
            self.image_quality = getattr(config, 'image_quality', 85)
            self.host = getattr(config, 'host', 'localhost')
            self.port = getattr(config, 'port', 3000)
        else:
            # 字典
            self.temp_image_dir = Path(config.get("temp_image_dir", "./temp_images")).resolve()
            self.supported_image_formats = config.get("supported_image_formats", ["png", "jpg", "jpeg", "gif", "bmp", "webp"])
            self.image_max_size = config.get("image_max_size", 10 * 1024 * 1024)
            self.image_quality = config.get("image_quality", 85)
            self.host = config.get("host", "localhost")
            self.port = config.get("port", 3000)
        
        self.temp_image_dir.mkdir(parents=True, exist_ok=True)
        self.server_base_url = f"http://{self.host}:{self.port}"
        
        # 为这个处理器实例生成唯一标识符，用于避免文件名冲突
        import time
        import random
        import string
        timestamp = int(time.time())
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        self.instance_id = f"{timestamp}_{random_suffix}"
        
        logger.info(f"{self.__class__.__name__} initialized", 
                   temp_image_dir=str(self.temp_image_dir),
                   server_base_url=self.server_base_url,
                   instance_id=self.instance_id)
    
    def _get_config_value(self, key: str, default=None):
        """获取配置值的helper方法，支持Config对象和字典"""
        if hasattr(self.config, key):
            return getattr(self.config, key, default)
        elif hasattr(self.config, 'get'):
            return self.config.get(key, default)
        else:
            return default
    
    @abstractmethod
    async def convert(self, file_content: bytes, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换文档的抽象方法
        
        Args:
            file_content: 文档内容（bytes）
            options: 转换选项
            
        Returns:
            转换结果字典
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式"""
        pass
    
    def decode_base64_content(self, base64_content: str) -> bytes:
        """解码Base64内容"""
        try:
            # 确保输入是字符串
            if not isinstance(base64_content, str):
                raise ValueError(f"Expected string, got {type(base64_content)}")
            
            # 移除可能的数据URI前缀
            if base64_content.startswith('data:'):
                base64_content = base64_content.split(',', 1)[1]
            
            return base64.b64decode(base64_content)
        except Exception as e:
            logger.error("Failed to decode base64 content", error=str(e))
            raise ValueError(f"Invalid base64 content: {e}")
    
    def process_file_content_input(self, file_content: str, filename: Optional[str] = None) -> bytes:
        """
        处理多种文件内容输入方式
        
        Args:
            file_content: 文件内容，可以是：
                1. Base64编码的内容
                2. 以'file://'开头的文件路径
                3. 原始二进制内容（如果是字符串则尝试编码）
            filename: 可选的文件名，用于推断处理方式
            
        Returns:
            处理后的文件内容（bytes）
        """
        try:
            # 方式1: 文件路径
            if isinstance(file_content, str) and file_content.startswith('file://'):
                file_path = file_content[7:]  # 移除 'file://' 前缀
                path = Path(file_path)
                
                if not path.exists():
                    raise ValueError(f"File not found: {file_path}")
                
                if not path.is_file():
                    raise ValueError(f"Path is not a file: {file_path}")
                
                # 检查文件大小
                file_size = path.stat().st_size
                max_size = self._get_config_value("max_file_size", 100 * 1024 * 1024)  # 100MB
                if file_size > max_size:
                    raise ValueError(f"File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)")
                
                with open(path, 'rb') as f:
                    content = f.read()
                
                logger.info("File loaded from path", path=file_path, size=len(content))
                return content
            
            # 方式2: Base64编码内容
            # 尝试检测是否为Base64编码
            if isinstance(file_content, str) and self._is_base64_content(file_content):
                content = self.decode_base64_content(file_content)
                logger.info("File content decoded from base64", size=len(content))
                return content
            
            # 方式3: 原始内容（作为最后的尝试）
            # 如果是字符串，尝试编码为bytes
            if isinstance(file_content, str):
                # 尝试不同的编码方式
                for encoding in ['utf-8', 'latin1', 'cp1252']:
                    try:
                        content = file_content.encode(encoding)
                        logger.warning("File content processed as raw string", 
                                     encoding=encoding, size=len(content))
                        return content
                    except UnicodeEncodeError:
                        continue
                
                raise ValueError("Unable to process file content as raw string")
            
            # 如果已经是bytes，直接返回
            if isinstance(file_content, bytes):
                logger.info("File content processed as raw bytes", size=len(file_content))
                return file_content
            
            raise ValueError(f"Unsupported file content type: {type(file_content)}")
            
        except Exception as e:
            logger.error("Failed to process file content input", 
                        content_type=type(file_content).__name__,
                        content_preview=str(file_content)[:100] if isinstance(file_content, str) else "binary",
                        error=str(e))
            raise ValueError(f"Failed to process file content: {e}")
    
    def _is_base64_content(self, content: str) -> bool:
        """
        检测内容是否为Base64编码
        
        Args:
            content: 要检测的内容
            
        Returns:
            如果内容看起来像Base64编码则返回True
        """
        try:
            # 确保输入是字符串
            if not isinstance(content, str):
                return False
            
            # 移除可能的数据URI前缀
            if content.startswith('data:'):
                content = content.split(',', 1)[1]
            
            # 基本的Base64检查
            if not content:
                return False
            
            # Base64字符集检查
            import re
            if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', content.strip()):
                return False
            
            # 长度检查（Base64编码的长度应该是4的倍数）
            if len(content.strip()) % 4 != 0:
                return False
            
            # 尝试解码
            base64.b64decode(content.strip())
            return True
            
        except Exception:
            return False
    
    def validate_file_size(self, content: bytes, max_size: Optional[int] = None) -> None:
        """验证文件大小"""
        if max_size is None:
            max_size = self._get_config_value("max_file_size", 100 * 1024 * 1024)  # 100MB
        
        if len(content) > max_size:
            raise ValueError(f"File size ({len(content)} bytes) exceeds maximum allowed size ({max_size} bytes)")
    
    async def save_temp_file(self, content: bytes, suffix: str = "") -> Path:
        """保存临时文件"""
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=suffix,
            dir=self.temp_image_dir.parent
        )
        
        try:
            temp_file.write(content)
            temp_file.flush()
            return Path(temp_file.name)
        finally:
            temp_file.close()
    
    async def save_image(self, image_data: bytes, filename: Optional[str] = None) -> Dict[str, str]:
        """
        保存图片到临时目录并返回访问信息
        
        Args:
            image_data: 图片数据
            filename: 可选的文件名
            
        Returns:
            包含文件路径和URL的字典
        """
        try:
            # 验证输入
            if not image_data or len(image_data) == 0:
                raise ValueError("图片数据为空")
            
            # 验证图片大小
            if len(image_data) > self.image_max_size:
                logger.warning("Image size exceeds limit", 
                             size=len(image_data), 
                             limit=self.image_max_size)
                # 可以选择压缩图片或跳过
                image_data = await self._compress_image(image_data)
            
            # 生成唯一文件名
            if filename is None:
                # 使用内容哈希生成文件名
                hash_obj = hashlib.md5(image_data)
                filename = f"{hash_obj.hexdigest()}.png"
            
            # 确保文件名是安全的
            filename = self._sanitize_filename(filename)
            
            # 确保临时目录存在
            self.temp_image_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存图片
            image_path = self.temp_image_dir / filename
            
            logger.info("准备保存图片", 
                       path=str(image_path),
                       data_size=len(image_data),
                       temp_dir=str(self.temp_image_dir),
                       temp_dir_exists=self.temp_image_dir.exists())
            
            # 写入文件
            try:
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                
                # 验证文件是否真正写入
                if not image_path.exists():
                    raise IOError(f"文件写入后不存在: {image_path}")
                
                # 验证文件大小
                actual_size = image_path.stat().st_size
                if actual_size != len(image_data):
                    raise IOError(f"文件大小不匹配: 期望 {len(image_data)}, 实际 {actual_size}")
                
                logger.info("文件写入验证成功", 
                           path=str(image_path),
                           expected_size=len(image_data),
                           actual_size=actual_size)
                
            except Exception as write_error:
                logger.error("文件写入失败", 
                           path=str(image_path),
                           error=str(write_error),
                           error_type=type(write_error).__name__)
                raise
            
            # 使用服务器基础URL生成完整的图片访问URL
            image_url = f"{self.server_base_url}/static/{filename}"
            
            result = {
                "filename": filename,
                "path": str(image_path),
                "url": image_url,
                "size": len(image_data)
            }
            
            logger.info("图片保存成功", 
                       path=str(image_path), 
                       url=image_url, 
                       size=len(image_data),
                       file_exists=image_path.exists())
            
            return result
            
        except Exception as e:
            logger.error("Failed to save image", 
                        error=str(e),
                        error_type=type(e).__name__,
                        filename=filename,
                        data_size=len(image_data) if image_data else 0)
            import traceback
            logger.debug("图片保存异常详情", traceback=traceback.format_exc())
            raise
    
    async def _compress_image(self, image_data: bytes) -> bytes:
        """压缩图片"""
        try:
            from PIL import Image
            import io
            
            # 打开图片
            img = Image.open(io.BytesIO(image_data))
            
            # 转换为RGB（如果需要）
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # 压缩图片
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=self.image_quality, optimize=True)
            
            compressed_data = output.getvalue()
            
            logger.info("Image compressed", 
                       original_size=len(image_data),
                       compressed_size=len(compressed_data),
                       compression_ratio=len(compressed_data)/len(image_data))
            
            return compressed_data
            
        except Exception as e:
            logger.error("Failed to compress image", error=str(e))
            # 如果压缩失败，返回原始数据
            return image_data
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，确保安全"""
        import re
        
        # 移除或替换危险字符
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        
        # 确保文件名不为空
        if not filename or filename == '.':
            filename = f"image_{uuid.uuid4().hex[:8]}.png"
        
        # 限制文件名长度
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, 'png')
            filename = f"{name[:240]}.{ext}"
        
        return filename
    
    def remove_header_footer_text(self, text: str, options: Dict[str, Any]) -> str:
        """
        移除页眉页脚文本的通用方法
        
        Args:
            text: 原始文本
            options: 处理选项
            
        Returns:
            处理后的文本
        """
        if not options.get("remove_header_footer", True):
            return text
        
        lines = text.split('\n')
        cleaned_lines = []
        
        # 简单的页眉页脚检测逻辑
        # 这里可以根据具体需求进行改进
        for line in lines:
            line = line.strip()
            
            # 跳过可能的页眉页脚内容
            if self._is_likely_header_footer(line):
                logger.debug("Removing likely header/footer", line=line)
                continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _is_likely_header_footer(self, line: str) -> bool:
        """判断是否可能是页眉页脚内容"""
        line = line.strip()
        
        # 空行
        if not line:
            return False
        
        # 常见的页眉页脚模式
        header_footer_patterns = [
            r'^\d+$',  # 纯数字（页码）
            r'^第\s*\d+\s*页',  # 中文页码
            r'^Page\s+\d+',  # 英文页码
            r'^\d+\s*/\s*\d+$',  # 页码格式 1/10
            r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}',  # 日期格式
            r'^Copyright\s+',  # 版权信息
            r'^©\s*\d{4}',  # 版权符号
        ]
        
        import re
        for pattern in header_footer_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return True
        
        # 检查是否是重复出现的短文本（可能是页眉页脚）
        if len(line) < 50 and line.count(' ') < 5:
            # 这里可以添加更复杂的逻辑来检测重复文本
            pass
        
        return False
    
    def format_output(self, content, metadata: Dict[str, Any], 
                     output_format: str = "markdown") -> Dict[str, Any]:
        """格式化输出结果"""
        # 处理分页内容（列表格式）
        if isinstance(content, list):
            # 将分页内容合并为单一字符串
            if all(isinstance(page, dict) and 'content' in page for page in content):
                # 如果是分页格式，合并所有页面的内容
                markdown_content = "\n\n---\n\n".join([page['content'] for page in content])
                # 保留分页信息在元数据中
                metadata['pages'] = content
                metadata['page_count'] = len(content)
            else:
                # 如果是其他格式的列表，转换为字符串
                markdown_content = str(content)
        else:
            markdown_content = str(content)
        
        result = {
            "content": markdown_content,
            "metadata": metadata,
            "format": output_format
        }
        
        if output_format == "html":
            # 转换为HTML
            result["content"] = self._markdown_to_html(markdown_content)
        elif output_format == "json":
            # 结构化JSON输出
            result = {
                "success": True,
                "data": {
                    "content": markdown_content,
                    "metadata": metadata
                },
                "format": output_format
            }
        
        return result
    
    def _markdown_to_html(self, markdown_content: str) -> str:
        """将Markdown转换为HTML"""
        try:
            import markdown
            html = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code'])
            return html
        except ImportError:
            logger.warning("markdown package not available, returning raw content")
            return f"<pre>{markdown_content}</pre>"
    
    async def cleanup_temp_files(self, file_paths: List[str]) -> None:
        """清理临时文件"""
        for file_path in file_paths:
            try:
                path = Path(file_path)
                if path.exists():
                    path.unlink()
                    logger.debug("Temp file cleaned up", path=str(path))
            except Exception as e:
                logger.warning("Failed to cleanup temp file", 
                             path=file_path, error=str(e)) 