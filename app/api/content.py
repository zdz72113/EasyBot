"""
内容生成 API
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import (
    GenerateRequest, RegenerateRequest, Response,
    ContentResult, HistoryRecord
)
from app.services.ai_service import AIService
from app.services.history_service import HistoryService
from app.services.fetcher_service import FetcherService

router = APIRouter(prefix="/api/content", tags=["内容生成"])

history_service = HistoryService()
fetcher_service = FetcherService()


@router.post("/generate")
async def generate_content(request: GenerateRequest):
    """流式生成内容"""
    async def event_stream():
        ai = AIService(request.model)
        
        # 检查 URL 抓取
        web_content = None
        if fetcher_service.is_url(request.query):
            fetch_result = await fetcher_service.fetch(request.query, method="jina")
            if fetch_result.success:
                web_content = {
                    "title": fetch_result.title,
                    "content": fetch_result.content,
                    "materials": [m.model_dump() for m in fetch_result.materials]
                }
        
        full_text = ""
        async for chunk in ai.generate_stream(
            query=request.query,
            web_content=web_content
        ):
            full_text += chunk
            yield f"data: {chunk}\n\n"
        
        # 解析并保存
        result = ai.parse_result(full_text)
        record_id = history_service.save_record(request.query, result)
        
        yield f"event: complete\ndata: {record_id}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )


@router.post("/generate-sync")
async def generate_content_sync(request: GenerateRequest) -> Response:
    """同步生成内容（非流式）"""
    try:
        ai = AIService(request.model)
        
        # 检查 URL 抓取
        web_content = None
        if fetcher_service.is_url(request.query):
            fetch_result = await fetcher_service.fetch(request.query, method="jina")
            if fetch_result.success:
                web_content = {
                    "title": fetch_result.title,
                    "content": fetch_result.content,
                    "materials": [m.model_dump() for m in fetch_result.materials]
                }
        
        # 收集所有文本
        full_text = ""
        async for chunk in ai.generate_stream(
            query=request.query,
            web_content=web_content
        ):
            full_text += chunk
        
        result = ai.parse_result(full_text)
        record_id = history_service.save_record(request.query, result)
        
        return Response(data={
            "record_id": record_id,
            "result": result.model_dump()
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regenerate")
async def regenerate_content(request: RegenerateRequest):
    """重新生成内容"""
    record = history_service.get_record(request.record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    async def event_stream():
        ai = AIService(request.model)
        
        full_text = ""
        async for chunk in ai.generate_stream(
            query="",
            original_raw=record.raw,
            instruction=request.instruction
        ):
            full_text += chunk
            yield f"data: {chunk}\n\n"
        
        result = ai.parse_result(full_text)
        history_service.update_record(request.record_id, result)
        
        yield f"event: complete\ndata: {request.record_id}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )


@router.get("/history")
async def get_history(limit: int = 100) -> Response:
    """获取历史记录"""
    records = history_service.list_records(limit)
    return Response(data=[r.model_dump() for r in records])


@router.get("/history/{record_id}")
async def get_record(record_id: str) -> Response:
    """获取单条记录"""
    record = history_service.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return Response(data=record.model_dump())


@router.put("/history/{record_id}")
async def update_record(record_id: str, result: ContentResult) -> Response:
    """更新记录"""
    success = history_service.update_record(record_id, result)
    if not success:
        raise HTTPException(status_code=404, detail="记录不存在")
    return Response(message="更新成功")


@router.delete("/history/{record_id}")
async def delete_record(record_id: str) -> Response:
    """删除记录"""
    success = history_service.delete_record(record_id)
    if not success:
        raise HTTPException(status_code=404, detail="记录不存在")
    return Response(message="删除成功")
