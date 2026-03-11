"""
EasyBot 配置：静态默认值 + config.json 读写（模型、模板、海报、视频）。
"""

import json
import os
import shutil
import sys
from typing import Optional


def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()
ICONS_DIR = os.path.join(BASE_DIR, "icons")

# ========== AI 模型配置 ==========

AI_MODELS = {
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "api_key": "",
        "model": "deepseek-chat",
        "supports_search": True,
    },
    "qwen": {
        "name": "通义千问",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": "",
        "model": "qwen-plus",
        "supports_search": True,
    },
}

SYSTEM_PROMPT = """你是一个专业的知识科普内容创作者。你的任务是将用户提供的主题、文字或文章内容，整理成"5个问题看懂[主题]"的格式。

请严格按照以下格式输出：

【标题】5个问题看懂XXX
【Q1】第一个问题？
【A1】第一个问题的回答，要求通俗易懂、数据准确。可以使用Markdown格式（加粗）来增强可读性。
【Q2】第二个问题？
【A2】第二个问题的回答
【Q3】第三个问题？
【A3】第三个问题的回答
【Q4】第四个问题？
【A4】第四个问题的回答
【Q5】第五个问题？
【A5】第五个问题的回答
【简介】一段15-30字的简短介绍，适合做视频简介
【标签】#标签1 #标签2 #标签3

要求：
1. 问题要由浅入深，从"是什么"到"为什么"再到"怎么办"
2. 回答要通俗易懂，避免过于专业的术语
3. 每个回答控制在50-70字
4. 数据和事实要准确，如有需要请利用联网搜索获取最新信息
5. 标签2-3个，以#开头，与主题相关
6. 不要输出任何格式标记以外的内容"""

# ========== 配色方案（复用 Old） ==========

COLOR_SCHEMES = {
    "经典红": {
        "name": "经典红",
        "primary": "#C41E24",
        "text": "#1A1A1A",
        "title": "#1A1A1A",
        "background": "#FDF8F5",
        "accent": "#8B0000",
        "header_bg": "#FFFFFF",
    },
    "墨绿": {
        "name": "墨绿",
        "primary": "#2D5A4A",
        "text": "#1A1A1A",
        "title": "#1A1A1A",
        "background": "#F5F9F7",
        "accent": "#1E3D32",
        "header_bg": "#FFFFFF",
    },
    "藏蓝": {
        "name": "藏蓝",
        "primary": "#1E3A5F",
        "text": "#2C2C2C",
        "title": "#1A1A1A",
        "background": "#F5F8FA",
        "accent": "#0D2137",
        "header_bg": "#FFFFFF",
    },
    "琥珀金": {
        "name": "琥珀金",
        "primary": "#B8860B",
        "text": "#3D3D3D",
        "title": "#2A2A2A",
        "background": "#FFFEF5",
        "accent": "#8B6508",
        "header_bg": "#FFFFFF",
    },
    "典雅紫": {
        "name": "典雅紫",
        "primary": "#6B4C9A",
        "text": "#2D2D2D",
        "title": "#1A1A1A",
        "background": "#F9F7FC",
        "accent": "#4A3570",
        "header_bg": "#FFFFFF",
    },
}

# ========== 尺寸与排版 ==========

DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1920

PADDING = {
    "left": 80,
    "right": 80,
    "top": 100,
    "bottom": 80,
}

FONT_SIZES = {
    "header_title": 110,
    "header_subtitle": 36,
    "header_tag": 42,
    "main_title": 52,
    "lead_text": 38,
    "body_text": 36,
    "footer_tag": 24,
}

LINE_SPACING = {
    "paragraph": 50,
    "line": 15,
}

# ========== 头部/底部配置 ==========

HEADER_CONFIG = {
    "title": "时代周刊",
    "subtitle": "TIMES WEEK",
    "tag": "本周热评",
    "height": 250,
}

FOOTER_CONFIG = {
    "show_banner": True,
    "banner_text": "车骑观察 Insights",
    "banner_height": 50,
    "slant_width": 30,
    "font_size": 28,
}

# ========== 视频配置 ==========

VIDEO_CONFIG = {
    "audio_dir": os.path.join(BASE_DIR, "audio"),
    "output_dir": os.path.join(BASE_DIR, "output"),
    "duration_options": [5, 10, 15, 20],
    "default_duration": 10,
    "fps": 24,
    "codec": "libx264",
    "audio_codec": "aac",
}

# ========== 预设模板 ==========

PRESET_TEMPLATES = {
    "自定义": {
        "name": "自定义",
        "description": "使用自定义配置",
        "color_scheme": "经典红",
        "header": {
            "title": "时代周刊",
            "subtitle": "TIMES WEEK",
            "tag": "本周热评",
            "height": 250,
        },
        "footer": {
            "show_banner": True,
            "banner_text": "车骑观察 Insights",
            "banner_height": 50,
            "slant_width": 30,
            "font_size": 28,
        },
        "icon": None,
    },
    "社会数据": {
        "name": "社会数据",
        "description": "社会数据",
        "color_scheme": "经典红",
        "header": {
            "title": "社会观察",
            "subtitle": "SOCIAL INSIGHTS",
            "tag": "数据洞察",
            "height": 250,
        },
        "footer": {
            "show_banner": False,
            "banner_text": "车骑观察 Insights",
            "banner_height": 50,
            "slant_width": 30,
            "font_size": 28,
        },
        "icon": None,
    },
    "国家纵览": {
        "name": "国家纵览",
        "description": "国际观察",
        "color_scheme": "经典红",
        "header": {
            "title": "国际观察",
            "subtitle": "GLOBAL INSIGHTS",
            "tag": "国家纵览",
            "height": 250,
        },
        "footer": {
            "show_banner": False,
            "banner_text": "车骑观察 Insights",
            "banner_height": 50,
            "slant_width": 30,
            "font_size": 28,
        },
        "icon": None,
    },
    "知识科普": {
        "name": "知识科普",
        "description": "知识科普",
        "color_scheme": "经典红",
        "header": {
            "title": "社会观察",
            "subtitle": "SOCIAL INSIGHTS",
            "tag": "知识科普",
            "height": 250,
        },
        "footer": {
            "show_banner": False,
            "banner_text": "车骑观察 Insights",
            "banner_height": 50,
            "slant_width": 30,
            "font_size": 28,
        },
        "icon": None,
    },
    "人民日报": {
        "name": "人民日报",
        "description": "人民日报风格 - 庄重大气的红色主题",
        "color_scheme": "经典红",
        "header": {
            "title": "人民日报",
            "subtitle": "PEOPLE'S DAILY",
            "tag": "热点聚焦",
            "height": 250,
        },
        "footer": {
            "show_banner": True,
            "banner_text": "人民日报 评论",
            "banner_height": 50,
            "slant_width": 30,
            "font_size": 28,
        },
        "icon": os.path.join(ICONS_DIR, "people_daily.png"),
    },
    "哈佛大学": {
        "name": "哈佛大学",
        "description": "Harvard 风格 - 深红学术主题",
        "color_scheme": "经典红",
        "header": {
            "title": "哈佛大学",
            "subtitle": "HARVARD UNIVERSITY",
            "tag": "学术前沿",
            "height": 250,
        },
        "footer": {
            "show_banner": True,
            "banner_text": "Harvard Academic",
            "banner_height": 50,
            "slant_width": 30,
            "font_size": 28,
        },
        "icon": os.path.join(ICONS_DIR, "harvard.jpeg"),
    },
    "路透社": {
        "name": "路透社",
        "description": "Reuters 风格 - 专业新闻橙色主题",
        "color_scheme": "经典红",
        "header": {
            "title": "路透社",
            "subtitle": "REUTERS",
            "tag": "全球资讯",
            "height": 250,
        },
        "footer": {
            "show_banner": True,
            "banner_text": "Reuters News",
            "banner_height": 50,
            "slant_width": 30,
            "font_size": 28,
        },
        "icon": os.path.join(ICONS_DIR, "reuters.jpg"),
    },
    "金融时报": {
        "name": "金融时报",
        "description": "Financial Times 风格 - 粉色商业主题",
        "color_scheme": "琥珀金",
        "header": {
            "title": "金融时报",
            "subtitle": "FINANCIAL TIMES",
            "tag": "财经观察",
            "height": 250,
        },
        "footer": {
            "show_banner": True,
            "banner_text": "FT Analysis",
            "banner_height": 50,
            "slant_width": 30,
            "font_size": 28,
        },
        "icon": os.path.join(ICONS_DIR, "ft.png"),
    }
}

# ========== 历史记录配置 ==========

HISTORY_DIR = os.path.join(BASE_DIR, "history")
HISTORY_MAX_RECORDS = 100

# ========== config.json 读写（用户配置：模型、模板、海报、视频） ==========

_CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
_CONFIG_EXAMPLE_PATH = os.path.join(BASE_DIR, "config_example.json")


def _config_load() -> dict:
    path = _CONFIG_PATH
    if not os.path.exists(path):
        example = _CONFIG_EXAMPLE_PATH
        if os.path.exists(example):
            try:
                shutil.copy2(example, path)
            except (IOError, OSError):
                pass
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _config_save(data: dict) -> None:
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_ai_models() -> dict:
    return _config_load().get("llm_models", {})


def get_color_schemes() -> dict:
    return _config_load().get("color_schemes", {})


def get_preset_templates() -> dict:
    return _config_load().get("templates", {})


def load_model() -> Optional[dict]:
    d = _config_load()
    llm = d.get("llm_models", {})
    name = d.get("selectModel", "")
    preset = next((k for k, v in llm.items() if v.get("name") == name), list(llm.keys())[0] if llm else "自定义")
    m = llm.get(preset, {})
    api_keys = {}
    for k in llm:
        api_keys["custom" if k == "自定义" else k] = llm[k].get("api_key", "")
    return {
        "preset": preset,
        "api_url": m.get("base_url", ""),
        "model_name": m.get("model", ""),
        "api_keys": api_keys,
    }


def save_model(preset: str, api_url: str, model_name: str, api_keys: dict) -> None:
    data = _config_load()
    llm = data.setdefault("llm_models", {})
    if preset in llm:
        llm[preset]["name"] = llm[preset].get("name", preset)
        llm[preset]["base_url"] = api_url
        llm[preset]["model"] = model_name
    data["selectModel"] = llm.get(preset, {}).get("name", preset)
    for k, v in api_keys.items():
        key = "自定义" if k == "custom" else k
        if key in llm:
            llm[key]["api_key"] = v
    _config_save(data)


def load_poster() -> Optional[dict]:
    d = _config_load()
    t = d.get("selectTemplate", "")
    templates = d.get("templates", {})
    sel = templates.get(t, {})
    h = sel.get("header", {})
    return {
        "template": t or (list(templates.keys())[0] if templates else ""),
        "template_select": t or (list(templates.keys())[0] if templates else ""),
        "color_scheme": sel.get("color_scheme", "经典红"),
        "header_title": h.get("title", ""),
        "header_subtitle": h.get("subtitle", ""),
        "header_tag": h.get("tag", ""),
    }


def save_poster(template: str, template_select: str, color_scheme: str, header_title: str, header_subtitle: str, header_tag: str) -> None:
    data = _config_load()
    tkey = template_select or template
    data["selectTemplate"] = tkey
    templates = data.setdefault("templates", {})
    if tkey not in templates:
        templates[tkey] = {}
    templates[tkey]["color_scheme"] = color_scheme
    if "header" not in templates[tkey]:
        templates[tkey]["header"] = {}
    templates[tkey]["header"]["title"] = header_title
    templates[tkey]["header"]["subtitle"] = header_subtitle
    templates[tkey]["header"]["tag"] = header_tag
    _config_save(data)


def load_video() -> Optional[dict]:
    return _config_load().get("video")


def save_video(audio_name: Optional[str], duration: int) -> None:
    data = _config_load()
    data["video"] = {"audio_name": audio_name or "", "duration": duration}
    _config_save(data)
