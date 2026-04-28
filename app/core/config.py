"""
核心配置模块
"""
import json
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CONFIG_PATH = DATA_DIR / "config.json"


class Settings(BaseSettings):
    """应用配置"""
    APP_NAME: str = "EasyBot"
    DEBUG: bool = True
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:5173", "http://127.0.0.1:5173"]
    
    # 文件路径
    AUDIO_DIR: Path = BASE_DIR / "audio"
    OUTPUT_DIR: Path = BASE_DIR / "output"
    HISTORY_DIR: Path = DATA_DIR / "history"
    
    class Config:
        env_file = ".env"


settings = Settings()

# 确保目录存在
settings.HISTORY_DIR.mkdir(exist_ok=True)
settings.OUTPUT_DIR.mkdir(exist_ok=True)


# ============ 配置读写 ============

def load_config() -> dict:
    """加载配置文件"""
    if not CONFIG_PATH.exists():
        return get_default_config()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return get_default_config()


def save_config(data: dict) -> None:
    """保存配置文件"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_default_config() -> dict:
    """默认配置"""
    return {
        "llm_models": {
            "deepseek": {
                "name": "DeepSeek",
                "base_url": "https://api.deepseek.com/v1",
                "model": "deepseek-chat",
                "api_key": "",
                "supports_search": True
            },
            "qwen": {
                "name": "通义千问",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "model": "qwen-plus",
                "api_key": "",
                "supports_search": True
            }
        },
        "select_model": "deepseek",
        "templates": {
            "社会数据": {
                "name": "社会数据",
                "color_scheme": "经典红",
                "header": {"title": "社会观察", "subtitle": "SOCIAL INSIGHTS", "tag": "数据洞察"}
            },
            "知识科普": {
                "name": "知识科普",
                "color_scheme": "经典红",
                "header": {"title": "知识科普", "subtitle": "KNOWLEDGE", "tag": "知识科普"}
            }
        },
        "color_schemes": {
            "经典红": {
                "primary": "#C41E24",
                "background": "#FDF8F5",
                "text": "#1A1A1A"
            },
            "墨绿": {
                "primary": "#2D5A4A",
                "background": "#F5F9F7",
                "text": "#1A1A1A"
            }
        },
        "fetcher": {
            "jina_api_key": "",
            "firecrawl_api_key": ""
        }
    }


# ============ AI 模型配置 ============

def get_model_config(model_name: Optional[str] = None) -> dict:
    """获取模型配置"""
    config = load_config()
    models = config.get("llm_models", {})
    
    if model_name and model_name in models:
        return models[model_name]
    
    # 返回默认模型
    default = config.get("select_model", "deepseek")
    return models.get(default, models.get("deepseek", {}))


def list_models() -> dict:
    """列出所有可用模型"""
    config = load_config()
    return config.get("llm_models", {})


# ============ 素材抓取配置 ============

def get_fetcher_config() -> dict:
    """获取素材抓取配置"""
    config = load_config()
    return config.get("fetcher", {})
