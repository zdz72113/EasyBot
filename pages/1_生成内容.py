"""
EasyBot - 生成内容页（原 app.py 逻辑）
通过问题快速看懂 XX：AI 生成科普内容、历史记录、重新生成。
"""

import streamlit as st
from datetime import datetime

from ai_service import generate_q5_stream, parse_q5_result
from web_fetcher import is_url, fetch_web_content
from history_manager import save_record, load_records, delete_record, update_record
from config import get_ai_models, load_model, save_model

st.set_page_config(
    page_title="生成内容",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 固定布局与标题样式，避免刷新/切换模型后被覆盖
st.markdown("""
<style>
    [data-testid="collapsedControl"] { display: none; }
    .main .block-container,
    [data-testid="stAppViewContainer"] .main .block-container,
    .reportview-container .main .block-container,
    section.main .block-container,
    div[data-testid="stAppViewContainer"] section.main .block-container {
        max-width: 100% !important;
        width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    .qa-question { font-weight: bold; color: #C41E24; font-size: 1.02rem; margin-top: 0.6rem; }
    .tag-badge { display: inline-block; background: #f0f0f0; color: #555; padding: 2px 10px; border-radius: 12px; margin: 2px 4px; font-size: 0.82rem; }
    .section-title { font-size: 1.1rem; font-weight: bold; color: #333; margin: 0.5rem 0; }
</style>
""", unsafe_allow_html=True)


def _preset_ids():
    m = get_ai_models()
    return ["custom"] + [k for k in m if k != "自定义"]


def _preset_to_key(preset: str) -> str:
    return "custom" if preset == "自定义" else preset


def init_session_state():
    AI_MODELS = get_ai_models()
    default_model = (list(AI_MODELS.values()) or [{"base_url": "", "model": ""}])[0]
    preset_keys = list(AI_MODELS.keys())
    defaults = {
        "model_api_url": default_model["base_url"],
        "model_name": default_model["model"],
        "model_preset": preset_keys[0],
        "history_editing_id": None,
        "generated_result": None,
        "raw_output": "",
        "generated_image_bytes": None,
        "video_bytes": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
    for preset_id in _preset_ids():
        k = f"model_api_key_{preset_id}"
        if k not in st.session_state:
            st.session_state[k] = ""
    saved = load_model()
    if saved:
        preset = saved.get("preset")
        if preset and (preset == "自定义" or preset in get_ai_models()):
            st.session_state.model_preset = preset
        st.session_state.model_api_url = saved.get("api_url") or st.session_state.model_api_url
        st.session_state.model_name = saved.get("model_name") or st.session_state.model_name
        api_keys = saved.get("api_keys") or {}
        for pid in _preset_ids():
            if pid in api_keys:
                st.session_state[f"model_api_key_{pid}"] = api_keys.get(pid) or ""


def render_model_config():
    AI_MODELS = get_ai_models()
    preset_keys = list(AI_MODELS.keys())
    current_preset = st.session_state.get("model_preset", "自定义")
    if current_preset not in preset_keys:
        current_preset = "自定义"
    key_suffix = _preset_to_key(current_preset)

    with st.expander("🤖 模型配置", expanded=False):
        preset_col, _, _ = st.columns([2, 2, 2])
        with preset_col:
            selected_preset = st.selectbox(
                "快速选择预设",
                options=preset_keys,
                format_func=lambda k: "自定义" if k == "自定义" else AI_MODELS[k]["name"],
                index=preset_keys.index(current_preset),
                key="model_preset_select",
            )
            if selected_preset != "自定义":
                if selected_preset != current_preset:
                    cfg = AI_MODELS[selected_preset]
                    st.session_state.model_preset = selected_preset
                    st.session_state.model_api_url = cfg["base_url"]
                    st.session_state.model_name = cfg["model"]
                    st.session_state["input_api_url"] = cfg["base_url"]
                    st.session_state["input_model_name"] = cfg["model"]
                    api_keys = {pid: st.session_state.get(f"model_api_key_{pid}", "") for pid in _preset_ids()}
                    save_model(preset=selected_preset, api_url=cfg["base_url"], model_name=cfg["model"], api_keys=api_keys)
                    st.rerun()
                display_api_url = AI_MODELS[selected_preset]["base_url"]
                display_model_name = AI_MODELS[selected_preset]["model"]
            else:
                st.session_state.model_preset = "自定义"
                if selected_preset != current_preset:
                    cfg = AI_MODELS.get("自定义", {})
                    st.session_state.model_api_url = cfg.get("base_url", "")
                    st.session_state.model_name = cfg.get("model", "")
                    st.session_state["input_api_url"] = cfg.get("base_url", "")
                    st.session_state["input_model_name"] = cfg.get("model", "")
                    api_keys = {pid: st.session_state.get(f"model_api_key_{pid}", "") for pid in _preset_ids()}
                    save_model(preset="自定义", api_url=cfg.get("base_url", ""), model_name=cfg.get("model", ""), api_keys=api_keys)
                    st.rerun()
                display_api_url = st.session_state.model_api_url
                display_model_name = st.session_state.model_name

        col1, col2, col3 = st.columns(3)
        with col1:
            api_url = st.text_input("API 接口地址", value=display_api_url, placeholder="https://api.openai.com/v1", help="OpenAI 兼容接口", key="input_api_url")
            st.session_state.model_api_url = api_url
        with col2:
            model_name = st.text_input("模型名字", value=display_model_name, placeholder="gpt-4o-mini", key="input_model_name")
            st.session_state.model_name = model_name
        with col3:
            api_key = st.text_input("API Key", value=st.session_state.get(f"model_api_key_{key_suffix}", ""), type="password", placeholder="sk-...", key=f"input_api_key_{key_suffix}")
            st.session_state[f"model_api_key_{key_suffix}"] = api_key
        if not api_key:
            st.warning("请填写 API Key 后再生成内容")

    api_keys = {pid: st.session_state.get(f"model_api_key_{pid}", "") for pid in _preset_ids()}
    save_model(
        preset=st.session_state.get("model_preset", "自定义"),
        api_url=st.session_state.model_api_url,
        model_name=st.session_state.model_name,
        api_keys=api_keys,
    )
    current_key_suffix = _preset_to_key(st.session_state.get("model_preset", "自定义"))
    return {
        "api_key": st.session_state.get(f"model_api_key_{current_key_suffix}", ""),
        "base_url": st.session_state.model_api_url,
        "model": st.session_state.model_name,
    }


def render_content_generation(model_config: dict):
    st.markdown('<div class="section-title">📝 内容生成</div>', unsafe_allow_html=True)
    user_input = st.text_area("输入主题、一段文字或文章链接", height=110, placeholder="例如：为什么手机要涨价了？\n或粘贴一个文章链接...", key="user_input")
    if not st.button("🚀 生成内容", type="primary", use_container_width=True):
        return
    if not user_input or not user_input.strip():
        st.warning("请输入主题内容")
        return
    if not model_config.get("api_key"):
        st.error("请在上方「模型配置」中填写 API Key")
        return
    if not model_config.get("base_url"):
        st.error("请在上方「模型配置」中填写 API 接口地址")
        return
    web_content = None
    if is_url(user_input.strip()):
        with st.spinner("正在抓取网页内容..."):
            web_content = fetch_web_content(user_input.strip())
            if web_content["success"]:
                st.success(f"已抓取: {web_content['title']}")
            else:
                st.warning(f"网页抓取失败: {web_content['error']}，将直接使用输入内容")
                web_content = None
    st.markdown("---")
    st.subheader("✨ 生成中...")
    output_placeholder = st.empty()
    full_text = ""
    try:
        for chunk in generate_q5_stream(user_input=user_input.strip(), model_config=model_config, web_content=web_content):
            full_text += chunk
            output_placeholder.markdown(full_text + "▌")
        output_placeholder.empty()
        result = parse_q5_result(full_text)
        st.session_state.generated_result = result
        st.session_state.raw_output = full_text
        st.session_state.generated_image_bytes = None
        st.session_state.video_bytes = None
        save_record(user_input.strip(), result)
        st.success("✅ 内容生成完成，已保存到下方历史记录")
        st.rerun()
    except Exception as e:
        st.error(f"生成失败: {str(e)}")


def _render_regenerate_ui(record: dict, record_id: str, model_config: dict):
    st.caption("描述如何调整内容，将拼接到模型提示词中重新生成。留空则按原意润色。")
    adjustment = st.text_area("修改意见", value="", height=80, placeholder="例如：把第二点写得更简洁；增加一段关于XX的说明……", key=f"regen_adjust_{record_id}")
    col_go, col_cancel = st.columns([3, 1])
    with col_go:
        if st.button("🚀 开始重新生成", type="primary", use_container_width=True, key=f"regen_go_{record_id}"):
            if not model_config.get("api_key"):
                st.error("请在上方「模型配置」中填写 API Key")
                return
            if not model_config.get("base_url"):
                st.error("请在上方「模型配置」中填写 API 接口地址")
                return
            instruction = (adjustment or "请对现有内容做适当润色，保持「5个问题看懂」格式不变。").strip()
            st.markdown("---")
            st.subheader("✨ 重新生成中...")
            out_placeholder = st.empty()
            full_text = ""
            try:
                for chunk in generate_q5_stream(user_input="", model_config=model_config, original_raw=record.get("raw", ""), adjustment_instruction=instruction):
                    full_text += chunk
                    out_placeholder.markdown(full_text + "▌")
                out_placeholder.empty()
                result = parse_q5_result(full_text)
                result["raw"] = full_text
                update_record(record_id, result)
                st.session_state.generated_result = {k: result.get(k) for k in ("title", "qa_list", "summary", "tags", "raw")}
                st.session_state.raw_output = full_text
                st.session_state.generated_image_bytes = None
                st.session_state.video_bytes = None
                st.session_state.history_regenerate_id = None
                if f"regen_adjust_{record_id}" in st.session_state:
                    del st.session_state[f"regen_adjust_{record_id}"]
                st.success("✅ 已按修改意见重新生成并更新该条记录")
                st.rerun()
            except Exception as e:
                st.error(f"重新生成失败: {str(e)}")
    with col_cancel:
        if st.button("取消", use_container_width=True, key=f"regen_cancel_{record_id}"):
            st.session_state.history_regenerate_id = None
            st.rerun()


def _render_result_editor(result: dict, record_id: str):
    st.caption("修改后点击「保存」")
    new_title = st.text_input("标题", value=result.get("title", ""), key=f"edit_title_{record_id}")
    qa_list = result.get("qa_list", [])
    new_qa_list = []
    for i in range(5):
        qa = qa_list[i] if i < len(qa_list) else {"q": "", "a": ""}
        col_q, col_a = st.columns([1, 2])
        with col_q:
            new_q = st.text_input(f"Q{i+1}", value=qa.get("q", ""), key=f"edit_q{i}_{record_id}")
        with col_a:
            new_a = st.text_area(f"A{i+1}", value=qa.get("a", ""), height=80, key=f"edit_a{i}_{record_id}")
        new_qa_list.append({"q": new_q, "a": new_a})
    new_summary = st.text_area("简介", value=result.get("summary", ""), height=60, key=f"edit_summary_{record_id}")
    new_tags_str = st.text_input("标签（用空格分隔）", value=" ".join(result.get("tags", [])), key=f"edit_tags_{record_id}")
    col_save, col_cancel = st.columns([3, 1])
    with col_save:
        if st.button("💾 保存修改", type="primary", use_container_width=True, key=f"save_edit_{record_id}"):
            new_tags = [t.strip() for t in new_tags_str.split() if t.strip()]
            updated = {"title": new_title, "qa_list": new_qa_list, "summary": new_summary, "tags": new_tags, "raw": result.get("raw", "")}
            update_record(record_id, updated)
            cur = st.session_state.get("generated_result")
            if cur and cur.get("title") == result.get("title"):
                st.session_state.generated_result = updated
            st.session_state.history_editing_id = None
            st.success("✅ 已保存")
            st.rerun()
    with col_cancel:
        if st.button("取消", use_container_width=True, key=f"cancel_edit_{record_id}"):
            st.session_state.history_editing_id = None
            st.rerun()


def render_history_section(model_config: dict):
    st.markdown('<div class="section-title">📚 历史记录</div>', unsafe_allow_html=True)
    records = load_records()
    if not records:
        st.info("暂无历史记录，在上方生成内容后会自动保存")
        return
    st.caption(f"共 {len(records)} 条历史记录")
    editing_id = st.session_state.get("history_editing_id", None)
    regenerate_id = st.session_state.get("history_regenerate_id", None)
    for record in records:
        ts = record.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts)
            display_time = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            display_time = ts[:16] if ts else "未知时间"
        title = record.get("title", "无标题")
        tags = record.get("tags", [])
        tags_str = "  " + " ".join(f"#{t}" for t in tags) if tags else ""
        record_id = record["id"]
        is_editing_this = editing_id == record_id
        is_regenerating_this = regenerate_id == record_id
        expander_label = f"{'✏️ ' if is_editing_this else '🔄 ' if is_regenerating_this else ''}**{title}**  ·  {display_time}{tags_str}"
        with st.expander(expander_label, expanded=is_editing_this or is_regenerating_this):
            if is_editing_this:
                _render_result_editor(record, record_id=record_id)
            elif is_regenerating_this:
                _render_regenerate_ui(record, record_id=record_id, model_config=model_config)
            else:
                if record.get("summary"):
                    st.markdown(f"*{record['summary']}*")
                for i, qa in enumerate(record.get("qa_list", []), 1):
                    st.markdown(f'<div class="qa-question">Q{i}: {qa.get("q", "")}</div>', unsafe_allow_html=True)
                    st.markdown(qa.get("a", ""))
                if tags:
                    st.markdown(" ".join(f'<span class="tag-badge">{t}</span>' for t in tags), unsafe_allow_html=True)
                st.markdown("---")
                col_regen, col_edit, col_del = st.columns(3)
                with col_regen:
                    if st.button("🔄 重新生成", key=f"regen_{record_id}", use_container_width=True):
                        st.session_state.history_regenerate_id = record_id
                        st.rerun()
                with col_edit:
                    if st.button("✏️ 编辑", key=f"edit_{record_id}", use_container_width=True):
                        st.session_state.history_editing_id = record_id
                        st.rerun()
                with col_del:
                    if st.button("🗑️ 删除", key=f"del_{record_id}", use_container_width=True):
                        delete_record(record_id)
                        st.rerun()


def main():
    init_session_state()
    st.markdown(
        '<div style="text-align:center; margin-bottom:2rem; padding:1.5rem 0;">'
        '<div style="font-size:2.4rem !important; font-weight:bold; color:#C41E24; margin-bottom:0.6rem;">🧠 EasyBot</div>'
        '<div style="font-size:1.05rem !important; color:#555; line-height:1.5; max-width:36em; margin:0 auto;">'
        'AI 驱动的知识科普内容和视频生成工具，核心是「通过问题快速看懂XX」</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    model_config = render_model_config()
    st.divider()
    render_content_generation(model_config)
    st.divider()
    render_history_section(model_config)
    st.divider()
    st.markdown('<div style="text-align:center;color:#aaa;font-size:0.8rem;">EasyBot · Powered by RoyZheng2017@gmail.com</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
