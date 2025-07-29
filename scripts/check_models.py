#!/usr/bin/env python3
"""
模型状态检查和下载工具
用于检查模型是否已下载完成，以及触发模型下载
"""

import os
import sys
import time
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def print_info(msg):
    print(f"\033[0;34m[INFO]\033[0m {msg}")

def print_success(msg):
    print(f"\033[0;32m[SUCCESS]\033[0m {msg}")

def print_error(msg):
    print(f"\033[0;31m[ERROR]\033[0m {msg}")

def print_progress(msg):
    print(f"\033[0;36m[PROGRESS]\033[0m {msg}")

def print_warning(msg):
    print(f"\033[1;33m[WARNING]\033[0m {msg}")

def check_model_files():
    """检查模型文件是否存在"""
    model_dirs = [
        os.environ.get("MODEL_CACHE_DIR", "~/.cache/marker"),
        os.environ.get("HF_HOME", "~/.cache/huggingface"),
        os.environ.get("TORCH_HOME", "~/.cache/torch"),
        os.environ.get("TRANSFORMERS_CACHE", "~/.cache/transformers"),
    ]
    
    print_info("🔍 检查模型文件...")
    all_exist = True
    
    for model_dir in model_dirs:
        expanded_dir = Path(model_dir).expanduser()
        if expanded_dir.exists() and any(expanded_dir.iterdir()):
            print_success(f"✅ 发现模型文件: {expanded_dir}")
        else:
            print_info(f"❌ 模型目录为空或不存在: {expanded_dir}")
            all_exist = False
    
    return all_exist

def show_download_warning():
    """显示下载前的友好提醒"""
    print()
    print("=" * 60)
    print_warning("⚠️  重要提醒：AI模型下载即将开始")
    print("=" * 60)
    print_info("📥 即将下载约 3-5GB 的AI模型文件")
    print_info("⏱️  预计需要 5-15分钟 （取决于网络速度）")
    print_info("🌐 需要访问 Hugging Face Hub (huggingface.co)")
    print_info("💾 请确保有足够的磁盘空间 (至少10GB)")
    print_info("📊 下载过程中会显示实时进度")
    print()
    print_warning("⏳ 请耐心等待，不要中断下载过程...")
    print_warning("💡 如果网络不稳定，下载失败后可以重新运行此脚本")
    print("=" * 60)
    print()
    
    # 给用户5秒钟阅读提醒
    for i in range(5, 0, -1):
        print(f"\r⏰ 下载将在 {i} 秒后开始...", end="", flush=True)
        time.sleep(1)
    print("\r🚀 开始下载模型...                    ")
    print()

async def download_models():
    """下载模型"""
    try:
        print_info("🚀 开始初始化模型管理器...")
        
        # 显示友好的下载前提醒
        show_download_warning()
        
        # 尝试导入模型管理器
        try:
            from any2markdown_mcp.models.model_manager import ModelManager
            from any2markdown_mcp.config import settings
        except ImportError as e:
            print_error(f"❌ 导入模块失败: {e}")
            print_error("💡 请确保已正确安装所有依赖:")
            print_error("   pip install -r requirements.txt")
            return False
        
        # 🔧 在创建模型管理器之前，先确保所有环境变量都正确设置
        print_progress("🔧 设置模型缓存环境变量...")
        
        # 设置模型缓存相关的环境变量
        env_mappings = {
            'MODEL_CACHE_DIR': settings.model_cache_dir,
            'HF_HOME': settings.hf_home,
            'HF_HUB_CACHE': settings.hf_hub_cache,
            'HF_ASSETS_CACHE': settings.hf_assets_cache,
            'TORCH_HOME': settings.torch_home,
            'TRANSFORMERS_CACHE': settings.transformers_cache,
            'HF_HUB_ENABLE_HF_TRANSFER': str(settings.hf_hub_enable_hf_transfer).lower(),
            'HF_HUB_DISABLE_PROGRESS_BARS': 'false',  # 确保显示进度
            'HF_HUB_DISABLE_TELEMETRY': str(settings.hf_hub_disable_telemetry).lower(),
        }
        
        for env_var, value in env_mappings.items():
            os.environ[env_var] = value
            print_info(f"  ✅ 设置 {env_var} = {value}")
        
        print_progress("📦 创建模型管理器实例...")
        
        # 创建模型管理器实例
        try:
            model_manager = ModelManager(settings.model_dump())
        except Exception as e:
            print_error(f"❌ 创建模型管理器失败: {e}")
            return False
        
        print_progress("🔄 开始模型初始化和下载...")
        print_info("📊 下载进度将显示在下方:")
        print()
        
        # 初始化模型（这会触发下载）
        start_time = time.time()
        await model_manager.initialize()
        
        elapsed_time = time.time() - start_time
        print()
        print_success("🎉" + "="*50)
        print_success(f"✅ 所有模型初始化完成! 耗时: {elapsed_time:.2f}秒")
        print_success("🎉" + "="*50)
        
        return True
        
    except KeyboardInterrupt:
        print()
        print_warning("⚠️  用户中断了下载过程")
        print_info("💡 您可以稍后重新运行此脚本继续下载")
        return False
    except Exception as e:
        print_error(f"❌ 模型下载失败: {e}")
        print_error("💡 可能的解决方案:")
        print_error("   1. 检查网络连接是否正常")
        print_error("   2. 确认能够访问 Hugging Face Hub")
        print_error("   3. 检查磁盘空间是否充足")
        print_error("   4. 尝试使用VPN或代理")
        import traceback
        print_error("🔍 详细错误信息:")
        traceback.print_exc()
        return False

def main():
    force_download = "--force" in sys.argv
    
    print("🤖 Any2Markdown 模型检查和下载工具")
    print("=" * 50)
    
    if not force_download and check_model_files():
        print_success("✅ 模型文件已存在，跳过下载")
        print_info("💡 如需强制重新下载，请使用 --force 参数")
        return 0
    
    if force_download:
        print_info("🔄 强制下载模式，将重新下载所有模型")
    
    # 运行异步下载
    try:
        success = asyncio.run(download_models())
    except KeyboardInterrupt:
        print()
        print_warning("⚠️  下载被用户中断")
        return 1
    
    if success:
        print()
        print_success("🎉 模型下载完成！服务器现在可以正常启动了")
        print_info("🚀 您现在可以启动 Any2Markdown 服务")
        return 0
    else:
        print_error("❌ 模型下载失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
