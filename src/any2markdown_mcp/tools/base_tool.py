"""
工具基础模块

定义所有MCP工具共用的组件和类型。
"""

from pydantic import Field

# 为所有工具中表示文件内容的参数定义一个可重用的Pydantic Field。
# 这确保了API的一致性，并简化了工具函数的定义。
file_content_field = Field(
    ...,  # `...` 表示这是一个必需的参数
    description="Base64编码的文件内容。这是将文件数据传递给工具的首选方法。",
    # 这些是OpenAPI/JSON Schema的元数据，可以被MCP客户端（如Inspector）用来提供更好的UI
    contentEncoding="base64",
    mediaType="application/octet-stream"  # 通用二进制流，具体工具可以覆盖
) 