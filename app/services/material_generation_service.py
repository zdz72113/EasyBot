"""
基于内容（Q1-Q5）生成视频素材的编排服务

每个 QA 视为一个素材维度，输出：
- keywords：用于图片/视频搜索的关键词
- image_prompt：用于 AI 生图的提示词（首版仅作为元数据，便于后续接入 AI 生图）
- images / videos：从 FetcherService 多源搜索的候选素材
- generated_image：使用 PIL 渲染的简单视觉卡片（base64），保证无外部素材时也有兜底图
"""
from __future__ import annotations

import asyncio
import base64
import io
import re
from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont

from app.models.schemas import (
    ContentResult,
    DimensionMaterialResult,
    Material,
    MaterialGenerateResult,
    QAPair,
)
from app.services.fetcher_service import FetcherService


_STOPWORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
    "没有", "看", "好", "自己", "这", "那", "如何", "什么", "怎么", "为什么",
    "可以", "因为", "所以", "但是", "如果", "通过", "我们", "他们", "它们",
    "对", "与", "及", "或", "等", "等等", "进行", "已经", "将", "把", "被",
    "由", "让", "使", "对于", "关于", "包括", "需要", "能够", "可能", "应该",
    "the", "a", "an", "of", "to", "in", "and", "or", "for", "is", "are",
    "was", "were", "be", "been", "with", "on", "at", "by", "as", "from",
    "this", "that", "it", "you", "we", "they", "i", "he", "she", "what",
    "how", "why", "when", "where", "which", "who",
}


def _strip_punct(text: str) -> str:
    return re.sub(r"[\s\u3000\u00a0]+", " ", re.sub(r"[\W_]+", " ", text or "", flags=re.UNICODE)).strip()


def _tokenize(text: str) -> List[str]:
    """非常轻量的中英文混合分词：英文按词切，中文按 2-4 字滑窗候选。"""
    text = _strip_punct(text)
    if not text:
        return []

    tokens: List[str] = []
    en_words = re.findall(r"[A-Za-z][A-Za-z0-9_-]+", text)
    tokens.extend(w.lower() for w in en_words if len(w) >= 2)

    zh_segments = re.findall(r"[\u4e00-\u9fff]+", text)
    for seg in zh_segments:
        if len(seg) <= 4:
            tokens.append(seg)
            continue
        for size in (4, 3, 2):
            if len(seg) < size:
                continue
            for i in range(0, len(seg) - size + 1):
                tokens.append(seg[i:i + size])

    return tokens


def extract_keywords(
    text: str,
    extra_anchors: Optional[List[str]] = None,
    limit: int = 5,
) -> List[str]:
    """从文本中提取关键词，结合外部 anchor（标题、标签）做加权。"""
    extra_anchors = [a for a in (extra_anchors or []) if a]
    tokens = _tokenize(text)
    if not tokens and not extra_anchors:
        return []

    scores: dict[str, float] = {}
    for tok in tokens:
        if tok in _STOPWORDS or len(tok) < 2:
            continue
        weight = 1.0
        if re.fullmatch(r"[\u4e00-\u9fff]+", tok):
            weight += min(len(tok), 4) * 0.3
        scores[tok] = scores.get(tok, 0.0) + weight

    for anchor in extra_anchors:
        clean = anchor.lstrip("#").strip()
        if not clean:
            continue
        scores[clean] = scores.get(clean, 0.0) + 3.0

    if not scores:
        return [a.lstrip("#").strip() for a in extra_anchors[:limit] if a.strip()]

    ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    selected: List[str] = []
    for word, _ in ordered:
        if any(word != other and word in other for other in selected):
            continue
        selected = [s for s in selected if not (s != word and s in word)]
        if word not in selected:
            selected.append(word)
        if len(selected) >= limit:
            break

    return selected


def build_image_prompt(
    title: str,
    question: str,
    answer: str,
    keywords: List[str],
) -> str:
    """构造适合 AI 生图的中文提示词。"""
    keyword_part = "、".join(keywords[:5]) if keywords else question or title
    answer_snippet = (answer or "").strip().replace("\n", " ")
    if len(answer_snippet) > 60:
        answer_snippet = answer_snippet[:60] + "…"

    return (
        f"主题：{title or question}；"
        f"画面要点：{question}；"
        f"信息要点：{answer_snippet}；"
        f"关键词：{keyword_part}；"
        "风格：现代信息图、简洁专业、扁平插画、明亮配色、9:16 竖屏构图、留白充足、避免文字"
    )


class MaterialGenerationService:
    """素材生成编排服务"""

    PALETTE = [
        ("#0F172A", "#F8FAFC", "#22D3EE"),
        ("#1E293B", "#FEF3C7", "#F97316"),
        ("#7C2D12", "#FFF7ED", "#FACC15"),
        ("#064E3B", "#ECFDF5", "#34D399"),
        ("#1E3A8A", "#EFF6FF", "#60A5FA"),
        ("#3B0764", "#F5F3FF", "#A855F7"),
    ]

    def __init__(self, fetcher: Optional[FetcherService] = None):
        self.fetcher = fetcher or FetcherService()
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.font_dir = self.base_dir / "fonts"

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        font_paths = [
            self.font_dir / "NotoSansSC-Bold.ttf",
            self.font_dir / "SourceHanSansSC-Bold.ttf",
            Path("C:/Windows/Fonts/msyhbd.ttc"),
            Path("C:/Windows/Fonts/msyh.ttc"),
            Path("C:/Windows/Fonts/simhei.ttf"),
            Path("C:/Windows/Fonts/simsun.ttc"),
        ]
        for path in font_paths:
            try:
                if path and Path(path).exists():
                    return ImageFont.truetype(str(path), size)
            except Exception:
                continue
        return ImageFont.load_default()

    def _wrap(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
        if not text:
            return []
        lines: List[str] = []
        current = ""
        for ch in text:
            test = current + ch
            if font.getbbox(test)[2] > max_width and current:
                lines.append(current)
                current = ch
            else:
                current = test
        if current:
            lines.append(current)
        return lines

    def render_simple_image(
        self,
        index: int,
        title: str,
        headline: str,
        keywords: List[str],
        footer: str = "EasyBot",
    ) -> str:
        """生成 9:16 视觉卡片，返回 data URL。"""
        width, height = 1080, 1920
        bg, fg, accent = self.PALETTE[index % len(self.PALETTE)]

        img = Image.new("RGB", (width, height), bg)
        draw = ImageDraw.Draw(img)

        for y in range(height):
            ratio = y / height
            r1, g1, b1 = int(bg[1:3], 16), int(bg[3:5], 16), int(bg[5:7], 16)
            r2, g2, b2 = int(accent[1:3], 16), int(accent[3:5], 16), int(accent[5:7], 16)
            r = int(r1 + (r2 - r1) * ratio * 0.35)
            g = int(g1 + (g2 - g1) * ratio * 0.35)
            b = int(b1 + (b2 - b1) * ratio * 0.35)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        margin = 96
        draw.rectangle([margin, margin, margin + 96, margin + 12], fill=accent)

        font_index = self._get_font(72)
        font_title = self._get_font(56)
        font_headline = self._get_font(72)
        font_chip = self._get_font(34)
        font_footer = self._get_font(28)

        index_text = f"0{index + 1}" if index < 9 else f"{index + 1}"
        draw.text((margin, margin + 28), index_text, font=font_index, fill=accent)

        y = margin + 28 + font_index.getbbox(index_text)[3] + 24
        title_text = title or headline
        for line in self._wrap(title_text, font_title, width - margin * 2)[:2]:
            draw.text((margin, y), line, font=font_title, fill=fg)
            y += font_title.getbbox(line)[3] + 12

        y += 36
        for line in self._wrap(headline, font_headline, width - margin * 2)[:4]:
            draw.text((margin, y), line, font=font_headline, fill=fg)
            y += font_headline.getbbox(line)[3] + 18

        chip_y = height - margin - 220
        chip_x = margin
        for kw in keywords[:6]:
            label = f"#{kw}"
            tw = font_chip.getbbox(label)[2] + 32
            th = font_chip.getbbox(label)[3] + 18
            if chip_x + tw > width - margin:
                chip_x = margin
                chip_y += th + 14
            draw.rounded_rectangle(
                [chip_x, chip_y, chip_x + tw, chip_y + th],
                radius=th // 2,
                outline=accent,
                width=2,
            )
            draw.text((chip_x + 16, chip_y + 6), label, font=font_chip, fill=accent)
            chip_x += tw + 14

        draw.text((margin, height - margin), footer, font=font_footer, fill=fg)

        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"

    async def _build_dimension(
        self,
        index: int,
        qa: QAPair,
        title: str,
        tags: List[str],
        image_limit: int,
        video_limit: int,
        generate_simple_image: bool,
    ) -> DimensionMaterialResult:
        keywords = extract_keywords(
            f"{qa.q} {qa.a}",
            extra_anchors=([title] if title else []) + tags,
            limit=6,
        )
        image_prompt = build_image_prompt(title, qa.q, qa.a, keywords)

        warnings: List[str] = []
        images: List[Material] = []
        videos: List[Material] = []

        search_query = " ".join(keywords[:3]) or qa.q or title
        if search_query:
            try:
                images = await self.fetcher.search_images(search_query, limit=image_limit)
            except Exception as exc:
                warnings.append(f"图片搜索失败：{exc}")

            try:
                videos = await self.fetcher.search_videos(search_query, limit=video_limit)
            except Exception as exc:
                warnings.append(f"视频搜索失败：{exc}")

        generated_image = None
        if generate_simple_image:
            try:
                generated_image = self.render_simple_image(
                    index=index,
                    title=title,
                    headline=qa.q or qa.a[:40],
                    keywords=keywords,
                    footer=title or "EasyBot",
                )
            except Exception as exc:
                warnings.append(f"简单图片生成失败：{exc}")

        return DimensionMaterialResult(
            dimension_id=f"q{index + 1}",
            title=f"Q{index + 1} · {qa.q}" if qa.q else f"Q{index + 1}",
            question=qa.q,
            answer=qa.a,
            keywords=keywords,
            image_prompt=image_prompt,
            images=images,
            videos=videos,
            generated_image=generated_image,
            warnings=warnings,
        )

    async def generate(
        self,
        content: ContentResult,
        image_limit: int = 5,
        video_limit: int = 3,
        generate_simple_image: bool = True,
    ) -> MaterialGenerateResult:
        title = content.title or ""
        tags = content.tags or []
        qa_list = [qa for qa in (content.qa_list or []) if (qa.q or qa.a)]

        tasks = [
            self._build_dimension(
                index=i,
                qa=qa,
                title=title,
                tags=tags,
                image_limit=image_limit,
                video_limit=video_limit,
                generate_simple_image=generate_simple_image,
            )
            for i, qa in enumerate(qa_list)
        ]

        dimensions = await asyncio.gather(*tasks) if tasks else []
        return MaterialGenerateResult(title=title, dimensions=list(dimensions))
