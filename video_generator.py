"""
视频生成模块
使用 moviepy 将海报图片和音频合成为视频
"""

import os
from pathlib import Path
from typing import List, Tuple
from PIL import Image
import tempfile

from config import VIDEO_CONFIG, DEFAULT_WIDTH, DEFAULT_HEIGHT


def get_available_audio_files(audio_dir: str = None) -> List[Tuple[str, str]]:
    """
    获取可用的音频文件列表

    Returns:
        [(显示名称, 文件路径), ...]
    """
    if audio_dir is None:
        audio_dir = VIDEO_CONFIG["audio_dir"]

    audio_extensions = {'.mp3', '.wav', '.ogg', '.m4a', '.flac'}
    audio_files = []

    audio_path = Path(audio_dir)
    if not audio_path.exists():
        audio_path.mkdir(parents=True, exist_ok=True)
        return audio_files

    for file in audio_path.iterdir():
        if file.is_file() and file.suffix.lower() in audio_extensions:
            display_name = file.stem
            audio_files.append((display_name, str(file)))

    audio_files.sort(key=lambda x: x[0])
    return audio_files


def resize_to_aspect_ratio(image: Image.Image, width_ratio: int, height_ratio: int) -> Image.Image:
    """调整图片到指定宽高比，通过添加背景色填充"""
    original_width, original_height = image.size
    target_ratio = width_ratio / height_ratio
    current_ratio = original_width / original_height

    if abs(current_ratio - target_ratio) < 0.01:
        return image

    if current_ratio > target_ratio:
        new_height = int(original_width / target_ratio)
        new_width = original_width
    else:
        new_width = int(original_height * target_ratio)
        new_height = original_height

    bg_color = image.getpixel((0, 0))
    new_image = Image.new('RGB', (new_width, new_height), bg_color)

    x_offset = (new_width - original_width) // 2
    y_offset = (new_height - original_height) // 2
    new_image.paste(image, (x_offset, y_offset))

    return new_image


def generate_video(
    image: Image.Image,
    audio_path: str,
    duration: int,
    output_path: str = None,
) -> str:
    """生成视频文件，返回文件路径"""
    from moviepy import ImageClip, AudioFileClip, concatenate_audioclips

    output_dir = VIDEO_CONFIG["output_dir"]
    os.makedirs(output_dir, exist_ok=True)

    if output_path is None:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"video_{timestamp}.mp4")

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        temp_image_path = tmp_file.name
        image = resize_to_aspect_ratio(image, 9, 16)
        image.save(temp_image_path, 'PNG')

    try:
        image_clip = ImageClip(temp_image_path, duration=duration)
        audio_clip = AudioFileClip(audio_path)

        if audio_clip.duration > duration:
            audio_clip = audio_clip.subclipped(0, duration)
        elif audio_clip.duration < duration:
            loops_needed = int(duration / audio_clip.duration) + 1
            audio_clips = [audio_clip] * loops_needed
            audio_clip = concatenate_audioclips(audio_clips).subclipped(0, duration)

        final_clip = image_clip.with_audio(audio_clip)

        final_clip.write_videofile(
            output_path,
            fps=VIDEO_CONFIG["fps"],
            codec=VIDEO_CONFIG["codec"],
            audio_codec=VIDEO_CONFIG["audio_codec"],
            logger=None,
        )

        final_clip.close()
        image_clip.close()
        audio_clip.close()

        return output_path

    finally:
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)


def generate_video_bytes(
    image: Image.Image,
    audio_path: str,
    duration: int,
) -> bytes:
    """生成视频并返回字节数据（用于 Streamlit 下载）"""
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
        temp_video_path = tmp_file.name

    try:
        generate_video(image, audio_path, duration, temp_video_path)

        with open(temp_video_path, 'rb') as f:
            video_bytes = f.read()

        return video_bytes

    finally:
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
