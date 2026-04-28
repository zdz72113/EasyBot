# EasyBot v2.0 - 知识创作工作台

> Learn. Create. Monetize.

AI 驱动的知识学习与内容创作平台，支持素材抓取、内容生成、海报制作、视频合成等功能。

## ✨ 新特性 (v2.0)

- **Vue3 前端**: 现代化界面，更好的用户体验
- **增强素材抓取**: 支持 Jina AI Reader、Firecrawl 等多种抓取方式
- **素材管理**: 统一管理抓取到的图片、链接、文本
- **精简海报模板**: 核心模板 + 可视化配置
- **视频字幕**: 支持配音上传 + 自动生成字幕
- **FastAPI 后端**: 高性能异步 API

## 🚀 快速开始

### 方式1: 一键启动 (推荐)

```bash
# 确保已安装 Python 3.10+ 和 Node.js 18+
python start.py
```

### 方式2: 分别启动

**后端:**
```bash
pip install -r app/requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

**前端:**
```bash
cd app/web
npm install
npm run dev
```

访问 http://localhost:5173

## 📁 项目结构

```
EasyBot_New/
├── app/                  # 应用主目录
│   ├── api/              # API 路由
│   │   ├── content.py    # 内容生成接口
│   │   ├── fetcher.py    # 素材抓取接口
│   │   ├── config.py     # 配置接口
│   │   ├── poster.py     # 海报制作接口
│   │   └── video.py      # 视频合成接口
│   ├── core/             # 核心配置
│   │   └── config.py     # 应用配置
│   ├── models/           # 数据模型
│   │   └── schemas.py    # Pydantic 模型
│   ├── services/         # 业务逻辑
│   │   ├── ai_service.py       # AI 内容生成
│   │   ├── fetcher_service.py  # 素材抓取
│   │   ├── poster_service.py   # 海报渲染
│   │   ├── video_service.py    # 视频合成
│   │   └── history_service.py  # 历史记录
│   ├── web/              # Vue3 前端
│   │   ├── src/
│   │   │   ├── views/    # 页面组件
│   │   │   ├── components/  # 公共组件
│   │   │   ├── api/      # API 调用
│   │   │   ├── stores/   # Pinia 状态
│   │   │   └── router/   # 路由配置
│   │   └── package.json
│   ├── main.py           # FastAPI 入口
│   └── requirements.txt  # Python 依赖
├── audio/                # 音频资源文件
├── start.py              # 一键启动脚本
└── README.md             # 项目说明
```

## 🔧 配置说明

### 1. AI 模型配置

在系统设置中配置：

- **DeepSeek**: 推荐，支持联网搜索
  - Base URL: `https://api.deepseek.com/v1`
  - Model: `deepseek-chat`

- **通义千问**: 阿里云服务
  - Base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`
  - Model: `qwen-plus`

### 2. 素材抓取配置 (可选)

- **Jina AI Reader**: 免费，无需配置
- **Firecrawl**: 需要 API Key，支持结构化数据
  - 获取地址: https://firecrawl.dev

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Element Plus |
| 后端 | FastAPI + Python 3.10+ |
| AI | OpenAI 兼容接口 |
| 视频 | MoviePy + FFmpeg |
| 语音 | OpenAI Whisper |

## 📌 功能模块

| 模块 | 功能 |
|------|------|
| 内容生成 | 输入主题，AI 自动生成「5个问题看懂」格式内容 |
| 素材管理 | 抓取网页内容，收集图片、链接等素材 |
| 海报制作 | 选择模板，一键生成精美知识海报 |
| 视频创作 | 合成海报与音频，支持字幕生成 |

## 📝 注意事项

1. **API Key**: 请妥善保管，仅存储在本地 `data/config.json`
2. **字体**: 海报渲染需要中文字体，系统会自动查找常见字体
3. **音频**: 视频创作需要背景音乐，请将 MP3 文件放入 `audio/` 目录

## 🤝 更新计划

- [x] Vue3 前端重构
- [x] 增强素材抓取
- [ ] 多场景视频编辑
- [ ] 高级字幕样式
- [ ] 素材库云端同步

---

Powered by EasyBot Team
