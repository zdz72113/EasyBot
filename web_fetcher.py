"""
网页内容抓取模块
检测 URL 并提取网页正文内容
"""

import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


def is_url(text: str) -> bool:
    """检测文本是否为 URL"""
    text = text.strip()
    if not text:
        return False
    if re.match(r'^https?://', text):
        try:
            result = urlparse(text)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    return False


def fetch_web_content(url: str, timeout: int = 15, max_chars: int = 8000) -> dict:
    """
    抓取网页内容，提取标题和正文

    Returns:
        {"title": str, "content": str, "url": str, "success": bool, "error": str}
    """
    result = {"title": "", "content": "", "url": url, "success": False, "error": ""}

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()

        if resp.encoding and resp.encoding.lower() == "iso-8859-1":
            resp.encoding = resp.apparent_encoding

        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside",
                         "iframe", "noscript", "form", "button", "svg"]):
            tag.decompose()

        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        article = soup.find("article")
        if article:
            text = article.get_text(separator="\n", strip=True)
        else:
            main = soup.find("main") or soup.find("div", {"id": "content"}) or soup.find("div", {"class": "content"})
            if main:
                text = main.get_text(separator="\n", strip=True)
            else:
                text = soup.body.get_text(separator="\n", strip=True) if soup.body else ""

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        cleaned = "\n".join(lines)

        if len(cleaned) > max_chars:
            cleaned = cleaned[:max_chars] + "\n...(内容已截断)"

        result["title"] = title
        result["content"] = cleaned
        result["success"] = True

    except requests.Timeout:
        result["error"] = "请求超时，请检查网络或链接是否可用"
    except requests.ConnectionError:
        result["error"] = "连接失败，请检查网络连接"
    except requests.HTTPError as e:
        result["error"] = f"HTTP 错误: {e.response.status_code}"
    except Exception as e:
        result["error"] = f"抓取失败: {str(e)}"

    return result
