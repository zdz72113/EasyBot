"""
Markdown 格式渲染器
支持标题、段落、有序/无序列表、加粗主题色
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Any, Tuple
from PIL import Image, ImageDraw

from .base import BaseRenderer, RenderContext, wrap_text, PADDING


@dataclass
class ListItem:
    text: str
    order: Optional[int] = None


@dataclass
class Paragraph:
    lead: str = ""
    body: str = ""
    list_items: List[ListItem] = field(default_factory=list)
    is_ordered_list: bool = False


@dataclass
class MarkdownContent:
    title: str = ""
    paragraphs: List[Paragraph] = field(default_factory=list)
    footnote: str = ""


class MarkdownRenderer(BaseRenderer):
    """Markdown 格式渲染器"""

    EXAMPLE_TEXT = """# 主标题

**引导语（加粗主题色）**这里是正文内容，正文中的**重点**也会显示主题色。

**另一个要点：**

• 无序列表项一
• **加粗内容**普通内容

**有序列表：**

1. 第一项内容
2. 第二项内容
3. 第三项内容

> 数据来源：XX网站"""

    FORMAT_HELP = """
**Markdown 格式说明：**

- 使用 `# 标题` 设置大标题（居中显示）
- 使用 `**文字**` 设置主题色文字
- 支持无序列表：`- 项目` 或 `• 项目`
- 支持有序列表：`1. 项目`
- 每个段落之间用空行分隔
- 使用 `> 备注` 或 `注：备注` 添加底部说明
"""

    def parse(self, text: str) -> MarkdownContent:
        lines = text.strip().split('\n')

        title = ""
        paragraphs = []
        current_paragraph_lines = []
        current_list_items = []
        current_list_ordered = False
        in_list = False
        footnote = ""

        def flush_paragraph():
            nonlocal current_paragraph_lines, current_list_items, in_list, current_list_ordered

            if current_list_items:
                para = Paragraph(
                    list_items=current_list_items,
                    is_ordered_list=current_list_ordered
                )
                paragraphs.append(para)
                current_list_items = []
                in_list = False

            if current_paragraph_lines:
                paragraph_text = ''.join(current_paragraph_lines)
                para = self._parse_paragraph(paragraph_text)
                if para:
                    paragraphs.append(para)
                current_paragraph_lines = []

        for line in lines:
            line = line.strip()

            if not line:
                flush_paragraph()
                continue

            if line.startswith('# '):
                flush_paragraph()
                title = line[2:].strip()
                continue

            if line.startswith('> '):
                footnote = line[2:].strip()
                continue
            footnote_match = re.match(r'^注\s*[:：]\s*(.+)$', line)
            if footnote_match:
                footnote = footnote_match.group(1).strip()
                continue

            if self._is_unordered_list_item(line):
                if current_paragraph_lines:
                    paragraph_text = ''.join(current_paragraph_lines)
                    para = self._parse_paragraph(paragraph_text)
                    if para:
                        paragraphs.append(para)
                    current_paragraph_lines = []

                if in_list and current_list_ordered:
                    para = Paragraph(list_items=current_list_items, is_ordered_list=True)
                    paragraphs.append(para)
                    current_list_items = []

                in_list = True
                current_list_ordered = False
                current_list_items.append(self._parse_list_item(line, False))
                continue

            is_ordered, _ = self._is_ordered_list_item(line)
            if is_ordered:
                if current_paragraph_lines:
                    paragraph_text = ''.join(current_paragraph_lines)
                    para = self._parse_paragraph(paragraph_text)
                    if para:
                        paragraphs.append(para)
                    current_paragraph_lines = []

                if in_list and not current_list_ordered:
                    para = Paragraph(list_items=current_list_items, is_ordered_list=False)
                    paragraphs.append(para)
                    current_list_items = []

                in_list = True
                current_list_ordered = True
                current_list_items.append(self._parse_list_item(line, True))
                continue

            if in_list:
                para = Paragraph(list_items=current_list_items, is_ordered_list=current_list_ordered)
                paragraphs.append(para)
                current_list_items = []
                in_list = False

            current_paragraph_lines.append(line)

        flush_paragraph()

        return MarkdownContent(title=title, paragraphs=paragraphs, footnote=footnote)

    def _is_unordered_list_item(self, line: str) -> bool:
        return line.startswith('- ') or line.startswith('* ') or line.startswith('• ')

    def _is_ordered_list_item(self, line: str) -> Tuple[bool, Optional[int]]:
        match = re.match(r'^(\d+)\.\s+', line)
        if match:
            return True, int(match.group(1))
        return False, None

    def _parse_list_item(self, line: str, is_ordered: bool) -> ListItem:
        if is_ordered:
            match = re.match(r'^\d+\.\s+(.+)$', line)
            text = match.group(1) if match else line
            order_match = re.match(r'^(\d+)\.', line)
            order = int(order_match.group(1)) if order_match else None
            return ListItem(text=text, order=order)
        else:
            if line.startswith('- ') or line.startswith('* '):
                text = line[2:]
            elif line.startswith('• '):
                text = line[2:]
            else:
                text = line
            return ListItem(text=text, order=None)

    def _parse_paragraph(self, text: str) -> Optional[Paragraph]:
        if not text.strip():
            return None

        pattern = r'\*\*(.+?)\*\*(.*)'
        match = re.match(pattern, text, re.DOTALL)

        if match:
            lead = match.group(1).strip()
            body = match.group(2).strip()
            return Paragraph(lead=lead, body=body)
        else:
            return Paragraph(lead="", body=text.strip())

    def render_content(
        self,
        draw: ImageDraw.Draw,
        img: Image.Image,
        data: MarkdownContent,
        y: int
    ) -> int:
        y = self.draw_main_title(draw, data.title, y)

        for para in data.paragraphs:
            y += self.context.line_spacing["paragraph"] // 2
            y = self._draw_paragraph(draw, para, y)

        if data.footnote:
            y = self._draw_footnote(draw, data.footnote, y)

        return y

    def _draw_paragraph(self, draw: ImageDraw.Draw, para: Paragraph, y: int) -> int:
        primary_color = self.context.primary_color
        text_color = self.context.text_color
        max_width = self.context.max_width
        x = PADDING["left"]

        if para.list_items:
            return self._draw_list(draw, para.list_items, para.is_ordered_list, y)

        if para.lead:
            lead_lines = wrap_text(para.lead, self.fonts.lead_text, max_width)
            lead_bbox = self.fonts.lead_text.getbbox("测")
            line_height = lead_bbox[3] - lead_bbox[1]

            for line in lead_lines:
                draw.text((x, y), line, font=self.fonts.lead_text, fill=primary_color)
                y += line_height + self.context.line_spacing["line"]

        if para.body:
            segments = self._parse_rich_text(para.body)
            _, y = self._draw_rich_text(draw, segments, x, y, max_width)

        return y

    def _draw_list(self, draw: ImageDraw.Draw, items: List[ListItem], is_ordered: bool, y: int) -> int:
        primary_color = self.context.primary_color
        max_width = self.context.max_width
        x = PADDING["left"]

        if is_ordered:
            max_num = max((item.order if item.order else (i + 1)) for i, item in enumerate(items))
            sample_bullet = f"{max_num}."
            bullet_bbox = self.fonts.body_text.getbbox(sample_bullet)
            bullet_width = bullet_bbox[2] - bullet_bbox[0] + 15
        else:
            bullet_width = 40

        for i, item in enumerate(items):
            if is_ordered:
                order_num = item.order if item.order else (i + 1)
                bullet = f"{order_num}."
            else:
                bullet = "•"

            draw.text((x, y), bullet, font=self.fonts.body_text, fill=primary_color)

            item_x = x + bullet_width
            item_max_width = max_width - bullet_width

            segments = self._parse_rich_text(item.text)
            _, y = self._draw_rich_text(draw, segments, item_x, y, item_max_width)
            y += 5

        return y

    def _parse_rich_text(self, text: str) -> List[Tuple[str, bool]]:
        result = []
        pattern = r'\*\*(.+?)\*\*'

        last_end = 0
        for match in re.finditer(pattern, text):
            if match.start() > last_end:
                normal_text = text[last_end:match.start()]
                if normal_text:
                    result.append((normal_text, False))
            result.append((match.group(1), True))
            last_end = match.end()

        if last_end < len(text):
            remaining = text[last_end:]
            if remaining:
                result.append((remaining, False))

        if not result:
            result.append((text, False))

        return result

    def _draw_rich_text(
        self,
        draw: ImageDraw.Draw,
        segments: List[Tuple[str, bool]],
        x: int,
        y: int,
        max_width: int
    ) -> Tuple[int, int]:
        primary_color = self.context.primary_color
        text_color = self.context.text_color

        current_x = x
        current_y = y
        start_x = x

        bbox = self.fonts.body_text.getbbox("测")
        line_height = bbox[3] - bbox[1] + self.context.line_spacing["line"]

        for text, is_bold in segments:
            # 粗体（**包裹）使用 body_text 字体，只改变颜色为主题色
            use_font = self.fonts.body_text
            color = primary_color if is_bold else text_color

            for char in text:
                char_bbox = use_font.getbbox(char)
                char_width = char_bbox[2] - char_bbox[0]

                if current_x + char_width > start_x + max_width:
                    current_x = start_x
                    current_y += line_height

                draw.text((current_x, current_y), char, font=use_font, fill=color)
                current_x += char_width

        return current_x, current_y + line_height

    def _draw_footnote(self, draw: ImageDraw.Draw, footnote: str, y: int) -> int:
        footnote_color = (128, 128, 128)

        footnote_lines = wrap_text(footnote, self.fonts.small_text, self.context.max_width)
        footnote_bbox = self.fonts.small_text.getbbox("测")
        line_height = footnote_bbox[3] - footnote_bbox[1] + 8

        y += 25

        for line in footnote_lines:
            line_bbox = self.fonts.small_text.getbbox(line)
            line_width = line_bbox[2] - line_bbox[0]
            x = (self.context.width - line_width) // 2
            draw.text((x, y), line, font=self.fonts.small_text, fill=footnote_color)
            y += line_height

        return y
