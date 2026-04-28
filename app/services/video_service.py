"""
视频生成服务
使用 moviepy 合成视频
"""
import os
import tempfile
from pathlib import Path
from typing import Optional, List, Tuple
from PIL import Image
from app.core.config import settings


class VideoService:
    """视频生成服务"""
    
    def __init__(self):
        self.output_dir = settings.OUTPUT_DIR
        self.output_dir.mkdir(exist_ok=True)
        self.audio_dir = settings.AUDIO_DIR
    
    def get_available_audio(self) -> List[Tuple[str, str]]:
        """获取可用音频文件列表"""
        audio_files = []
        if not self.audio_dir.exists():
            return audio_files
        
        extensions = {'.mp3', '.wav', '.ogg', '.m4a', '.flac'}
        
        for file in sorted(self.audio_dir.iterdir()):
            if file.is_file() and file.suffix.lower() in extensions:
                audio_files.append((file.stem, str(file)))
        
        return audio_files
    
    def resize_to_9_16(self, image: Image.Image) -> Image.Image:
        """调整图片为 9:16 比例"""
        target_ratio = 9 / 16
        orig_w, orig_h = image.size
        current_ratio = orig_w / orig_h
        
        if abs(current_ratio - target_ratio) < 0.01:
            return image
        
        # 计算新尺寸
        if current_ratio > target_ratio:
            # 太宽，以宽度为准
            new_w = orig_w
            new_h = int(orig_w / target_ratio)
        else:
            # 太高，以高度为准
            new_h = orig_h
            new_w = int(orig_h * target_ratio)
        
        # 创建新图
        bg_color = image.getpixel((0, 0))
        new_img = Image.new('RGB', (new_w, new_h), bg_color)
        
        # 居中粘贴
        x = (new_w - orig_w) // 2
        y = (new_h - orig_h) // 2
        new_img.paste(image, (x, y))
        
        return new_img
    
    async def generate_video(
        self,
        poster_image: Image.Image,
        audio_path: Optional[str],
        duration: int,
        output_path: Optional[str] = None
    ) -> str:
        """
        生成视频
        
        Args:
            poster_image: 海报图片
            audio_path: 音频路径（None则无背景音乐）
            duration: 视频时长（秒）
            output_path: 输出路径（可选）
        
        Returns:
            输出文件路径
        """
        from moviepy import ImageClip, AudioFileClip, concatenate_audioclips
        
        # 生成输出路径
        if output_path is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.output_dir / f"video_{timestamp}.mp4")
        
        # 调整图片比例并保存临时文件
        poster_image = self.resize_to_9_16(poster_image)
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            temp_path = tmp.name
            poster_image.save(temp_path, 'PNG')
        
        try:
            # 创建视频片段
            image_clip = ImageClip(temp_path, duration=duration)
            
            # 添加音频
            if audio_path and os.path.exists(audio_path):
                audio_clip = AudioFileClip(audio_path)
                
                # 调整音频长度
                if audio_clip.duration > duration:
                    audio_clip = audio_clip.subclipped(0, duration)
                elif audio_clip.duration < duration:
                    # 循环音频
                    loops = int(duration / audio_clip.duration) + 1
                    audio_clip = concatenate_audioclips([audio_clip] * loops)
                    audio_clip = audio_clip.subclipped(0, duration)
                
                final_clip = image_clip.with_audio(audio_clip)
            else:
                final_clip = image_clip
            
            # 写入视频
            final_clip.write_videofile(
                output_path,
                fps=24,
                codec="libx264",
                audio_codec="aac",
                logger=None,
            )
            
            # 清理
            final_clip.close()
            image_clip.close()
            if audio_path:
                audio_clip.close()
            
            return output_path
            
        finally:
            # 删除临时图片
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    async def generate_with_subtitles(
        self,
        poster_image: Image.Image,
        audio_path: str,
        subtitles: List[dict],
        output_path: Optional[str] = None
    ) -> str:
        """
        生成带字幕的视频（进阶功能）
        
        Args:
            poster_image: 海报图片
            audio_path: 配音音频路径
            subtitles: 字幕列表 [{"text": "...", "start": 0.0, "end": 3.0}, ...]
            output_path: 输出路径
        
        Returns:
            输出文件路径
        """
        from moviepy import (
            ImageClip, AudioFileClip, TextClip,
            CompositeVideoClip, concatenate_videoclips
        )
        
        if output_path is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.output_dir / f"video_sub_{timestamp}.mp4")
        
        # 准备图片
        poster_image = self.resize_to_9_16(poster_image)
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            temp_path = tmp.name
            poster_image.save(temp_path, 'PNG')
        
        try:
            # 音频时长
            audio = AudioFileClip(audio_path)
            duration = audio.duration
            
            # 基础视频
            base_clip = ImageClip(temp_path, duration=duration)
            
            # 创建字幕片段
            subtitle_clips = []
            for sub in subtitles:
                # 字幕样式
                txt_clip = TextClip(
                    sub["text"],
                    fontsize=36,
                    color="white",
                    font="SimHei",
                    bg_color="rgba(0,0,0,0.6)",
                    method="caption",
                    size=(800, None),
                )
                
                # 位置和时长
                txt_clip = txt_clip.with_position(("center", 0.85), relative=True)
                txt_clip = txt_clip.with_start(sub["start"]).with_end(sub["end"])
                
                subtitle_clips.append(txt_clip)
            
            # 合成
            final = CompositeVideoClip(
                [base_clip] + subtitle_clips,
                size=base_clip.size
            )
            final = final.with_audio(audio)
            
            # 输出
            final.write_videofile(
                output_path,
                fps=24,
                codec="libx264",
                audio_codec="aac",
                logger=None,
            )
            
            # 清理
            final.close()
            base_clip.close()
            audio.close()
            for clip in subtitle_clips:
                clip.close()
            
            return output_path
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    async def generate_subtitles_from_audio(
        self,
        audio_path: str,
        language: str = "zh"
    ) -> List[dict]:
        """
        从音频生成字幕（使用 Whisper）
        
        Returns:
            字幕列表 [{"text": "...", "start": 0.0, "end": 3.0}, ...]
        """
        import whisper
        
        # 加载模型（使用 tiny 或 base 提高速度）
        model = whisper.load_model("base")
        
        # 转录
        result = model.transcribe(audio_path, language=language)
        
        # 转换为标准格式
        subtitles = []
        for segment in result["segments"]:
            subtitles.append({
                "text": segment["text"].strip(),
                "start": segment["start"],
                "end": segment["end"],
            })
        
        return subtitles
