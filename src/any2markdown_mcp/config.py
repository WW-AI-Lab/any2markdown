"""
配置管理模块

管理Any2Markdown MCP Server的所有配置选项
支持环境变量和默认值
"""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """应用配置类"""
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器主机地址")
    port: int = Field(default=3000, description="服务器端口")
    mcp_path: str = Field(default="/mcp", description="MCP服务路径")
    debug: bool = Field(default=False, description="调试模式")
    
    # 并发控制
    max_concurrent_jobs: int = Field(default=5, description="最大并发处理任务数")
    
    # 文件处理配置
    max_file_size: int = Field(default=100 * 1024 * 1024, description="最大文件大小(字节)")
    temp_image_dir: str = Field(default="./temp_images", description="临时图片存储目录")
    
    # 模型配置
    model_cache_dir: str = Field(default="~/.cache/marker", description="Marker模型缓存目录")
    device: str = Field(default="auto", description="计算设备 (cpu/cuda/mps/auto)")
    
    # Hugging Face模型缓存配置
    hf_home: str = Field(default="~/.cache/huggingface", description="Hugging Face缓存根目录")
    hf_hub_cache: str = Field(default="~/.cache/huggingface/hub", description="模型仓库缓存目录")
    hf_assets_cache: str = Field(default="~/.cache/huggingface/assets", description="资产缓存目录")
    torch_home: str = Field(default="~/.cache/torch", description="PyTorch模型缓存目录")
    transformers_cache: str = Field(default="~/.cache/transformers", description="Transformers库缓存目录")
    
    # 模型下载配置
    hf_hub_enable_hf_transfer: bool = Field(default=False, description="使用hf_transfer加速下载")
    hf_hub_disable_progress_bars: bool = Field(default=False, description="禁用下载进度条")
    hf_hub_disable_telemetry: bool = Field(default=True, description="禁用使用遥测")
    model_download_timeout: int = Field(default=300, description="模型下载超时时间(秒)")
    model_retry_attempts: int = Field(default=3, description="模型下载重试次数")
    
    # PDF处理配置
    pdf_languages: str = Field(default="en", description="PDF OCR默认语言")
    pdf_force_ocr: bool = Field(default=False, description="是否强制OCR")
    pdf_max_pages: int = Field(default=1000, description="PDF最大页数限制")
    
    # Word处理配置
    word_preserve_formatting: bool = Field(default=True, description="是否保持Word格式")
    word_extract_images: bool = Field(default=True, description="是否提取Word图片")
    
    # Excel处理配置
    excel_max_rows: int = Field(default=10000, description="Excel最大行数限制")
    excel_max_sheets: int = Field(default=20, description="Excel最大工作表数限制")
    
    # 图片处理配置
    image_max_size: int = Field(default=10 * 1024 * 1024, description="单个图片最大大小")
    image_formats: List[str] = Field(default=["png", "jpg", "jpeg", "gif", "bmp"], description="支持的图片格式")
    image_quality: int = Field(default=85, description="图片压缩质量")
    
    # 页眉页脚处理配置
    header_footer_threshold: float = Field(default=0.15, description="页眉页脚区域阈值(页面高度百分比)")
    header_footer_min_pages: int = Field(default=3, description="检测页眉页脚的最小页数")
    
    # 缓存配置
    enable_cache: bool = Field(default=True, description="是否启用缓存")
    cache_ttl: int = Field(default=3600, description="缓存TTL(秒)")
    
    # 日志配置
    log_level: str = Field(default="DEBUG", description="日志级别")
    log_file: Optional[str] = Field(default="logs/server.log", description="日志文件路径")
    
    # 安全配置
    allowed_file_types: List[str] = Field(
        default=["pdf", "docx", "doc", "xlsx", "xls"], 
        description="允许的文件类型"
    )
    
    # 清理配置
    cleanup_interval: int = Field(default=3600, description="临时文件清理间隔(秒)")
    cleanup_max_age: int = Field(default=24 * 3600, description="临时文件最大保留时间(秒)")
    
    class Config:
        """Pydantic配置"""
        env_prefix = "ANY2MD_"
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        """初始化配置"""
        super().__init__(**kwargs)
        
        # 展开用户目录路径
        cache_dirs = [
            'model_cache_dir', 'hf_home', 'hf_hub_cache', 
            'hf_assets_cache', 'torch_home', 'transformers_cache'
        ]
        
        for cache_dir_attr in cache_dirs:
            cache_dir_value = getattr(self, cache_dir_attr)
            if cache_dir_value.startswith("~"):
                setattr(self, cache_dir_attr, str(Path(cache_dir_value).expanduser()))
        
        # 确保目录存在
        Path(self.model_cache_dir).mkdir(parents=True, exist_ok=True)
        Path(self.hf_home).mkdir(parents=True, exist_ok=True)
        Path(self.hf_hub_cache).mkdir(parents=True, exist_ok=True)
        Path(self.hf_assets_cache).mkdir(parents=True, exist_ok=True)
        Path(self.torch_home).mkdir(parents=True, exist_ok=True)
        Path(self.transformers_cache).mkdir(parents=True, exist_ok=True)
        Path(self.temp_image_dir).mkdir(parents=True, exist_ok=True)
        if self.log_file:
            Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # 设置环境变量，确保模型库能正确使用缓存目录
        self._set_model_cache_env_vars()
    
    @property
    def base_url(self) -> str:
        """获取服务器基础URL"""
        return f"http://{self.host}:{self.port}"
    
    @property
    def static_url_prefix(self) -> str:
        """获取静态文件URL前缀"""
        return f"{self.base_url}/static"
    
    def get_model_cache_path(self, model_name: str) -> Path:
        """获取模型缓存路径"""
        return Path(self.model_cache_dir) / model_name
    
    def get_temp_image_path(self, session_id: str) -> Path:
        """获取临时图片路径"""
        path = Path(self.temp_image_dir) / session_id
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def is_file_type_allowed(self, filename: str) -> bool:
        """检查文件类型是否被允许"""
        if not filename:
            return False
        
        extension = Path(filename).suffix.lower().lstrip('.')
        return extension in self.allowed_file_types
    
    def get_device(self) -> str:
        """获取计算设备"""
        if self.device == "auto":
            # 自动检测设备
            try:
                import torch
                if torch.cuda.is_available():
                    return "cuda"
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    return "mps"
                else:
                    return "cpu"
            except ImportError:
                return "cpu"
        return self.device
    
    def validate_file_size(self, file_size: int) -> bool:
        """验证文件大小"""
        return file_size <= self.max_file_size
    
    def validate_image_size(self, image_size: int) -> bool:
        """验证图片大小"""
        return image_size <= self.image_max_size
    
    def _set_model_cache_env_vars(self):
        """设置模型缓存相关的环境变量"""
        env_mappings = {
            'HF_HOME': self.hf_home,
            'HF_HUB_CACHE': self.hf_hub_cache,
            'HF_ASSETS_CACHE': self.hf_assets_cache,
            'TORCH_HOME': self.torch_home,
            'TRANSFORMERS_CACHE': self.transformers_cache,
            'HF_HUB_ENABLE_HF_TRANSFER': str(self.hf_hub_enable_hf_transfer).lower(),
            'HF_HUB_DISABLE_PROGRESS_BARS': str(self.hf_hub_disable_progress_bars).lower(),
            'HF_HUB_DISABLE_TELEMETRY': str(self.hf_hub_disable_telemetry).lower(),
        }
        
        for env_var, value in env_mappings.items():
            # 只有当环境变量未设置时才设置，避免覆盖用户自定义设置
            if env_var not in os.environ:
                os.environ[env_var] = value
    
    def get_all_cache_dirs(self) -> dict:
        """获取所有缓存目录的配置"""
        return {
            'marker_cache': self.model_cache_dir,
            'hf_home': self.hf_home,
            'hf_hub_cache': self.hf_hub_cache,
            'hf_assets_cache': self.hf_assets_cache,
            'torch_home': self.torch_home,
            'transformers_cache': self.transformers_cache,
            'temp_images': self.temp_image_dir,
        }

# 创建一个全局的配置实例，供其他模块使用
settings = Config() 