"""
EasyBot - 通过问题快速看懂XX
第2页：生成视频
"""

import io
from datetime import datetime

import streamlit as st
from PIL import Image

from config import (
    HEADER_CONFIG, FOOTER_CONFIG,
    VIDEO_CONFIG,
)
from ai_service import result_to_markdown
from video_generator import get_available_audio_files, generate_video_bytes
from history_manager import load_records, update_record
from renderers import RenderContext
from renderers.markdown_renderer import MarkdownRenderer
from config import get_color_schemes, get_preset_templates, load_poster, save_poster, load_video, save_video

st.set_page_config(
    page_title="生成视频",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    [data-testid="collapsedControl"] { display: none; }
    /* 防止刷新后内容区变窄 */
    .main .block-container, [data-testid="stAppViewContainer"] .main .block-container,
    .reportview-container .main .block-container {
        max-width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #C41E24;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #888;
        text-align: center;
        margin-bottom: 1rem;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: bold;
        color: #333;
        margin: 0.5rem 0;
    }
    .content-card {
        background: #f8f9fa;
        border-left: 4px solid #C41E24;
        border-radius: 6px;
        padding: 10px 16px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    defaults = {
        "generated_result": None,
        "raw_output": "",
        "generated_image_bytes": None,
        "video_bytes": None,
        "p2_selected_record_id": "__current__",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
    # 从 JSON 恢复海报配置：仅当 key 不存在时写入，避免每次 rerun 用旧 JSON 覆盖用户当次修改（否则标签等修改无法保存）
    saved_poster = load_poster()
    if saved_poster:
        if "poster_template" not in st.session_state and saved_poster.get("template"):
            st.session_state.poster_template = saved_poster["template"]
        if "poster_color_scheme" not in st.session_state and saved_poster.get("color_scheme"):
            st.session_state.poster_color_scheme = saved_poster["color_scheme"]
        if "poster_header_title" not in st.session_state and saved_poster.get("header_title") is not None:
            st.session_state.poster_header_title = saved_poster["header_title"]
        if "poster_header_subtitle" not in st.session_state and saved_poster.get("header_subtitle") is not None:
            st.session_state.poster_header_subtitle = saved_poster["header_subtitle"]
        if "poster_header_tag" not in st.session_state and saved_poster.get("header_tag") is not None:
            st.session_state.poster_header_tag = saved_poster["header_tag"]
    template_names = list(get_preset_templates().keys())
    # 仅首次进入页面时用 JSON 初始化下拉框选中项，之后以用户选择为准
    if "poster_template_select" not in st.session_state:
        st.session_state.poster_template_select = (
            (saved_poster.get("template_select") or saved_poster.get("template")) if saved_poster else (template_names[0] if template_names else "自定义")
        ) or (template_names[0] if template_names else "自定义")
    # 视频配置从 JSON 在 render_video_config 中恢复


def render_poster_config():
    """顶部海报配置（可收缩）；切换模板时同步更新配色、头部等具体内容"""
    PRESET_TEMPLATES = get_preset_templates()
    COLOR_SCHEMES = get_color_schemes()
    template_names = list(PRESET_TEMPLATES.keys())
    current_template = st.session_state.get("poster_template", template_names[0] if template_names else "自定义")
    if current_template not in template_names:
        current_template = template_names[0] if template_names else "自定义"
    if "poster_template_select" not in st.session_state:
        st.session_state.poster_template_select = current_template

    with st.expander("🎨 海报配置", expanded=False):
        idx = template_names.index(st.session_state.poster_template_select) if st.session_state.poster_template_select in template_names else 0
        selected_template_name = st.selectbox(
            "选择海报模板",
            options=template_names,
            index=idx,
            help="选择预设的品牌模板",
            key="poster_template_select",
        )
        selected_template = PRESET_TEMPLATES[selected_template_name]
        template_header = selected_template.get("header", HEADER_CONFIG)

        # 用独立 key 检测模板是否被用户切换；切换后用该模板默认值更新并 rerun
        # 不能修改 poster_template_select（该 key 已绑定 selectbox），rerun 后下拉框会保持用户所选
        if selected_template_name != current_template:
            st.session_state.poster_template = selected_template_name
            st.session_state.poster_color_scheme = selected_template.get("color_scheme", "经典红")
            st.session_state.poster_header_title = template_header.get("title", HEADER_CONFIG["title"])
            st.session_state.poster_header_subtitle = template_header.get("subtitle", HEADER_CONFIG["subtitle"])
            st.session_state.poster_header_tag = template_header.get("tag", HEADER_CONFIG["tag"])
            # 先写入 JSON，再 rerun，否则下次 init 会从 JSON 读回旧模板
            save_poster(
                template=selected_template_name,
                template_select=selected_template_name,
                color_scheme=st.session_state.poster_color_scheme,
                header_title=st.session_state.poster_header_title,
                header_subtitle=st.session_state.poster_header_subtitle,
                header_tag=st.session_state.poster_header_tag,
            )
            # 清除与模板相关的 widget 状态，让输入框在 rerun 后显示新值
            for k in list(st.session_state.keys()):
                if k.startswith("poster_header_") or k == "poster_color_scheme":
                    del st.session_state[k]
            st.rerun()

        default_color_scheme = st.session_state.get("poster_color_scheme", selected_template.get("color_scheme", "经典红"))
        color_scheme_options = list(COLOR_SCHEMES.keys()) if COLOR_SCHEMES else ["经典红"]
        default_color_index = (
            color_scheme_options.index(default_color_scheme)
            if default_color_scheme in color_scheme_options
            else 0
        )

        color_scheme = st.selectbox(
            "配色方案",
            options=color_scheme_options,
            index=default_color_index,
            key="poster_color_scheme",
        )
        colors = (COLOR_SCHEMES.get(color_scheme) or list(COLOR_SCHEMES.values())[0]) if COLOR_SCHEMES else {"primary": "#C41E24", "background": "#FDF8F5"}
        swatch_html = (
            f'<span style="background:{colors["primary"]};display:inline-block;'
            f'width:28px;height:28px;border-radius:4px;margin-right:6px;vertical-align:middle;"></span>'
            f'<span style="background:{colors["background"]};display:inline-block;'
            f'width:28px;height:28px;border-radius:4px;border:1px solid #ccc;'
            f'margin-right:6px;vertical-align:middle;"></span>'
            f'<small>{colors["primary"]} / {colors["background"]}</small>'
        )
        st.markdown(swatch_html, unsafe_allow_html=True)

        st.markdown("**头部文字**")
        hcol1, hcol2, hcol3 = st.columns(3)
        with hcol1:
            st.text_input(
                "头部标题",
                value=st.session_state.get("poster_header_title", template_header.get("title", HEADER_CONFIG["title"])),
                key="poster_header_title",
            )
        with hcol2:
            st.text_input(
                "副标题",
                value=st.session_state.get("poster_header_subtitle", template_header.get("subtitle", HEADER_CONFIG["subtitle"])),
                key="poster_header_subtitle",
            )
        with hcol3:
            st.text_input(
                "标签",
                value=st.session_state.get("poster_header_tag", template_header.get("tag", HEADER_CONFIG["tag"])),
                key="poster_header_tag",
            )

    # 持久化到 JSON
    save_poster(
        template=st.session_state.get("poster_template", template_names[0]),
        template_select=st.session_state.get("poster_template_select", st.session_state.get("poster_template", template_names[0])),
        color_scheme=st.session_state.get("poster_color_scheme", "经典红"),
        header_title=st.session_state.get("poster_header_title", HEADER_CONFIG["title"]),
        header_subtitle=st.session_state.get("poster_header_subtitle", HEADER_CONFIG["subtitle"]),
        header_tag=st.session_state.get("poster_header_tag", HEADER_CONFIG["tag"]),
    )

    cur_template = st.session_state.get("poster_template", template_names[0] if template_names else "自定义")
    selected_template = PRESET_TEMPLATES.get(cur_template) or (list(PRESET_TEMPLATES.values())[0] if PRESET_TEMPLATES else {})
    return {
        "selected_template": selected_template,
        "color_scheme": st.session_state.get("poster_color_scheme", "经典红"),
        "header_title": st.session_state.get("poster_header_title", HEADER_CONFIG["title"]),
        "header_subtitle": st.session_state.get("poster_header_subtitle", HEADER_CONFIG["subtitle"]),
        "header_tag": st.session_state.get("poster_header_tag", HEADER_CONFIG["tag"]),
    }


def render_video_config():
    """顶部视频配置（可收缩）"""
    saved_video = load_video()
    default_duration = (saved_video.get("duration") if saved_video else None) or VIDEO_CONFIG["default_duration"]
    duration_value = st.session_state.get("video_duration", default_duration)

    with st.expander("🎬 视频配置", expanded=False):
        audio_files = get_available_audio_files()
        selected_audio_path = None
        selected_audio_name = None
        if audio_files:
            audio_options = {name: path for name, path in audio_files}
            audio_names = list(audio_options.keys())
            default_audio_idx = 0
            if saved_video and saved_video.get("audio_name") and saved_video["audio_name"] in audio_names:
                default_audio_idx = audio_names.index(saved_video["audio_name"])
            selected_audio_name = st.selectbox(
                "背景音乐",
                options=audio_names,
                index=default_audio_idx,
                key="video_audio_name",
            )
            selected_audio_path = audio_options[selected_audio_name]
        else:
            st.warning("未找到音频文件，请在 `audio` 文件夹中放置 MP3/WAV 文件")

        video_duration = st.slider(
            "视频时长（秒）",
            min_value=5, max_value=20,
            value=duration_value,
            step=1,
            key="video_duration",
        )

    save_video(audio_name=selected_audio_name, duration=video_duration)

    return {
        "selected_audio_path": selected_audio_path,
        "video_duration": video_duration,
    }


def build_render_context(poster_config: dict) -> RenderContext:
    template = poster_config["selected_template"]
    return RenderContext(
        color_scheme_name=poster_config["color_scheme"],
        header_config={
            "title": poster_config["header_title"],
            "subtitle": poster_config["header_subtitle"],
            "tag": poster_config["header_tag"],
            "height": HEADER_CONFIG["height"],
        },
        footer_config={
            "show_banner": False,
            "banner_text": "",
            "banner_height": FOOTER_CONFIG["banner_height"],
            "slant_width": FOOTER_CONFIG["slant_width"],
            "font_size": FOOTER_CONFIG["font_size"],
        },
        icon_path=template.get("icon", None),
    )


def generate_poster_bytes(markdown_text: str, poster_config: dict) -> bytes:
    renderer = MarkdownRenderer()
    context = build_render_context(poster_config)
    img = renderer.render(markdown_text, context)
    img_bytes_io = io.BytesIO()
    img.save(img_bytes_io, format="PNG", quality=95)
    img_bytes_io.seek(0)
    return img_bytes_io.getvalue()


def render_content_selector() -> dict | None:
    """内容选择器：从历史记录或当前内容中选择"""
    st.markdown('<div class="section-title">📂 选择内容</div>', unsafe_allow_html=True)

    records = load_records()
    current_result = st.session_state.get("generated_result")

    options = {}
    if current_result and current_result.get("title"):
        options["__current__"] = f"📌 当前内容：{current_result['title']}"

    for r in records:
        ts = r.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts)
            time_str = dt.strftime("%m-%d %H:%M")
        except Exception:
            time_str = ts[:10] if ts else ""
        label = f"{r.get('title', '无标题')}  ·  {time_str}"
        options[r["id"]] = label

    if not options:
        st.info("暂无可用内容。请前往「生成内容」页面生成内容或查看历史记录。")
        return None

    option_keys = list(options.keys())
    option_labels = list(options.values())

    prev_id = st.session_state.get("p2_selected_record_id", option_keys[0])
    if prev_id not in option_keys:
        prev_id = option_keys[0]

    selected_idx = st.selectbox(
        "选择要使用的内容",
        range(len(option_keys)),
        format_func=lambda i: option_labels[i],
        index=option_keys.index(prev_id),
        key="p2_content_select",
    )
    selected_id = option_keys[selected_idx]
    st.session_state.p2_selected_record_id = selected_id

    if selected_id == "__current__":
        result = current_result
    else:
        result = next((r for r in records if r["id"] == selected_id), None)
        if result:
            result = {
                "title": result.get("title", ""),
                "qa_list": result.get("qa_list", []),
                "summary": result.get("summary", ""),
                "tags": result.get("tags", []),
                "raw": result.get("raw", ""),
            }

    return result


def _render_preview_editor(result: dict, selected_id: str):
    """内容预览内的编辑表单（用于生成视频页）"""
    st.caption("修改后点击「保存」")
    new_title = st.text_input("标题", value=result.get("title", ""), key="p2_edit_title")
    qa_list = result.get("qa_list", [])
    new_qa_list = []
    for i in range(5):
        qa = qa_list[i] if i < len(qa_list) else {"q": "", "a": ""}
        col_q, col_a = st.columns([1, 2])
        with col_q:
            new_q = st.text_input(f"Q{i+1}", value=qa.get("q", ""), key=f"p2_edit_q{i}")
        with col_a:
            new_a = st.text_area(f"A{i+1}", value=qa.get("a", ""), height=80, key=f"p2_edit_a{i}")
        new_qa_list.append({"q": new_q, "a": new_a})
    new_summary = st.text_area("简介", value=result.get("summary", ""), height=60, key="p2_edit_summary")
    new_tags_str = st.text_input("标签（用空格分隔）", value=" ".join(result.get("tags", [])), key="p2_edit_tags")
    col_save, col_cancel = st.columns([3, 1])
    with col_save:
        if st.button("💾 保存", type="primary", use_container_width=True, key="p2_edit_save"):
            new_tags = [t.strip() for t in new_tags_str.split() if t.strip()]
            updated = {
                "title": new_title,
                "qa_list": new_qa_list,
                "summary": new_summary,
                "tags": new_tags,
                "raw": result.get("raw", ""),
            }
            if selected_id == "__current__":
                st.session_state.generated_result = updated
                st.session_state.raw_output = updated.get("raw", "")
            else:
                update_record(selected_id, updated)
            st.session_state.p2_editing_content_id = None
            st.success("✅ 已保存")
            st.rerun()
    with col_cancel:
        if st.button("取消", use_container_width=True, key="p2_edit_cancel"):
            st.session_state.p2_editing_content_id = None
            st.rerun()


def render_preview_column(result: dict):
    """左侧 1/3：内容预览（含编辑按钮）"""
    st.markdown("**👀 内容预览**")
    if not result:
        st.caption("请在上方选择内容")
        return
    selected_id = st.session_state.get("p2_selected_record_id", "__current__")
    is_editing = st.session_state.get("p2_editing_content_id") == selected_id

    if is_editing:
        _render_preview_editor(result, selected_id)
        return

    st.markdown(f"**{result.get('title', '无标题')}**")
    if result.get("summary"):
        st.caption(result["summary"])
    for i, qa in enumerate(result.get("qa_list", []), 1):
        st.markdown(f"**Q{i}** {qa.get('q', '')}")
        st.markdown(qa.get("a", "")[:80] + ("…" if len(qa.get("a", "")) > 80 else ""))
    if result.get("tags"):
        st.caption(" ".join(f"#{t}" for t in result["tags"]))
    if st.button("✏️ 编辑", use_container_width=True, key="p2_btn_edit_content"):
        st.session_state.p2_editing_content_id = selected_id
        st.rerun()


def render_poster_column(result: dict, poster_config: dict):
    """中间 1/3：生成海报"""
    st.markdown("**🖼️ 生成海报**")

    if not result:
        st.caption("请先选择内容")
        return

    if st.button("🖼️ 生成海报", type="primary", use_container_width=True, key="btn_gen_poster"):
        with st.spinner("正在生成海报..."):
            try:
                markdown_text = result_to_markdown(result)
                poster_bytes = generate_poster_bytes(markdown_text, poster_config)
                st.session_state.generated_image_bytes = poster_bytes
                st.session_state.video_bytes = None
                st.success("✅ 海报生成成功！")
            except Exception as e:
                st.error(f"海报生成失败: {str(e)}")

    if st.session_state.generated_image_bytes:
        st.image(st.session_state.generated_image_bytes, use_container_width=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="📥 下载海报",
            data=st.session_state.generated_image_bytes,
            file_name=f"easybot_poster_{timestamp}.png",
            mime="image/png",
            use_container_width=True,
        )


def render_video_column(video_config: dict):
    """右侧 1/3：生成视频"""
    st.markdown("**🎬 生成视频**")

    if not st.session_state.generated_image_bytes:
        st.info("请先在中间列生成海报")
        return

    if not video_config.get("selected_audio_path"):
        st.warning("未找到音频文件，请在 `audio` 文件夹中放置 MP3/WAV")
        return

    if st.button("🎬 生成视频", type="primary", use_container_width=True, key="btn_gen_video"):
        duration = video_config["video_duration"]
        with st.spinner(f"正在生成 {duration} 秒视频..."):
            try:
                img = Image.open(io.BytesIO(st.session_state.generated_image_bytes))
                video_bytes = generate_video_bytes(
                    image=img,
                    audio_path=video_config["selected_audio_path"],
                    duration=duration,
                )
                st.session_state.video_bytes = video_bytes
                st.success("✅ 视频生成成功！")
            except Exception as e:
                st.error(f"视频生成失败: {str(e)}")

    if st.session_state.video_bytes:
        st.video(st.session_state.video_bytes)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="📥 下载视频 (MP4)",
            data=st.session_state.video_bytes,
            file_name=f"easybot_video_{timestamp}.mp4",
            mime="video/mp4",
            use_container_width=True,
        )


def main():
    init_session_state()

    st.markdown(
        '<div class="main-header">🎬 生成视频</div>'
        '<div class="sub-header">加载任意内容，一键生成海报和视频</div>',
        unsafe_allow_html=True,
    )

    poster_config = render_poster_config()
    video_config = render_video_config()

    st.divider()

    result = render_content_selector()

    if result:
        st.divider()
        col_preview, col_poster, col_video = st.columns(3)
        with col_preview:
            render_preview_column(result)
        with col_poster:
            render_poster_column(result, poster_config)
        with col_video:
            render_video_column(video_config)

    st.divider()
    st.markdown(
        '<div style="text-align:center;color:#aaa;font-size:0.8rem;">'
        "EasyBot · Powered by RoyZheng2017@gmail.com + Pillow + MoviePy"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
