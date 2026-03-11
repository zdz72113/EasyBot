"""
AI 内容生成服务
使用 OpenAI 兼容接口调用 DeepSeek / 通义千问
支持流式输出和结构化解析
"""

import re
from typing import Generator, Optional

from openai import OpenAI

from config import SYSTEM_PROMPT


def build_user_prompt(user_input: str, web_content: Optional[dict] = None) -> str:
    """构建用户提示词"""
    parts = []

    if web_content and web_content.get("success"):
        parts.append("以下是从网页抓取的参考资料：")
        if web_content.get("title"):
            parts.append(f"网页标题：{web_content['title']}")
        parts.append(f"网页内容：\n{web_content['content']}")
        parts.append(f"\n请基于以上网页内容，生成「5个问题看懂」格式的科普内容。")
    else:
        parts.append(f"请针对以下主题/内容，利用你的知识（如有需要请联网搜索最新信息），生成「5个问题看懂」格式的科普内容：")
        parts.append(f"\n{user_input}")

    return "\n".join(parts)


def build_regenerate_prompt(original_raw: str, adjustment_instruction: str) -> str:
    """构建重新生成时的用户提示词（在原有内容基础上按用户修改意见调整）"""
    return (
        "以下是已生成的「5个问题看懂」格式内容：\n\n"
        f"{original_raw}\n\n"
        "请根据用户的以下修改意见，重新生成一份完整的「5个问题看懂」格式内容（标题、简介、5 个 Q&A、标签等结构保持一致）：\n\n"
        f"{adjustment_instruction}"
    )


def generate_q5_stream(
    user_input: str,
    model_config: dict,
    web_content: Optional[dict] = None,
    original_raw: Optional[str] = None,
    adjustment_instruction: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    流式生成 Q5 内容。
    若提供 original_raw 与 adjustment_instruction，则按「在原有内容上按修改意见重新生成」构建提示词。

    Yields:
        每次返回一个文本 chunk
    """
    client = OpenAI(
        api_key=model_config["api_key"],
        base_url=model_config["base_url"],
    )

    if original_raw is not None and adjustment_instruction is not None:
        user_prompt = build_regenerate_prompt(original_raw, adjustment_instruction)
    else:
        user_prompt = build_user_prompt(user_input, web_content)

    kwargs = {
        "model": model_config["model"],
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "stream": True,
        "temperature": 0.7,
    }

    if model_config.get("supports_search"):
        model_name = model_config.get("model", "")
        if "deepseek" in model_config.get("base_url", "").lower():
            kwargs["extra_body"] = {"search": True}
        elif "dashscope" in model_config.get("base_url", "").lower():
            kwargs["extra_body"] = {"enable_search": True}

    response = client.chat.completions.create(**kwargs)

    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def parse_q5_result(raw_text: str) -> dict:
    """
    解析 AI 输出的结构化文本

    Returns:
        {
            "title": str,
            "qa_list": [{"q": str, "a": str}, ...],
            "summary": str,
            "tags": [str, ...],
            "raw": str,
        }
    """
    result = {
        "title": "",
        "qa_list": [],
        "summary": "",
        "tags": [],
        "raw": raw_text,
    }

    title_match = re.search(r'【标题】\s*(.+)', raw_text)
    if title_match:
        result["title"] = title_match.group(1).strip()

    for i in range(1, 6):
        q_match = re.search(rf'【Q{i}】\s*(.+?)(?=【[AQ\d简标]|$)', raw_text, re.DOTALL)
        a_match = re.search(rf'【A{i}】\s*(.+?)(?=【[QA\d简标]|$)', raw_text, re.DOTALL)
        q_text = q_match.group(1).strip() if q_match else ""
        a_text = a_match.group(1).strip() if a_match else ""
        if q_text or a_text:
            result["qa_list"].append({"q": q_text, "a": a_text})

    summary_match = re.search(r'【简介】\s*(.+?)(?=【|$)', raw_text, re.DOTALL)
    if summary_match:
        result["summary"] = summary_match.group(1).strip()

    tags_match = re.search(r'【标签】\s*(.+?)(?=【|$)', raw_text, re.DOTALL)
    if tags_match:
        tags_text = tags_match.group(1).strip()
        result["tags"] = [t.strip() for t in re.findall(r'#\S+', tags_text)]

    return result


def result_to_markdown(result: dict) -> str:
    """将解析结果转换为 Markdown 格式（用于海报渲染）"""
    lines = []

    if result.get("title"):
        lines.append(f"# {result['title']}")
        lines.append("")

    for i, qa in enumerate(result.get("qa_list", []), 1):
        if qa.get("q"):
            lines.append(f"**Q{i}: {qa['q']}**")
            lines.append("")
        if qa.get("a"):
            lines.append(qa["a"])
            lines.append("")

    if result.get("summary"):
        lines.append(f"> {result['summary']}")

    return "\n".join(lines)
