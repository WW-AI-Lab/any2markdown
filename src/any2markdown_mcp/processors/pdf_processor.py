"""
PDF文档处理器

基于marker-pdf实现PDF转换功能，支持：
- 高质量PDF转Markdown转换
- 页眉页脚智能移除
- 图片提取和静态化
- 分页输出
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import re

import structlog
import pymupdf  # PyMuPDF
from PIL import Image
import io

from .base_processor import BaseProcessor

logger = structlog.get_logger(__name__)


class PDFProcessor(BaseProcessor):
    """PDF文档处理器"""
    
    def __init__(self, config: Dict[str, Any], model_manager=None):
        super().__init__(config)
        self.model_manager = model_manager
        
        # PDF特定配置
        self.pdf_dpi = self._get_config_value("pdf_dpi", 150)
        self.pdf_max_pages = self._get_config_value("pdf_max_pages", 500)
        
        logger.info("PDFProcessor initialized")
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式"""
        return ["pdf"]
    
    async def convert(self, file_content: bytes, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换PDF文档
        
        Args:
            file_content: PDF文件内容
            options: 转换选项
            
        Returns:
            转换结果
        """
        temp_files = []
        
        try:
            # 验证文件大小
            self.validate_file_size(file_content)
            
            # 保存临时PDF文件
            temp_pdf_path = await self.save_temp_file(file_content, suffix=".pdf")
            temp_files.append(str(temp_pdf_path))
            
            logger.info("Starting PDF conversion", 
                       file_size=len(file_content),
                       temp_path=str(temp_pdf_path))
            
            # 分析PDF结构
            pdf_info = await self._analyze_pdf_structure(temp_pdf_path)
            
            # 检查页面范围
            start_page = options.get("start_page", 0)
            end_page = options.get("end_page", None)
            if end_page is None:
                end_page = pdf_info["page_count"]
            elif end_page > pdf_info["page_count"]:
                end_page = pdf_info["page_count"]
            
            # 提取图片（如果启用）
            images_info = []
            if options.get("extract_images", True):
                images_info = await self._extract_images(temp_pdf_path, start_page, end_page)
                # 注意：不要将图片文件添加到temp_files中，因为它们需要被保留用于静态文件服务
            
            # 使用marker转换PDF
            markdown_content, conversion_metadata = await self._convert_with_marker(
                temp_pdf_path, options
            )
            
            # 移除页眉页脚（如果启用）
            if options.get("remove_header_footer", True):
                markdown_content = await self._remove_header_footer(
                    markdown_content, pdf_info, options
                )
            
            # 嵌入图片URL到markdown中
            if images_info:
                markdown_content = await self._embed_image_urls(markdown_content, images_info)
            
            # 分页处理
            if options.get("paginate_output", True):
                pages = await self._paginate_content(markdown_content, pdf_info)
            else:
                pages = [{"page": 1, "content": markdown_content}]
            
            # 构建元数据
            metadata = {
                "source_type": "pdf",
                "page_count": pdf_info["page_count"],
                "processed_pages": f"{start_page}-{end_page}",
                "images": images_info,
                "conversion_time": conversion_metadata.get("conversion_time", 0),
                "model_info": conversion_metadata.get("model_info", {}),
                "file_size": len(file_content),
                "options_used": options
            }
            
            # 格式化输出
            result = self.format_output(
                markdown_content if not options.get("paginate_output", True) else pages,
                metadata,
                options.get("output_format", "markdown")
            )
            
            logger.info("PDF conversion completed successfully",
                       pages_processed=end_page - start_page,
                       images_extracted=len(images_info))
            
            return result
            
        except Exception as e:
            logger.error("PDF conversion failed", error=str(e))
            raise
        finally:
            # 清理临时文件
            if temp_files:
                await self.cleanup_temp_files(temp_files)
    
    async def _analyze_pdf_structure(self, pdf_path: Path) -> Dict[str, Any]:
        """分析PDF文档结构"""
        try:
            doc = pymupdf.open(str(pdf_path))
            
            info = {
                "page_count": len(doc),
                "metadata": doc.metadata,
                "has_images": False,
                "has_tables": False,
                "text_density": [],
                "page_sizes": []
            }
            
            # 分析每页内容
            for page_num in range(min(len(doc), 10)):  # 只分析前10页以提高性能
                page = doc[page_num]
                
                # 页面尺寸
                info["page_sizes"].append({
                    "width": page.rect.width,
                    "height": page.rect.height
                })
                
                # 文本密度
                text = page.get_text()
                info["text_density"].append(len(text.strip()))
                
                # 检查是否有图片
                if not info["has_images"]:
                    images = page.get_images()
                    info["has_images"] = len(images) > 0
                
                # 检查是否有表格（简单检测）
                if not info["has_tables"]:
                    try:
                        # 通过检测表格特征来判断
                        tables = page.find_tables()
                        # 确保tables是可迭代对象
                        if hasattr(tables, '__len__'):
                            info["has_tables"] = len(tables) > 0
                        elif hasattr(tables, '__iter__'):
                            info["has_tables"] = any(True for _ in tables)
                        else:
                            info["has_tables"] = False
                    except Exception as e:
                        logger.debug("Table detection failed", error=str(e))
                        info["has_tables"] = False
            
            doc.close()
            
            logger.debug("PDF structure analyzed", info=info)
            return info
            
        except Exception as e:
            logger.error("Failed to analyze PDF structure", error=str(e))
            raise
    
    async def _extract_images(self, pdf_path: Path, start_page: int, end_page: int) -> List[Dict[str, Any]]:
        """从PDF中提取图片"""
        images_info = []
        logger.info("开始从PDF中提取图片", path=str(pdf_path), page_range=f"{start_page}-{end_page}")
        
        try:
            doc = pymupdf.open(str(pdf_path))
            image_count = 0
            
            for page_num in range(start_page, min(end_page, len(doc))):
                page = doc[page_num]
                page_images = page.get_images()
                if page_images:
                    logger.info(f"在页面 {page_num + 1} 发现 {len(page_images)} 张图片")
                    image_count += len(page_images)

                for img_index, img in enumerate(page_images):
                    try:
                        # 获取图片数据
                        xref = img[0]
                        pix = pymupdf.Pixmap(doc, xref)
                        
                        # 跳过过小的图片（可能是装饰性图片）
                        if pix.width < 50 or pix.height < 50:
                            pix = None
                            continue
                        
                        # 保存原始尺寸信息
                        original_width = pix.width
                        original_height = pix.height
                        
                        # 转换为PNG格式
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            img_data = pix.tobytes("png")
                        else:  # CMYK: 转换为RGB
                            pix_rgb = pymupdf.Pixmap(pymupdf.csRGB, pix)
                            img_data = pix_rgb.tobytes("png")
                            pix_rgb = None
                        
                        pix = None
                        
                        # 验证图片数据有效性
                        if not img_data or len(img_data) == 0:
                            logger.warning("Empty image data", 
                                         page=page_num + 1, 
                                         index=img_index + 1)
                            continue
                        
                        # 保存图片（使用实例ID避免文件名冲突）
                        filename = f"pdf_{self.instance_id}_page_{page_num + 1}_img_{img_index + 1}.png"
                        
                        logger.info("准备保存图片", 
                                  filename=filename, 
                                  data_size=len(img_data),
                                  page=page_num + 1,
                                  index=img_index + 1)
                        
                        image_info = await self.save_image(img_data, filename)
                        
                        # 验证图片是否真正保存成功
                        saved_path = Path(image_info["path"])
                        if not saved_path.exists():
                            logger.error("图片保存失败：文件不存在", 
                                       path=str(saved_path),
                                       filename=filename)
                            continue
                        
                        # 添加页面和位置信息
                        image_info.update({
                            "page": page_num + 1,
                            "index": img_index + 1,
                            "original_size": {
                                "width": original_width,
                                "height": original_height
                            }
                        })
                        
                        images_info.append(image_info)
                        
                        logger.info("图片提取并保存成功", 
                                  page=page_num + 1, 
                                  index=img_index + 1,
                                  filename=filename,
                                  saved_path=str(saved_path),
                                  file_exists=saved_path.exists())
                        
                    except Exception as e:
                        logger.error("图片提取失败", 
                                   page=page_num + 1, 
                                   index=img_index + 1,
                                   error=str(e),
                                   error_type=type(e).__name__)
                        import traceback
                        logger.debug("图片提取异常详情", traceback=traceback.format_exc())
                        continue
            
            doc.close()
            
            logger.info("图片提取完成", total_found=image_count, total_saved=len(images_info))
            return images_info
            
        except Exception as e:
            logger.error("从PDF提取图片时出错", error=str(e))
            return []
    
    async def _convert_with_marker(self, pdf_path: Path, options: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """使用marker转换PDF"""
        try:
            if not self.model_manager:
                raise ValueError("Model manager not available")
            
            # 准备marker转换参数（移除不支持的langs参数）
            marker_options = {
                "batch_multiplier": options.get("batch_multiplier", 2),
            }
            
            # 只添加marker支持的参数
            if "start_page" in options:
                marker_options["start_page"] = options["start_page"]
            
            logger.info("Starting marker conversion", options=marker_options)
            
            # 调用marker转换
            result = await self.model_manager.convert_pdf_with_marker(
                str(pdf_path), **marker_options
            )
            
            # marker返回(text, images, metadata)
            if isinstance(result, tuple) and len(result) >= 2:
                markdown_content = result[0]
                conversion_metadata = result[2] if len(result) > 2 else {}
            else:
                markdown_content = str(result)
                conversion_metadata = {}
            
            logger.info("Marker conversion completed", 
                       content_length=len(markdown_content))
            
            return markdown_content, conversion_metadata
            
        except Exception as e:
            logger.error("Marker conversion failed", error=str(e))
            # 如果marker转换失败，尝试使用PyMuPDF作为备选
            return await self._fallback_conversion(pdf_path, options)
    
    async def _fallback_conversion(self, pdf_path: Path, options: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """备选转换方法（使用PyMuPDF）"""
        try:
            logger.info("Using fallback conversion method")
            
            doc = pymupdf.open(str(pdf_path))
            markdown_content = ""
            
            start_page = options.get("start_page", 0)
            end_page = options.get("end_page")
            if end_page is None:
                end_page = len(doc)
            
            for page_num in range(start_page, min(end_page, len(doc))):
                page = doc[page_num]
                
                # 提取文本
                text = page.get_text()
                
                # 简单的markdown格式化
                if text.strip():
                    markdown_content += f"\n\n## Page {page_num + 1}\n\n{text}\n"
            
            doc.close()
            
            metadata = {
                "conversion_method": "pymupdf_fallback",
                "conversion_time": 0
            }
            
            return markdown_content, metadata
            
        except Exception as e:
            logger.error("Fallback conversion failed", error=str(e))
            raise
    
    async def _remove_header_footer(self, content: str, pdf_info: Dict[str, Any], options: Dict[str, Any]) -> str:
        """移除PDF页眉页脚"""
        if not options.get("remove_header_footer", True):
            return content
        
        logger.info("Removing header/footer from PDF content")
        
        # 使用基类的通用方法
        cleaned_content = self.remove_header_footer_text(content, options)
        
        # PDF特定的页眉页脚处理
        cleaned_content = await self._remove_pdf_specific_headers_footers(cleaned_content, pdf_info)
        
        return cleaned_content
    
    async def _remove_pdf_specific_headers_footers(self, content: str, pdf_info: Dict[str, Any]) -> str:
        """移除PDF特定的页眉页脚"""
        lines = content.split('\n')
        cleaned_lines = []
        
        # 检测重复出现的行（可能是页眉页脚）
        line_counts = {}
        for line in lines:
            line = line.strip()
            if line:
                line_counts[line] = line_counts.get(line, 0) + 1
        
        # 如果某行出现次数接近页面数，可能是页眉页脚
        page_count = pdf_info.get("page_count", 1)
        threshold = max(2, page_count // 3)  # 至少出现页面数的1/3次
        
        repeated_lines = {line for line, count in line_counts.items() 
                         if count >= threshold and len(line) < 100}
        
        for line in lines:
            line_stripped = line.strip()
            
            # 跳过重复的可能页眉页脚行
            if line_stripped in repeated_lines:
                logger.debug("Removing repeated line (likely header/footer)", line=line_stripped)
                continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    async def _embed_image_urls(self, content: str, images_info: List[Dict[str, Any]]) -> str:
        """将图片URL嵌入到markdown内容中"""
        if not images_info:
            return content
        
        logger.info("Embedding image URLs in markdown", count=len(images_info))
        
        # 按页面分组图片
        images_by_page = {}
        for img in images_info:
            page = img.get("page", 1)
            if page not in images_by_page:
                images_by_page[page] = []
            images_by_page[page].append(img)
        
        # 在每页内容后添加图片
        lines = content.split('\n')
        result_lines = []
        current_page = 1
        
        for line in lines:
            result_lines.append(line)
            
            # 检测页面分隔符
            if line.startswith('## Page ') or line.startswith('# Page '):
                try:
                    page_match = re.search(r'Page (\d+)', line)
                    if page_match:
                        current_page = int(page_match.group(1))
                except:
                    pass
            
            # 在页面结束时添加图片
            if (line.strip() == '' and 
                current_page in images_by_page and 
                len(result_lines) > 1 and 
                result_lines[-2].strip() != ''):
                
                result_lines.append('')  # 空行分隔
                result_lines.append(f'### Images from Page {current_page}')
                result_lines.append('')
                
                for img in images_by_page[current_page]:
                    alt_text = f"Image {img['index']} from page {img['page']}"
                    result_lines.append(f"![{alt_text}]({img['url']})")
                    result_lines.append('')
                
                # 标记该页面的图片已处理
                del images_by_page[current_page]
        
        # 处理剩余未处理的图片
        for page, imgs in images_by_page.items():
            result_lines.append('')
            result_lines.append(f'### Images from Page {page}')
            result_lines.append('')
            
            for img in imgs:
                alt_text = f"Image {img['index']} from page {img['page']}"
                result_lines.append(f"![{alt_text}]({img['url']})")
                result_lines.append('')
        
        return '\n'.join(result_lines)
    
    async def _paginate_content(self, content: str, pdf_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """将内容分页"""
        pages = []
        
        # 按页面分隔符分割内容
        page_pattern = r'^##?\s*Page\s+(\d+)'
        lines = content.split('\n')
        
        current_page_content = []
        current_page_num = 1
        
        for line in lines:
            page_match = re.match(page_pattern, line.strip())
            
            if page_match:
                # 保存当前页面
                if current_page_content:
                    pages.append({
                        "page": current_page_num,
                        "content": '\n'.join(current_page_content).strip()
                    })
                
                # 开始新页面
                current_page_num = int(page_match.group(1))
                current_page_content = [line]
            else:
                current_page_content.append(line)
        
        # 保存最后一页
        if current_page_content:
            pages.append({
                "page": current_page_num,
                "content": '\n'.join(current_page_content).strip()
            })
        
        # 如果没有找到页面分隔符，将整个内容作为一页
        if not pages:
            pages.append({
                "page": 1,
                "content": content.strip()
            })
        
        logger.info("Content paginated", total_pages=len(pages))
        return pages 