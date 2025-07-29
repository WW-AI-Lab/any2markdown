"""
模型管理器模块

负责加载和管理marker-pdf模型以及其他必要的机器学习模型
支持GPU/CPU自动检测和模型缓存
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import warnings
import time

import structlog
import torch
from huggingface_hub import snapshot_download

# 抑制一些不必要的警告
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

logger = structlog.get_logger(__name__)


class ModelManager:
    """模型管理器，负责加载和管理所有机器学习模型"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.device = self._detect_device()
        self.models: Dict[str, Any] = {}
        self.model_cache_dir = Path(config.get("model_cache_dir", "~/.cache/marker")).expanduser()
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化标志
        self._initialized = False
        self._initialization_lock = asyncio.Lock()
        
        # 设置模型下载相关的环境变量（确保进度显示）
        self._setup_model_env_vars()
        
        logger.info("ModelManager initialized", 
                   device=self.device, 
                   cache_dir=str(self.model_cache_dir),
                   progress_bars_enabled=not self._is_progress_disabled())
    
    def _setup_model_env_vars(self):
        """设置模型下载相关的环境变量"""
        # 确保显示下载进度条
        if self.config.get("hf_hub_disable_progress_bars", False):
            logger.warning("⚠️  Progress bars are disabled in config. Model download progress will not be visible!")
            os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "true"
        else:
            logger.info("✅ Model download progress bars are enabled")
            os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "false"
        
        # 设置其他环境变量
        env_vars = {
            "MODEL_CACHE_DIR": self.config.get("model_cache_dir", "~/.cache/marker"),
            "HF_HOME": self.config.get("hf_home", "~/.cache/huggingface"),
            "HF_HUB_CACHE": self.config.get("hf_hub_cache", "~/.cache/huggingface/hub"),
            "HF_ASSETS_CACHE": self.config.get("hf_assets_cache", "~/.cache/huggingface/assets"),
            "TORCH_HOME": self.config.get("torch_home", "~/.cache/torch"),
            "TRANSFORMERS_CACHE": self.config.get("transformers_cache", "~/.cache/transformers"),
            "HF_HUB_ENABLE_HF_TRANSFER": str(self.config.get("hf_hub_enable_hf_transfer", False)).lower(),
            "HF_HUB_DISABLE_TELEMETRY": str(self.config.get("hf_hub_disable_telemetry", True)).lower(),
        }
        
        for key, value in env_vars.items():
            # 展开用户目录路径
            if value.startswith("~"):
                expanded_value = str(Path(value).expanduser())
            else:
                expanded_value = value
            
            # 设置环境变量（即使已存在也要更新，确保使用配置中的值）
            os.environ[key] = expanded_value
            logger.debug("Set environment variable", var=key, value=expanded_value)
        
        # 确保缓存目录存在
        for key in ["HF_HOME", "HF_HUB_CACHE", "HF_ASSETS_CACHE", "TORCH_HOME", "TRANSFORMERS_CACHE", "MODEL_CACHE_DIR"]:
            cache_dir = Path(os.environ[key])
            cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug("Ensured cache directory exists", dir=str(cache_dir))
    
    def _is_progress_disabled(self) -> bool:
        """检查是否禁用了进度条"""
        return os.environ.get("HF_HUB_DISABLE_PROGRESS_BARS", "false").lower() == "true"
    
    def _detect_device(self) -> str:
        """自动检测最佳设备"""
        device_config = self.config.get("device", "auto").lower()
        
        if device_config == "cpu":
            return "cpu"
        elif device_config == "cuda" and torch.cuda.is_available():
            return "cuda"
        elif device_config == "mps" and torch.backends.mps.is_available():
            return "mps"
        elif device_config == "auto":
            # 自动检测最佳设备
            if torch.cuda.is_available():
                device = "cuda"
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0)
                logger.info("CUDA available", gpu_count=gpu_count, gpu_name=gpu_name)
                return device
            elif torch.backends.mps.is_available():
                logger.info("MPS (Apple Silicon) available")
                return "mps"
            else:
                logger.info("Using CPU (no GPU acceleration available)")
                return "cpu"
        else:
            logger.warning("Invalid device config, falling back to CPU", 
                         device_config=device_config)
            return "cpu"
    
    async def initialize(self) -> None:
        """异步初始化所有模型"""
        if self._initialized:
            return
            
        async with self._initialization_lock:
            if self._initialized:  # 双重检查
                return
                
            logger.info("🚀 Starting model initialization...")
            logger.info("📥 This may take some time for first run as models need to be downloaded...")
            
            start_time = time.time()
            
            try:
                # 初始化marker模型
                await self._initialize_marker_model()
                
                # 可以在这里添加其他模型的初始化
                # await self._initialize_other_models()
                
                self._initialized = True
                
                elapsed_time = time.time() - start_time
                logger.info("✅ All models initialized successfully", 
                          initialization_time=f"{elapsed_time:.2f}s")
                
            except Exception as e:
                elapsed_time = time.time() - start_time
                logger.error("❌ Failed to initialize models", 
                           error=str(e), 
                           elapsed_time=f"{elapsed_time:.2f}s")
                raise
    
    async def _initialize_marker_model(self) -> None:
        """初始化marker-pdf模型"""
        try:
            logger.info("📦 Loading marker-pdf models...")
            logger.info("ℹ️  If this is the first run, marker will download ~3-5GB of AI models")
            logger.info("📊 Download progress will be shown below:")
            
            # 导入marker模块（延迟导入以避免启动时的依赖问题）
            try:
                from marker.scripts.convert import process_single_pdf, create_model_dict
                logger.info("✅ Marker modules imported successfully")
            except ImportError as e:
                logger.error("❌ Failed to import marker modules", error=str(e))
                logger.error("💡 Please ensure marker-pdf is installed: pip install marker-pdf")
                raise
            
            # 在executor中运行模型加载（避免阻塞事件循环）
            loop = asyncio.get_event_loop()
            
            logger.info("🔄 Loading AI models (this may take several minutes)...")
            models = await loop.run_in_executor(
                None, 
                self._load_marker_models
            )
            
            self.models["marker"] = {
                "models": models,
                "convert_func": process_single_pdf
            }
            
            logger.info("✅ Marker models loaded successfully")
            
        except ImportError as e:
            logger.error("❌ Failed to import marker modules", error=str(e))
            raise
        except Exception as e:
            logger.error("❌ Failed to load marker models", error=str(e))
            raise
    
    def _load_marker_models(self) -> Any:
        """在线程池中加载marker模型"""
        try:
            from marker.scripts.convert import create_model_dict
            
            logger.info("🔧 Setting up model cache directories...")
            
            # 设置环境变量
            os.environ["TORCH_HOME"] = str(self.model_cache_dir)
            
            logger.info("🤖 Creating marker model dictionary...")
            logger.info("📡 Models will be downloaded to:", cache_dir=str(self.model_cache_dir))
            
            # 创建模型字典
            device = None if self.device == "auto" else self.device
            logger.info("🚀 Initializing models...", target_device=device or "auto")
            
            models = create_model_dict(device=device)
            
            logger.info("✅ Marker models created successfully")
            return models
            
        except Exception as e:
            logger.error("❌ Error in _load_marker_models", error=str(e))
            import traceback
            logger.error("🔍 Full traceback:", traceback=traceback.format_exc())
            raise
    
    async def get_marker_models(self) -> Dict[str, Any]:
        """获取marker模型"""
        await self.initialize()
        return self.models["marker"]["models"]
    
    async def convert_pdf_with_marker(self, pdf_path: str, **kwargs) -> tuple:
        """使用marker转换PDF"""
        await self.initialize()
        
        try:
            convert_func = self.models["marker"]["convert_func"]
            models = self.models["marker"]["models"]
            
            # 在executor中运行转换（避免阻塞事件循环）
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: convert_func(pdf_path, models, **kwargs)
            )
            
            return result
            
        except Exception as e:
            logger.error("PDF conversion failed", error=str(e), pdf_path=pdf_path)
            raise
    
    def get_device_info(self) -> Dict[str, Any]:
        """获取设备信息"""
        info = {
            "device": self.device,
            "torch_version": torch.__version__,
        }
        
        if self.device == "cuda":
            info.update({
                "cuda_available": torch.cuda.is_available(),
                "cuda_version": torch.version.cuda,
                "gpu_count": torch.cuda.device_count(),
                "gpu_names": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())],
                "current_device": torch.cuda.current_device(),
            })
        elif self.device == "mps":
            info.update({
                "mps_available": torch.backends.mps.is_available(),
            })
        
        return info
    
    async def cleanup(self) -> None:
        """清理资源"""
        logger.info("Cleaning up model manager...")
        
        # 清理GPU缓存
        if self.device == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # 清理模型引用
        self.models.clear()
        self._initialized = False
        
        logger.info("Model manager cleanup completed")
    
    def __del__(self):
        """析构函数"""
        if hasattr(self, 'models') and self.models:
            # 注意：在析构函数中不能使用async
            if self.device == "cuda" and torch.cuda.is_available():
                torch.cuda.empty_cache() 