"""
AI 内容生成服务
"""
import re
from typing import AsyncGenerator, Optional
from openai import AsyncOpenAI
from app.core.config import get_model_config
from app.models.schemas import ContentResult, QAPair


SYSTEM_PROMPT = """你是一个专业的知识科普内容创作者。
请将用户提供的主题或内容，整理成"5个问题看懂[主题]"的格式。

输出格式：
【标题】5个问题看懂XXX
【Q1】第一个问题？
【A1】回答内容（50-70字，通俗易懂）
【Q2】第二个问题？
【A2】回答内容
【Q3】第三个问题？
【A3】回答内容
【Q4】第四个问题？
【A4】回答内容
【Q5】第五个问题？
【A5】回答内容
【简介】15-30字简短介绍
【标签】#标签1 #标签2 #标签3

要求：
1. 问题由浅入深：是什么→为什么→怎么办
2. 回答通俗易懂，避免过于专业的术语
3. 数据和事实要准确，必要时联网搜索最新信息
4. 标签2-3个，以#开头
5. 不要输出格式标记以外的内容"""


class AIService:
    """AI 服务"""
    
    def __init__(self, model_name: Optional[str] = None):
        self.config = get_model_config(model_name)
        self.client = AsyncOpenAI(
            api_key=self.config.get("api_key", ""),
            base_url=self.config.get("base_url", ""),
        )
        self.model = self.config.get("model", "deepseek-chat")
        self.supports_search = self.config.get("supports_search", False)
    
    def _build_prompt(self, query: str, web_content: Optional[dict] = None) -> str:
        """构建提示词"""
        if web_content:
            return f"""以下是从网页抓取的参考资料：
网页标题：{web_content.get('title', '')}
网页内容：
{web_content.get('content', '')}

请基于以上网页内容，生成「5个问题看懂」格式的科普内容。"""
        else:
            return f"请针对以下主题/内容，生成「5个问题看懂」格式的科普内容：\n\n{query}"
    
    def _build_regenerate_prompt(self, original_raw: str, instruction: str) -> str:
        """构建重新生成的提示词"""
        return f"""以下是已生成的「5个问题看懂」格式内容：

{original_raw}

请根据用户的以下修改意见，重新生成一份完整的「5个问题看懂」格式内容：

{instruction}"""
    
    async def generate_stream(
        self,
        query: str,
        web_content: Optional[dict] = None,
        original_raw: Optional[str] = None,
        instruction: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """流式生成内容"""
        if original_raw and instruction:
            user_prompt = self._build_regenerate_prompt(original_raw, instruction)
        else:
            user_prompt = self._build_prompt(query, web_content)
        
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "stream": True,
            "temperature": 0.7,
        }
        
        # 添加搜索参数（如果支持）
        if self.supports_search:
            base_url = self.config.get("base_url", "").lower()
            if "deepseek" in base_url:
                kwargs["extra_body"] = {"search": True}
            elif "dashscope" in base_url:
                kwargs["extra_body"] = {"enable_search": True}
        
        async for chunk in await self.client.chat.completions.create(**kwargs):
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    @staticmethod
    def parse_result(raw_text: str) -> ContentResult:
        """解析 AI 输出为结构化结果"""
        result = {
            "title": "",
            "qa_list": [],
            "summary": "",
            "tags": [],
            "raw": raw_text,
        }
        
        # 解析标题
        title_match = re.search(r'【标题】\s*(.+)', raw_text)
        if title_match:
            result["title"] = title_match.group(1).strip()
        
        # 解析问答对
        for i in range(1, 6):
            q_match = re.search(rf'【Q{i}】\s*(.+?)(?=【[AQ\d简标]|$)', raw_text, re.DOTALL)
            a_match = re.search(rf'【A{i}】\s*(.+?)(?=【[QA\d简标]|$)', raw_text, re.DOTALL)
            q_text = q_match.group(1).strip() if q_match else ""
            a_text = a_match.group(1).strip() if a_match else ""
            if q_text or a_text:
                result["qa_list"].append(QAPair(q=q_text, a=a_text))
        
        # 解析简介
        summary_match = re.search(r'【简介】\s*(.+?)(?=【|$)', raw_text, re.DOTALL)
        if summary_match:
            result["summary"] = summary_match.group(1).strip()
        
        # 解析标签
        tags_match = re.search(r'【标签】\s*(.+?)(?=【|$)', raw_text, re.DOTALL)
        if tags_match:
            tags_text = tags_match.group(1).strip()
            result["tags"] = [t.strip() for t in re.findall(r'#\S+', tags_text)]
        
        return ContentResult(**result)
    
    @staticmethod
    def result_to_markdown(result: ContentResult) -> str:
        """转换为 Markdown 用于海报渲染"""
        lines = []
        
        if result.title:
            lines.append(f"# {result.title}")
            lines.append("")
        
        for i, qa in enumerate(result.qa_list, 1):
            if qa.q:
                lines.append(f"**Q{i}: {qa.q}**")
                lines.append("")
            if qa.a:
                lines.append(qa.a)
                lines.append("")
        
        return "\n".join(lines)
