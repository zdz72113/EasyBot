"""
渲染器模块
仅保留 Markdown 格式海报渲染
"""

from .base import BaseRenderer, RenderContext
from .markdown_renderer import MarkdownRenderer

RENDERERS = {
    "markdown": {
        "name": "Markdown",
        "description": "标题、段落、列表，支持加粗主题色",
        "renderer": MarkdownRenderer,
        "icon": "📝",
    },
}

__all__ = [
    "BaseRenderer",
    "RenderContext",
    "MarkdownRenderer",
    "RENDERERS",
]
