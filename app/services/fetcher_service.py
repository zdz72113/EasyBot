"""
素材抓取增强服务
支持：Jina AI Reader, Firecrawl, 基础爬虫
"""
import re
import httpx
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, quote_plus
from app.models.schemas import FetchResult, Material
from app.core.config import get_fetcher_config


class FetcherService:
    """素材抓取服务"""
    
    def __init__(self):
        self.config = get_fetcher_config()
        self.jina_api_key = self.config.get("jina_api_key", "")
        self.firecrawl_api_key = self.config.get("firecrawl_api_key", "")
    
    @staticmethod
    def is_url(text: str) -> bool:
        """检测是否为 URL"""
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
    
    async def fetch(self, url: str, method: str = "auto") -> FetchResult:
        """
        抓取网页素材
        
        Args:
            url: 网页链接
            method: 抓取方式 (auto, jina, firecrawl, basic)
        
        Returns:
            FetchResult: 包含正文、图片、链接等素材
        """
        # 自动选择最优抓取方式
        if method == "auto":
            method = self._select_best_method(url)
        
        try:
            if method == "jina":
                return await self._fetch_with_jina(url)
            elif method == "firecrawl":
                return await self._fetch_with_firecrawl(url)
            else:
                return await self._fetch_basic(url)
        except Exception as e:
            # 失败后降级到基础抓取
            if method != "basic":
                return await self._fetch_basic(url)
            return FetchResult(
                url=url,
                title="",
                content="",
                materials=[],
                success=False,
                error=str(e)
            )
    
    def _select_best_method(self, url: str) -> str:
        """选择最佳抓取方式"""
        # 优先使用 Jina（免费且稳定）
        if "r.jina.ai" not in url:  # 避免循环
            return "jina"
        # 其次尝试 Firecrawl
        if self.firecrawl_api_key:
            return "firecrawl"
        return "basic"
    
    async def _fetch_with_jina(self, url: str) -> FetchResult:
        """使用 Jina AI Reader 抓取"""
        jina_url = f"https://r.jina.ai/http://{url.replace('https://', '').replace('http://', '')}"
        
        async with httpx.AsyncClient(timeout=30) as client:
            headers = {}
            if self.jina_api_key:
                headers["Authorization"] = f"Bearer {self.jina_api_key}"
            
            resp = await client.get(jina_url, headers=headers)
            resp.raise_for_status()
            
            content = resp.text
            
            # 解析 Jina 返回的内容（Markdown 格式）
            title = ""
            title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
            if title_match:
                title = title_match.group(1).strip()
            
            # 同时抓取原始页面获取图片等素材
            basic_result = await self._fetch_basic(url, parse_content=False)
            
            return FetchResult(
                url=url,
                title=title or basic_result.title,
                content=content,
                materials=basic_result.materials,
                success=True
            )
    
    async def _fetch_with_firecrawl(self, url: str) -> FetchResult:
        """使用 Firecrawl 抓取（结构化数据）"""
        api_url = "https://api.firecrawl.dev/v1/scrape"
        
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                api_url,
                headers={"Authorization": f"Bearer {self.firecrawl_api_key}"},
                json={
                    "url": url,
                    "formats": ["markdown", "links", "images"]
                }
            )
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("success"):
                result_data = data.get("data", {})
                
                materials = []
                
                # 收集图片
                for img in result_data.get("images", []):
                    materials.append(Material(
                        type="image",
                        content=img.get("alt", ""),
                        url=img.get("src"),
                        title=img.get("alt", "")
                    ))
                
                # 收集链接
                for link in result_data.get("links", []):
                    materials.append(Material(
                        type="link",
                        content=link.get("title", ""),
                        url=link.get("url"),
                        title=link.get("title", "")
                    ))
                
                return FetchResult(
                    url=url,
                    title=result_data.get("title", ""),
                    content=result_data.get("markdown", result_data.get("content", "")),
                    materials=materials,
                    success=True
                )
            
            raise Exception(f"Firecrawl API error: {data}")
    
    async def _fetch_basic(
        self,
        url: str,
        parse_content: bool = True
    ) -> FetchResult:
        """基础爬虫抓取"""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        resp.raise_for_status()
        
        if resp.encoding and resp.encoding.lower() == "iso-8859-1":
            resp.encoding = resp.apparent_encoding
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # 清理无关标签
        for tag in soup(["script", "style", "nav", "footer", "header", "aside",
                         "iframe", "noscript", "form", "button", "svg"]):
            tag.decompose()
        
        # 提取标题
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        
        materials = []
        
        # 提取图片
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if src:
                src = urljoin(url, src)
                alt = img.get("alt", "")
                materials.append(Material(
                    type="image",
                    content=alt,
                    url=src,
                    title=alt
                ))
        
        # 提取链接
        for link in soup.find_all("a", href=True):
            href = urljoin(url, link.get("href", ""))
            text = link.get_text(strip=True)
            if text and len(text) < 100:
                materials.append(Material(
                    type="link",
                    content=text,
                    url=href,
                    title=text
                ))
        
        # 提取正文
        content = ""
        if parse_content:
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
            content = "\n".join(lines[:200])  # 限制长度
        
        return FetchResult(
            url=url,
            title=title,
            content=content,
            materials=materials,
            success=True
        )
    
    async def search_images(self, query: str, limit: int = 5) -> List[Material]:
        """
        搜索相关图片。
        首版使用 Wikimedia Commons 的公开 API，失败时返回可打开的搜索入口。
        """
        query = query.strip()
        if not query:
            return []

        materials: List[Material] = []
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    "https://commons.wikimedia.org/w/api.php",
                    params={
                        "action": "query",
                        "format": "json",
                        "generator": "search",
                        "gsrsearch": f"{query} filetype:bitmap|drawing",
                        "gsrnamespace": 6,
                        "gsrlimit": limit,
                        "prop": "imageinfo",
                        "iiprop": "url|mime|extmetadata",
                        "iiurlwidth": 900,
                        "origin": "*",
                    },
                )
                resp.raise_for_status()
                pages = resp.json().get("query", {}).get("pages", {})
                for page in pages.values():
                    image_info = (page.get("imageinfo") or [{}])[0]
                    image_url = image_info.get("thumburl") or image_info.get("url")
                    if not image_url:
                        continue
                    title = page.get("title", "").replace("File:", "")
                    materials.append(Material(
                        type="image",
                        content=title,
                        url=image_url,
                        title=title,
                        meta={
                            "source": "wikimedia",
                            "page_url": image_info.get("descriptionurl"),
                            "keyword": query,
                        },
                    ))
                    if len(materials) >= limit:
                        break
        except Exception:
            materials = []

        if materials:
            return materials

        encoded = quote_plus(query)
        return [
            Material(
                type="image",
                content=f"{query} 图片搜索",
                url=f"https://www.bing.com/images/search?q={encoded}",
                title=f"{query} 图片搜索",
                meta={"source": "search_link", "keyword": query},
            )
        ]

    async def search_videos(self, query: str, limit: int = 3) -> List[Material]:
        """返回可用于人工挑选的视频素材搜索入口。"""
        query = query.strip()
        if not query:
            return []

        encoded = quote_plus(query)
        candidates = [
            ("Pexels", f"https://www.pexels.com/search/videos/{encoded}/"),
            ("Pixabay", f"https://pixabay.com/videos/search/{encoded}/"),
            ("Bing", f"https://www.bing.com/videos/search?q={encoded}"),
        ]

        return [
            Material(
                type="video",
                content=f"{query} 视频素材",
                url=url,
                title=f"{source} 视频搜索：{query}",
                meta={"source": source.lower(), "keyword": query},
            )
            for source, url in candidates[:limit]
        ]
