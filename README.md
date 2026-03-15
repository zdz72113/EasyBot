# EasyBot

个人知识学习和创现工作台，通过一键流程把感兴趣的热点话题快速变成「内容 + 海报 + 视频」

![EasyBot](https://github.com/zdz72113/EasyBot/blob/main/img/1.png)

---

## 功能

1. **内容生成**：输入主题或链接，自动搜索并生成结构化科普文档。
2. **海报制作**：内置多套模板，一键将内容排版为知识海报。
3. **视频合成**：选择背景音乐和时长，自动将海报合成为短视频。

---

## 案例

![案例](https://github.com/zdz72113/EasyBot/blob/main/img/example.jpg)

---

## 安装使用

1. 从 [Releases](https://github.com/zdz72113/EasyBot/releases) 中下载对应版本的.zip文件。
2. 解压到任意目录（建议路径不含中文或空格）。
3. 双击 **运行EasyBot.bat**，然后打开浏览器输入 http://localhost:8502 页面即可访问。

---

## 使用说明

- **模型**：在「生成内容」页展开「模型配置」，选择预设或自定义，填写 API 地址、模型名、API Key。
- **海报**：在「生成视频」页选择模板，可改头部标题/副标题/标签、配色。
- **视频**：从网上下载背景音乐并放入`audio/` 目录，然后可以选择背景音乐和时长。

---

## 从代码启动

### 环境

- Python 3.10+
- 依赖见 `requirements.txt`

```bash
pip install -r requirements.txt
```

### 启动

```bash
streamlit run EasyBot.py
```

---


## 技术栈

- **Streamlit** 多页应用
- **OpenAI 兼容 API**（DeepSeek、通义千问等）流式生成
- **Pillow** 海报绘图
- **MoviePy** 视频合成
- **BeautifulSoup / requests** 网页抓取

---

## 许可与署名

EasyBot · Powered by RoyZheng2017@gmail.com

## 联系作者

![联系](https://github.com/zdz72113/EasyBot/blob/main/img/contact.jpg)
