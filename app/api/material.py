"""
素材生成 API：基于内容（Q1-Q5）按维度生成关键词、提示词、图片/视频候选与简单图片
"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import MaterialGenerateRequest, Response
from app.services.material_generation_service import MaterialGenerationService

router = APIRouter(prefix="/api/materials", tags=["素材生成"])

material_service = MaterialGenerationService()


@router.post("/generate-from-content")
async def generate_from_content(request: MaterialGenerateRequest) -> Response:
    """根据 ContentResult 的 QA 列表生成维度素材。"""
    if not request.content or not request.content.qa_list:
        raise HTTPException(status_code=400, detail="内容缺少 QA 列表")

    try:
        result = await material_service.generate(
            content=request.content,
            image_limit=max(1, min(request.image_limit, 12)),
            video_limit=max(0, min(request.video_limit, 6)),
            generate_simple_image=request.generate_simple_image,
        )
        return Response(data=result.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
