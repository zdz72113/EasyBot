"""
配置 API
"""
from fastapi import APIRouter
from app.models.schemas import Response
from app.core.config import load_config, save_config, list_models

router = APIRouter(prefix="/api/config", tags=["配置"])


@router.get("")
async def get_config() -> Response:
    """获取配置"""
    return Response(data=load_config())


@router.post("")
async def update_config(config: dict) -> Response:
    """更新配置"""
    save_config(config)
    return Response(message="配置已保存")


@router.get("/models")
async def get_models() -> Response:
    """获取可用模型列表"""
    return Response(data=list_models())


@router.get("/templates")
async def get_templates() -> Response:
    """获取海报模板列表"""
    config = load_config()
    return Response(data=config.get("templates", {}))


@router.get("/color-schemes")
async def get_color_schemes() -> Response:
    """获取配色方案"""
    config = load_config()
    return Response(data=config.get("color_schemes", {}))
