"""
海报生成 API
"""
import io
import base64
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response as FastAPIResponse
from app.models.schemas import PosterGenerateRequest, PosterConfig, ContentResult, Response
from app.services.poster_service import PosterService

router = APIRouter(prefix="/api/poster", tags=["海报生成"])

poster_service = PosterService()


@router.post("/generate")
async def generate_poster(request: PosterGenerateRequest) -> Response:
    """生成海报，返回 base64 图片"""
    try:
        # 生成图片
        img = poster_service.generate(request.content, request.config)
        
        # 转换为 base64
        img_bytes = poster_service.to_bytes(img, "PNG")
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        return Response(data={
            "image_base64": f"data:image/png;base64,{img_base64}",
            "width": img.width,
            "height": img.height,
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-download")
async def generate_poster_download(request: PosterGenerateRequest) -> FastAPIResponse:
    """生成海报并直接下载"""
    try:
        img = poster_service.generate(request.content, request.config)
        img_bytes = poster_service.to_bytes(img, "PNG")
        
        return FastAPIResponse(
            content=img_bytes,
            media_type="image/png",
            headers={
                "Content-Disposition": "attachment; filename=poster.png"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
