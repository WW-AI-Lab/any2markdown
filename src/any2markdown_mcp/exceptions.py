"""
Exceptions for Any2Markdown MCP Server
"""


class MCPError(Exception):
    """Base exception for MCP server errors"""
    pass


class ToolError(MCPError):
    """Exception raised when tool execution fails"""
    pass


class ValidationError(MCPError):
    """Exception raised when input validation fails"""
    pass


class ConversionError(MCPError):
    """Exception raised when document conversion fails"""
    pass 