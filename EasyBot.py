"""
EasyBot 首页：标题、简介与流程入口。
运行: streamlit run EasyBot.py
"""

import streamlit as st

st.set_page_config(
    page_title="EasyBot",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 保持宽版布局
st.markdown("""
<style>
    [data-testid="collapsedControl"] { display: none; }
    .main .block-container,
    [data-testid="stAppViewContainer"] .main .block-container,
    .reportview-container .main .block-container,
    section.main .block-container {
        max-width: 100% !important;
        width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    .hero-title { font-size: 2.4rem !important; font-weight: bold; color: #C41E24; text-align: center; margin-bottom: 0.6rem; }
    .hero-desc { font-size: 1.05rem !important; color: #555; line-height: 1.5; text-align: center; max-width: 36em; margin: 0 auto 2rem; }
    .step-card { background: #f8f9fa; border-left: 4px solid #C41E24; border-radius: 8px; padding: 1.25rem 1.5rem; margin-bottom: 1rem; }
    .step-num { font-weight: bold; color: #C41E24; font-size: 1rem; margin-bottom: 0.25rem; }
    .step-title { font-size: 1.15rem; font-weight: bold; color: #333; margin-bottom: 0.35rem; }
    .step-desc { font-size: 0.95rem; color: #666; margin-bottom: 0.75rem; }
</style>
""", unsafe_allow_html=True)

# 标题与简介
st.markdown(
    '<div class="hero-title">🧠 EasyBot</div>'
    '<div class="hero-desc">AI 驱动的知识科普内容和视频生成工具，核心是「通过问题快速看懂一个主题」</div>',
    unsafe_allow_html=True,
)

st.divider()

# 流程步骤与跳转
st.markdown("**📋 使用流程**")
col1, col2 = st.columns(2)
with col1:
    st.markdown(
        '<div class="step-card">'
        '<div class="step-num">第一步</div>'
        '<div class="step-title">生成内容</div>'
        '<div class="step-desc">输入主题或文章链接，由 AI 生成「5 个问题看懂 XXX」格式的科普内容，可编辑、重新生成并保存。</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.page_link("pages/1_生成内容.py", label="前往生成内容 →", icon="🧠")
with col2:
    st.markdown(
        '<div class="step-card">'
        '<div class="step-num">第二步</div>'
        '<div class="step-title">生成视频</div>'
        '<div class="step-desc">从历史或当前内容中选择，配置海报模板与配色生成海报，再选择背景音乐与时长一键生成 MP4 视频。</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.page_link("pages/2_生成视频.py", label="前往生成视频 →", icon="🎬")

st.divider()
st.markdown(
    '<div style="text-align:center; color:#aaa; font-size:0.8rem;">EasyBot · Powered by RoyZheng2017@gmail.com</div>',
    unsafe_allow_html=True,
)
