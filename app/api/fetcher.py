"""
素材抓取 API
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import FetchRequest, Response
from app.services.fetcher_service import FetcherService

router = APIRouter(prefix="/api/fetcher", tags=["素材抓取"])

fetcher_service = FetcherService()


@router.post("/fetch")
async def fetch_url(request: FetchRequest) -> Response:
    """抓取网页素材"""
    try:
        result = await fetcher_service.fetch(request.url, request.method)
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)
        return Response(data=result.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check-url")
async def check_url(url: str) -> Response:
    """检查是否为有效 URL"""
    is_valid = fetcher_service.is_url(url)
    return Response(data={"is_url": is_valid})
