"""
海报渲染服务

排版采用三层结构：
- 顶部 Header：栏目标签 + 大标题 + 副标题（KNOWLEDGE 等英文小标）
- 中部 Body：精简后的 QA 内容（Q 作为小标题，A 作为正文）
- 底部 Footer：摘要、标签、品牌信息（下标）

为了在不同长度的内容下都保持专业排版，绘制流程会：
1. 预估三层高度，自动收缩内容条数；
2. 单条 QA 的回答超出上限时进行截断，并补省略号；
3. 支持背景图片（来自维度素材）的暗色覆盖叠加，避免文字看不清。
"""
from __future__ import annotations

import base64
import io
import re
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.models.schemas import ContentResult, PosterConfig, QAPair


class PosterService:
    """海报生成服务"""

    DEFAULT_WIDTH = 1080
    DEFAULT_HEIGHT = 1920

    SAFE_MARGIN_X = 96
    SAFE_MARGIN_TOP = 120
    SAFE_MARGIN_BOTTOM = 140

    HEADER_RESERVED = 360
    FOOTER_RESERVED = 220

    FONT_SIZES = {
        "tag": 30,
        "title": 84,
        "subtitle": 30,
        "question": 44,
        "answer_default": 34,
        "footer_summary": 28,
        "footer_brand": 26,
    }

    MAX_QA_ITEMS = 5
    MIN_QA_ITEMS = 2
    MAX_TITLE_LINES = 2
    MAX_QUESTION_LINES = 2
    MAX_ANSWER_LINES = 4

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.font_dir = self.base_dir / "fonts"
        self.font_dir.mkdir(exist_ok=True)

    # ---------- font / drawing helpers ----------

    def _get_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        bold_paths = [
            self.font_dir / "NotoSansSC-Bold.ttf",
            self.font_dir / "SourceHanSansSC-Bold.ttf",
            Path("C:/Windows/Fonts/msyhbd.ttc"),
            Path("C:/Windows/Fonts/simhei.ttf"),
        ]
        regular_paths = [
            self.font_dir / "NotoSansSC-Regular.ttf",
            self.font_dir / "SourceHanSansSC-Regular.ttf",
            Path("C:/Windows/Fonts/msyh.ttc"),
            Path("C:/Windows/Fonts/simhei.ttf"),
            Path("C:/Windows/Fonts/simsun.ttc"),
        ]
        font_paths = bold_paths if bold else regular_paths
        for path in font_paths:
            try:
                if path and Path(path).exists():
                    return ImageFont.truetype(str(path), size)
            except Exception:
                continue
        return ImageFont.load_default()

    def _wrap_text(
        self,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int,
    ) -> List[str]:
        if not text:
            return []
        cleaned = re.sub(r"\s+", " ", text.strip())
        lines: List[str] = []
        current = ""
        for ch in cleaned:
            test = current + ch
            if font.getbbox(test)[2] > max_width and current:
                lines.append(current)
                current = ch
            else:
                current = test
        if current:
            lines.append(current)
        return lines

    def _line_height(self, font: ImageFont.FreeTypeFont) -> int:
        bbox = font.getbbox("汉Aj")
        return bbox[3] - bbox[1]

    def _truncate_lines(
        self,
        lines: List[str],
        max_lines: int,
        font: ImageFont.FreeTypeFont,
        max_width: int,
    ) -> List[str]:
        if len(lines) <= max_lines:
            return lines
        truncated = lines[:max_lines]
        last = truncated[-1]
        while last and font.getbbox(last + "…")[2] > max_width:
            last = last[:-1]
        truncated[-1] = (last or "").rstrip() + "…"
        return truncated

    # ---------- color helpers ----------

    @staticmethod
    def _hex_to_rgb(value: str) -> Tuple[int, int, int]:
        value = value.lstrip("#")
        if len(value) == 3:
            value = "".join(ch * 2 for ch in value)
        try:
            return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
        except Exception:
            return (255, 255, 255)

    @staticmethod
    def _mix(rgb_a: Tuple[int, int, int], rgb_b: Tuple[int, int, int], ratio: float) -> Tuple[int, int, int]:
        return tuple(int(a + (b - a) * ratio) for a, b in zip(rgb_a, rgb_b))  # type: ignore[return-value]

    def _get_color_scheme(self, scheme_name: str) -> dict:
        schemes = {
            "经典红": {
                "primary": "#C41E24",
                "background": "#FFFFFF",
                "panel": "#FBF6F4",
                "text": "#1F1F1F",
                "text_secondary": "#5C5C5C",
                "text_inverse": "#FFFFFF",
                "divider": "#E9DCDA",
                "accent": "#C41E24",
            },
            "墨绿": {
                "primary": "#2D5A4A",
                "background": "#F5F9F7",
                "panel": "#E8F1EC",
                "text": "#172A22",
                "text_secondary": "#4F665C",
                "text_inverse": "#FFFFFF",
                "divider": "#D4E2DA",
                "accent": "#2D5A4A",
            },
            "沉稳灰": {
                "primary": "#1F2937",
                "background": "#F8FAFC",
                "panel": "#EEF2F7",
                "text": "#0F172A",
                "text_secondary": "#475569",
                "text_inverse": "#FFFFFF",
                "divider": "#D8DEE9",
                "accent": "#0EA5E9",
            },
        }
        return schemes.get(scheme_name, schemes["经典红"])

    # ---------- background ----------

    def _build_background(
        self,
        colors: dict,
        background_image: Optional[str],
    ) -> Image.Image:
        canvas = Image.new("RGB", (self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT), colors["background"])
        if not background_image:
            return canvas

        try:
            data = self._load_image(background_image)
            if data is None:
                return canvas
            bg = Image.open(io.BytesIO(data)).convert("RGB")
            bg = bg.filter(ImageFilter.GaussianBlur(radius=10))
            bg = self._cover_resize(bg, (self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT))
            canvas.paste(bg, (0, 0))

            overlay = Image.new(
                "RGBA",
                (self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT),
                (*self._hex_to_rgb(colors["background"]), 215),
            )
            canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
        except Exception:
            return Image.new("RGB", (self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT), colors["background"])
        return canvas

    @staticmethod
    def _cover_resize(img: Image.Image, size: Tuple[int, int]) -> Image.Image:
        target_w, target_h = size
        ratio = max(target_w / img.width, target_h / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        resized = img.resize(new_size, Image.LANCZOS)
        left = (resized.width - target_w) // 2
        top = (resized.height - target_h) // 2
        return resized.crop((left, top, left + target_w, top + target_h))

    @staticmethod
    def _load_image(source: str) -> Optional[bytes]:
        if not source:
            return None
        if source.startswith("data:"):
            try:
                _, encoded = source.split(",", 1)
                return base64.b64decode(encoded)
            except Exception:
                return None
        if source.startswith("http://") or source.startswith("https://"):
            try:
                import requests

                resp = requests.get(source, timeout=10)
                resp.raise_for_status()
                return resp.content
            except Exception:
                return None
        path = Path(source)
        if path.exists():
            return path.read_bytes()
        return None

    # ---------- layout ----------

    def generate(self, content: ContentResult, config: PosterConfig) -> Image.Image:
        colors = self._get_color_scheme(config.color_scheme)
        canvas = self._build_background(colors, getattr(config, "background_image", None))
        draw = ImageDraw.Draw(canvas)

        body_top, body_bottom = self._draw_header(draw, canvas, content, config, colors)
        self._draw_body(draw, content, config, colors, body_top, body_bottom)
        self._draw_footer(draw, canvas, content, config, colors)

        return canvas

    # ---------- header ----------

    def _draw_header(
        self,
        draw: ImageDraw.Draw,
        canvas: Image.Image,
        content: ContentResult,
        config: PosterConfig,
        colors: dict,
    ) -> Tuple[int, int]:
        margin_x = self.SAFE_MARGIN_X
        max_width = self.DEFAULT_WIDTH - margin_x * 2

        accent_rgb = self._hex_to_rgb(colors["accent"])
        draw.rectangle([0, 0, self.DEFAULT_WIDTH, 6], fill=accent_rgb)

        y = self.SAFE_MARGIN_TOP

        tag_text = (config.header_tag or "").strip()
        if tag_text:
            tag_font = self._get_font(self.FONT_SIZES["tag"], bold=True)
            tag_w = tag_font.getbbox(tag_text)[2] + 36
            tag_h = self._line_height(tag_font) + 16
            draw.rounded_rectangle(
                [margin_x, y, margin_x + tag_w, y + tag_h],
                radius=tag_h // 2,
                fill=accent_rgb,
            )
            draw.text(
                (margin_x + 18, y + 6),
                tag_text,
                font=tag_font,
                fill=colors["text_inverse"],
            )
            y += tag_h + 28

        title_text = content.title or config.header_title or ""
        if title_text:
            title_font = self._get_font(self.FONT_SIZES["title"], bold=True)
            lines = self._wrap_text(title_text, title_font, max_width)
            lines = self._truncate_lines(lines, self.MAX_TITLE_LINES, title_font, max_width)
            line_h = self._line_height(title_font)
            for line in lines:
                draw.text((margin_x, y), line, font=title_font, fill=colors["text"])
                y += line_h + 14
            draw.rectangle([margin_x, y + 8, margin_x + 96, y + 14], fill=accent_rgb)
            y += 30

        subtitle_text = (config.header_subtitle or "").strip()
        if subtitle_text:
            sub_font = self._get_font(self.FONT_SIZES["subtitle"])
            draw.text((margin_x, y), subtitle_text, font=sub_font, fill=colors["text_secondary"])
            y += self._line_height(sub_font) + 18

        body_top = max(y + 24, self.HEADER_RESERVED)
        body_bottom = self.DEFAULT_HEIGHT - self.FOOTER_RESERVED
        return body_top, body_bottom

    # ---------- body ----------

    def _draw_body(
        self,
        draw: ImageDraw.Draw,
        content: ContentResult,
        config: PosterConfig,
        colors: dict,
        body_top: int,
        body_bottom: int,
    ) -> None:
        margin_x = self.SAFE_MARGIN_X
        content_width = self.DEFAULT_WIDTH - margin_x * 2

        qa_list = [qa for qa in (content.qa_list or []) if (qa.q or qa.a)]
        if not qa_list:
            return

        line_spacing = max(8, config.line_spacing)
        paragraph_spacing = max(20, config.paragraph_spacing)
        body_text_size = max(24, config.body_text_size or self.FONT_SIZES["answer_default"])

        question_font = self._get_font(self.FONT_SIZES["question"], bold=True)
        answer_font = self._get_font(body_text_size)

        question_h = self._line_height(question_font)
        answer_h = self._line_height(answer_font)

        max_height = body_bottom - body_top
        chosen, items_layout = self._fit_items(
            qa_list,
            margin_x,
            content_width,
            question_font,
            answer_font,
            question_h,
            answer_h,
            line_spacing,
            paragraph_spacing,
            max_height,
        )

        if not items_layout:
            return

        accent_rgb = self._hex_to_rgb(colors["accent"])
        text_rgb = self._hex_to_rgb(colors["text"])
        secondary_rgb = self._hex_to_rgb(colors["text_secondary"])

        y = body_top
        for index, layout in enumerate(items_layout, 1):
            q_lines = layout["question_lines"]
            a_lines = layout["answer_lines"]
            block_height = layout["height"]

            badge_size = question_h + 10
            badge_x = margin_x
            badge_y = y - 4
            draw.rounded_rectangle(
                [badge_x, badge_y, badge_x + badge_size + 18, badge_y + badge_size],
                radius=8,
                fill=accent_rgb,
            )
            badge_label = f"Q{index}"
            badge_font = self._get_font(int(self.FONT_SIZES["question"] * 0.7), bold=True)
            badge_label_w = badge_font.getbbox(badge_label)[2]
            draw.text(
                (badge_x + (badge_size + 18 - badge_label_w) // 2, badge_y + 6),
                badge_label,
                font=badge_font,
                fill=colors["text_inverse"],
            )

            text_x = margin_x + badge_size + 36
            text_max_w = content_width - (badge_size + 36)
            cursor_y = y
            for line in q_lines:
                draw.text((text_x, cursor_y), line, font=question_font, fill=text_rgb)
                cursor_y += question_h + 8

            cursor_y += 10
            for line in a_lines:
                draw.text((text_x, cursor_y), line, font=answer_font, fill=secondary_rgb)
                cursor_y += answer_h + line_spacing

            y += block_height + paragraph_spacing

        if len(qa_list) > len(items_layout):
            remaining_font = self._get_font(self.FONT_SIZES["footer_summary"])
            note = f"…还有 {len(qa_list) - len(items_layout)} 个问题，扫码或访问文末链接查看"
            draw.text(
                (margin_x, body_bottom - self._line_height(remaining_font) - 16),
                note,
                font=remaining_font,
                fill=secondary_rgb,
            )

    def _fit_items(
        self,
        qa_list: List[QAPair],
        margin_x: int,
        content_width: int,
        question_font: ImageFont.FreeTypeFont,
        answer_font: ImageFont.FreeTypeFont,
        question_h: int,
        answer_h: int,
        line_spacing: int,
        paragraph_spacing: int,
        max_height: int,
    ) -> Tuple[int, List[dict]]:
        target_count = min(self.MAX_QA_ITEMS, len(qa_list))
        text_max_w = content_width - (question_h + 10 + 36)

        for count in range(target_count, max(self.MIN_QA_ITEMS - 1, 0), -1):
            for max_answer_lines in range(self.MAX_ANSWER_LINES, 1, -1):
                items = self._layout_items(
                    qa_list[:count],
                    text_max_w,
                    question_font,
                    answer_font,
                    question_h,
                    answer_h,
                    line_spacing,
                    max_answer_lines,
                )
                total = sum(item["height"] for item in items) + paragraph_spacing * (len(items) - 1)
                if total <= max_height:
                    return count, items

        items = self._layout_items(
            qa_list[: max(self.MIN_QA_ITEMS, 1)],
            text_max_w,
            question_font,
            answer_font,
            question_h,
            answer_h,
            line_spacing,
            2,
        )
        return len(items), items

    def _layout_items(
        self,
        qa_list: List[QAPair],
        text_max_w: int,
        question_font: ImageFont.FreeTypeFont,
        answer_font: ImageFont.FreeTypeFont,
        question_h: int,
        answer_h: int,
        line_spacing: int,
        max_answer_lines: int,
    ) -> List[dict]:
        items = []
        for qa in qa_list:
            q_lines = self._wrap_text(qa.q or "", question_font, text_max_w)
            q_lines = self._truncate_lines(q_lines, self.MAX_QUESTION_LINES, question_font, text_max_w)

            a_lines = self._wrap_text(qa.a or "", answer_font, text_max_w)
            a_lines = self._truncate_lines(a_lines, max_answer_lines, answer_font, text_max_w)

            height = (
                len(q_lines) * (question_h + 8)
                + 10
                + len(a_lines) * (answer_h + line_spacing)
            )
            items.append(
                {
                    "question_lines": q_lines,
                    "answer_lines": a_lines,
                    "height": height,
                }
            )
        return items

    # ---------- footer ----------

    def _draw_footer(
        self,
        draw: ImageDraw.Draw,
        canvas: Image.Image,
        content: ContentResult,
        config: PosterConfig,
        colors: dict,
    ) -> None:
        margin_x = self.SAFE_MARGIN_X
        max_width = self.DEFAULT_WIDTH - margin_x * 2

        divider_y = self.DEFAULT_HEIGHT - self.FOOTER_RESERVED + 20
        draw.line(
            [(margin_x, divider_y), (margin_x + max_width, divider_y)],
            fill=self._hex_to_rgb(colors["divider"]),
            width=2,
        )

        secondary_rgb = self._hex_to_rgb(colors["text_secondary"])
        text_rgb = self._hex_to_rgb(colors["text"])
        accent_rgb = self._hex_to_rgb(colors["accent"])

        y = divider_y + 24

        summary_font = self._get_font(self.FONT_SIZES["footer_summary"])
        summary = (content.summary or "").strip()
        if summary:
            lines = self._wrap_text(summary, summary_font, max_width)
            lines = self._truncate_lines(lines, 2, summary_font, max_width)
            for line in lines:
                draw.text((margin_x, y), line, font=summary_font, fill=secondary_rgb)
                y += self._line_height(summary_font) + 6
            y += 8

        tag_font = self._get_font(self.FONT_SIZES["footer_brand"], bold=True)
        chip_x = margin_x
        chip_y = y
        for tag in (content.tags or [])[:5]:
            label = tag if tag.startswith("#") else f"#{tag}"
            tw = tag_font.getbbox(label)[2] + 28
            th = self._line_height(tag_font) + 14
            if chip_x + tw > margin_x + max_width:
                chip_x = margin_x
                chip_y += th + 10
            draw.rounded_rectangle(
                [chip_x, chip_y, chip_x + tw, chip_y + th],
                radius=th // 2,
                outline=accent_rgb,
                width=2,
            )
            draw.text((chip_x + 14, chip_y + 6), label, font=tag_font, fill=accent_rgb)
            chip_x += tw + 12

        brand_text = (config.header_title or "").strip() or "EasyBot"
        brand_font = self._get_font(self.FONT_SIZES["footer_brand"], bold=True)
        brand_w = brand_font.getbbox(brand_text)[2]
        brand_y = self.DEFAULT_HEIGHT - self.SAFE_MARGIN_BOTTOM // 2 - 14
        draw.text(
            (self.DEFAULT_WIDTH - margin_x - brand_w, brand_y),
            brand_text,
            font=brand_font,
            fill=text_rgb,
        )

    # ---------- output ----------

    def to_bytes(self, img: Image.Image, format: str = "PNG") -> bytes:
        buffer = io.BytesIO()
        img.save(buffer, format=format, quality=95)
        return buffer.getvalue()
