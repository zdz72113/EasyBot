# EasyBot

AI 驱动的知识科普内容和视频生成工具，核心是「通过问题快速看懂一个主题」。

输入主题、一段文字或文章链接，由 AI 生成「5 个问题看懂 XXX」格式的科普内容；支持历史记录、重新生成、编辑；在「生成视频」页可选择内容一键生成海报与视频。

![EasyBot](https://github.com/zdz72113/EasyBot/blob/main/img/1.png)

---

## 功能

1. **生成内容**：输入主题或文章链接，调用 OpenAI 兼容接口（如 DeepSeek、通义千问）流式生成「5 个问题看懂」格式内容，支持网页抓取。保存生成结果并支持编辑、重新生成、删除
2.  **生成视频**：从历史或当前内容中选择，配置海报模板与配色，生成海报图；再选背景音乐与时长，生成 MP4 视频。

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
