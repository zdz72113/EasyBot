"""
Pydantic 数据模型
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


# ============ 通用响应 ============

class Response(BaseModel):
    """通用响应"""
    code: int = 0
    message: str = "success"
    data: Any = None


# ============ AI 内容生成 ============

class QAPair(BaseModel):
    """问答对"""
    q: str
    a: str


class ContentResult(BaseModel):
    """内容生成结果"""
    title: str
    qa_list: List[QAPair]
    summary: str
    tags: List[str]
    raw: str


class GenerateRequest(BaseModel):
    """内容生成请求"""
    query: str
    model: Optional[str] = None
    use_search: bool = True


class RegenerateRequest(BaseModel):
    """重新生成请求"""
    record_id: str
    instruction: str
    model: Optional[str] = None


# ============ 历史记录 ============

class HistoryRecord(BaseModel):
    """历史记录"""
    id: str
    query: str
    title: str
    qa_list: List[QAPair]
    summary: str
    tags: List[str]
    raw: str
    created_at: str


# ============ 素材抓取 ============

class FetchRequest(BaseModel):
    """素材抓取请求"""
    url: str
    method: str = "auto"  # auto, jina, firecrawl, basic


class Material(BaseModel):
    """素材项"""
    type: str  # text, image, link, video
    content: str
    url: Optional[str] = None
    title: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class FetchResult(BaseModel):
    """素材抓取结果"""
    url: str
    title: str
    content: str
    materials: List[Material]
    success: bool
    error: Optional[str] = None


class MaterialDimension(BaseModel):
    """基于内容问答拆分的素材维度"""
    dimension_id: str
    title: str
    question: str
    answer: str
    keywords: List[str] = Field(default_factory=list)
    image_prompt: str = ""


class DimensionMaterialResult(MaterialDimension):
    """单个维度对应的素材生成结果"""
    images: List[Material] = Field(default_factory=list)
    videos: List[Material] = Field(default_factory=list)
    generated_image: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class MaterialGenerateRequest(BaseModel):
    """按内容生成维度素材请求"""
    content: ContentResult
    image_limit: int = 5
    video_limit: int = 3
    generate_simple_image: bool = True


class MaterialGenerateResult(BaseModel):
    """按内容生成维度素材结果"""
    title: str
    dimensions: List[DimensionMaterialResult]


# ============ 海报生成 ============

class PosterConfig(BaseModel):
    """海报配置"""
    model_config = ConfigDict(populate_by_name=True)

    template: str = "知识科普"
    color_scheme: str = Field(default="经典红", alias="colorScheme")
    header_title: str = Field(default="知识科普", alias="headerTitle")
    header_subtitle: str = Field(default="KNOWLEDGE", alias="headerSubtitle")
    header_tag: str = Field(default="本周热评", alias="headerTag")
    body_text_size: int = Field(default=34, alias="bodyTextSize")
    paragraph_spacing: int = Field(default=50, alias="paragraphSpacing")
    line_spacing: int = Field(default=15, alias="lineSpacing")
    background_image: Optional[str] = Field(default=None, alias="backgroundImage")


class PosterGenerateRequest(BaseModel):
    """海报生成请求"""
    content: ContentResult
    config: PosterConfig


# ============ 视频生成 ============

class VideoConfig(BaseModel):
    """视频配置"""
    audio_path: Optional[str] = None
    duration: int = 30
    resolution: str = "9:16"  # 9:16, 16:9, 1:1
    subtitle_style: Optional[Dict[str, Any]] = None


class VideoGenerateRequest(BaseModel):
    """视频生成请求"""
    poster_image: str  # base64 或路径
    config: VideoConfig


class SubtitleSegment(BaseModel):
    """字幕片段"""
    text: str
    start: float
    end: float


class SubtitleGenerateRequest(BaseModel):
    """字幕生成请求"""
    audio_path: str
    language: str = "zh"
