"""
基础渲染器类
所有格式渲染器的基类
"""

import os
import platform
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    DEFAULT_WIDTH, DEFAULT_HEIGHT, PADDING,
    FONT_SIZES, LINE_SPACING, HEADER_CONFIG, FOOTER_CONFIG,
    get_effective_font_sizes, get_effective_line_spacing,
)


def _get_color_schemes():
    from config import get_color_schemes
    return get_color_schemes()


@dataclass
class RenderContext:
    """渲染上下文，包含渲染所需的所有配置"""
    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT
    color_scheme_name: str = "经典红"
    header_config: Dict[str, Any] = field(default_factory=lambda: HEADER_CONFIG.copy())
    footer_config: Dict[str, Any] = field(default_factory=lambda: FOOTER_CONFIG.copy())
    icon_path: Optional[str] = None
    line_spacing: Dict[str, int] = field(default_factory=get_effective_line_spacing)

    @property
    def colors(self) -> Dict[str, str]:
        schemes = _get_color_schemes()
        return schemes.get(self.color_scheme_name) or schemes.get("经典红") or {}

    @property
    def primary_color(self) -> Tuple[int, int, int]:
        return hex_to_rgb(self.colors["primary"])

    @property
    def text_color(self) -> Tuple[int, int, int]:
        return hex_to_rgb(self.colors["text"])

    @property
    def title_color(self) -> Tuple[int, int, int]:
        return hex_to_rgb(self.colors["title"])

    @property
    def background_color(self) -> Tuple[int, int, int]:
        return hex_to_rgb(self.colors["background"])

    @property
    def max_width(self) -> int:
        return self.width - PADDING["left"] - PADDING["right"]


@dataclass
class FontSet:
    """字体集合"""
    header_title: ImageFont.FreeTypeFont
    header_subtitle: ImageFont.FreeTypeFont
    header_tag: ImageFont.FreeTypeFont
    main_title: ImageFont.FreeTypeFont
    lead_text: ImageFont.FreeTypeFont
    body_text: ImageFont.FreeTypeFont
    footer_banner: ImageFont.FreeTypeFont
    small_text: ImageFont.FreeTypeFont


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_system_font_path() -> dict:
    system = platform.system()

    if system == "Windows":
        font_dir = "C:/Windows/Fonts/"
        return {
            "regular": os.path.join(font_dir, "msyh.ttc"),
            "bold": os.path.join(font_dir, "msyhbd.ttc"),
            "song": os.path.join(font_dir, "simsun.ttc"),
            "kai": os.path.join(font_dir, "simkai.ttf"),
            "hei": os.path.join(font_dir, "simhei.ttf"),
            "fangsong": os.path.join(font_dir, "simfang.ttf"),
        }
    elif system == "Darwin":
        font_dir = "/System/Library/Fonts/"
        return {
            "regular": os.path.join(font_dir, "PingFang.ttc"),
            "bold": os.path.join(font_dir, "PingFang.ttc"),
            "song": os.path.join(font_dir, "Songti.ttc"),
            "kai": os.path.join(font_dir, "Kaiti.ttc"),
            "hei": os.path.join(font_dir, "PingFang.ttc"),
        }
    else:
        return {
            "regular": "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            "bold": "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            "song": "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            "kai": "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            "hei": "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        }


def load_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)
    except Exception:
        pass

    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def create_font_set(font_paths: dict = None) -> FontSet:
    if font_paths is None:
        font_paths = get_system_font_path()
    font_sizes = get_effective_font_sizes()

    return FontSet(
        header_title=load_font(font_paths.get("kai", font_paths["regular"]), font_sizes["header_title"]),
        header_subtitle=load_font(font_paths["regular"], font_sizes["header_subtitle"]),
        header_tag=load_font(font_paths.get("kai", font_paths["regular"]), font_sizes["header_tag"]),
        main_title=load_font(font_paths.get("bold", font_paths["regular"]), font_sizes["main_title"]),
        lead_text=load_font(font_paths.get("bold", font_paths["regular"]), font_sizes["lead_text"]),
        body_text=load_font(font_paths["regular"], font_sizes["body_text"]),
        footer_banner=load_font(font_paths.get("kai", font_paths["regular"]), FOOTER_CONFIG["font_size"]),
        small_text=load_font(font_paths["regular"], 28),
    )


def load_icon(icon_path: str, target_height: int = 80) -> Optional[Image.Image]:
    if not icon_path:
        return None

    try:
        if os.path.exists(icon_path):
            icon = Image.open(icon_path)
            if icon.mode != 'RGBA':
                icon = icon.convert('RGBA')

            aspect_ratio = icon.width / icon.height
            new_height = target_height
            new_width = int(new_height * aspect_ratio)

            icon = icon.resize((new_width, new_height), Image.Resampling.LANCZOS)
            return icon
    except Exception:
        pass

    return None


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    lines = []
    current_line = ""

    for char in text:
        test_line = current_line + char
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char

    if current_line:
        lines.append(current_line)

    return lines


class BaseRenderer(ABC):
    """基础渲染器抽象类"""

    EXAMPLE_TEXT: str = ""
    FORMAT_HELP: str = ""

    def __init__(self):
        self.fonts: FontSet = None
        self.context: RenderContext = None

    @abstractmethod
    def parse(self, text: str) -> Any:
        pass

    @abstractmethod
    def render_content(
        self,
        draw: ImageDraw.Draw,
        img: Image.Image,
        data: Any,
        y: int
    ) -> int:
        pass

    def render(
        self,
        text: str,
        context: RenderContext = None
    ) -> Image.Image:
        if context is None:
            context = RenderContext()

        self.context = context
        self.fonts = create_font_set()

        data = self.parse(text)

        img = Image.new('RGB', (context.width, context.height), context.background_color)
        draw = ImageDraw.Draw(img)

        y = self.draw_header(draw, img)
        y = self.render_content(draw, img, data, y)
        self.draw_footer(draw)

        return img

    def draw_header(self, draw: ImageDraw.Draw, img: Image.Image) -> int:
        header_config = self.context.header_config
        primary_color = self.context.primary_color
        text_color = self.context.text_color

        y = PADDING["top"]

        icon = load_icon(self.context.icon_path, target_height=80)
        icon_width = 0
        icon_spacing = 20

        if icon:
            icon_x = PADDING["left"]
            icon_y = y + 10
            img.paste(icon, (icon_x, icon_y), icon)
            icon_width = icon.width + icon_spacing

        title = header_config.get("title", HEADER_CONFIG["title"])
        title_bbox = self.fonts.header_title.getbbox(title)
        title_x = PADDING["left"] + icon_width
        draw.text((title_x, y), title, font=self.fonts.header_title, fill=primary_color)

        subtitle = header_config.get("subtitle", HEADER_CONFIG["subtitle"])
        subtitle_y = y + (title_bbox[3] - title_bbox[1]) + 10
        draw.text((title_x, subtitle_y), subtitle, font=self.fonts.header_subtitle, fill=text_color)

        tag = header_config.get("tag", HEADER_CONFIG["tag"])
        tag_bbox = self.fonts.header_tag.getbbox(tag)
        tag_width = tag_bbox[2] - tag_bbox[0]
        tag_x = self.context.width - PADDING["right"] - tag_width
        tag_y = y + 60
        draw.text((tag_x, tag_y), tag, font=self.fonts.header_tag, fill=primary_color)

        subtitle_bbox = self.fonts.header_subtitle.getbbox(subtitle)
        subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]
        line_y = subtitle_y + subtitle_height + 25

        draw.rectangle(
            [PADDING["left"], line_y, self.context.width - PADDING["right"], line_y + 5],
            fill=primary_color
        )
        draw.rectangle(
            [PADDING["left"], line_y + 10, PADDING["left"] + 180, line_y + 13],
            fill=primary_color
        )

        return line_y + 60

    def draw_footer(self, draw: ImageDraw.Draw) -> None:
        footer_config = self.context.footer_config

        if not footer_config.get("show_banner", True):
            return

        primary_color = self.context.primary_color
        white_color = (255, 255, 255)

        banner_text = footer_config.get("banner_text", "")
        banner_height = footer_config.get("banner_height", 50)
        slant_width = footer_config.get("slant_width", 30)

        banner_y_top = self.context.height - banner_height - 20
        banner_y_bottom = self.context.height - 20

        text_bbox = self.fonts.footer_banner.getbbox(banner_text)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        banner_padding = 60
        banner_width = text_width + banner_padding * 2

        banner_x_start = (self.context.width - banner_width) // 2
        banner_x_end = banner_x_start + banner_width

        polygon_points = [
            (banner_x_start + slant_width, banner_y_top),
            (banner_x_end - slant_width, banner_y_top),
            (banner_x_end, banner_y_top + banner_height // 2),
            (banner_x_end - slant_width, banner_y_bottom),
            (banner_x_start + slant_width, banner_y_bottom),
            (banner_x_start, banner_y_top + banner_height // 2),
        ]

        draw.polygon(polygon_points, fill=primary_color)

        text_x = (self.context.width - text_width) // 2
        text_y = banner_y_top + (banner_height - text_height) // 2 - 2
        draw.text((text_x, text_y), banner_text, font=self.fonts.footer_banner, fill=white_color)

    def draw_main_title(self, draw: ImageDraw.Draw, title: str, y: int) -> int:
        if not title:
            return y

        title_color = self.context.title_color
        max_width = self.context.max_width

        lines = wrap_text(title, self.fonts.main_title, max_width)
        title_bbox = self.fonts.main_title.getbbox("测")
        line_height = title_bbox[3] - title_bbox[1]

        for line in lines:
            line_bbox = self.fonts.main_title.getbbox(line)
            line_width = line_bbox[2] - line_bbox[0]
            x = (self.context.width - line_width) // 2
            draw.text((x, y), line, font=self.fonts.main_title, fill=title_color)
            y += line_height + 18

        return y + 20
