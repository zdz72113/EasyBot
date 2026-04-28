"""
视频生成 API
"""
import io
import base64
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from PIL import Image
from app.models.schemas import VideoGenerateRequest, VideoConfig, SubtitleGenerateRequest, Response
from app.services.video_service import VideoService
from app.services.history_service import HistoryService

router = APIRouter(prefix="/api/video", tags=["视频生成"])

video_service = VideoService()
history_service = HistoryService()


def decode_base64_image(base64_string: str) -> Image.Image:
    """解码 base64 图片"""
    if base64_string.startswith("data:image"):
        base64_string = base64_string.split(",")[1]
    
    img_bytes = base64.b64decode(base64_string)
    return Image.open(io.BytesIO(img_bytes))


@router.get("/audio-list")
async def get_audio_list() -> Response:
    """获取可用音频列表"""
    audio_files = video_service.get_available_audio()
    return Response(data=[
        {"name": name, "path": path}
        for name, path in audio_files
    ])


@router.post("/generate")
async def generate_video(request: VideoGenerateRequest) -> Response:
    """生成视频"""
    try:
        # 解码图片
        poster_image = decode_base64_image(request.poster_image)
        
        # 生成视频
        output_path = await video_service.generate_video(
            poster_image=poster_image,
            audio_path=request.config.audio_path,
            duration=request.config.duration,
        )
        
        return Response(data={
            "video_path": output_path,
            "download_url": f"/api/video/download?path={output_path}"
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download")
async def download_video(path: str):
    """下载视频文件"""
    if not Path(path).exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path,
        media_type="video/mp4",
        filename="video.mp4"
    )


@router.post("/subtitles/generate")
async def generate_subtitles(audio: UploadFile = File(...)) -> Response:
    """从音频文件生成字幕"""
    try:
        # 保存临时音频文件
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(await audio.read())
            tmp_path = tmp.name
        
        # 生成字幕
        subtitles = await video_service.generate_subtitles_from_audio(tmp_path)
        
        # 清理临时文件
        Path(tmp_path).unlink(missing_ok=True)
        
        return Response(data=subtitles)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-with-subtitles")
async def generate_video_with_subtitles(
    poster_image: str,
    audio_path: str,
    subtitles: list
):
    """生成带字幕的视频（进阶功能）"""
    try:
        poster_img = decode_base64_image(poster_image)
        
        output_path = await video_service.generate_with_subtitles(
            poster_image=poster_img,
            audio_path=audio_path,
            subtitles=subtitles,
        )
        
        return Response(data={
            "video_path": output_path,
            "download_url": f"/api/video/download?path={output_path}"
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
