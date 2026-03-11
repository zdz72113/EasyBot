"""
历史记录管理模块
使用 JSON 文件存储生成记录
"""

import json
import os
import uuid
from datetime import datetime
from typing import List, Optional

from config import HISTORY_DIR, HISTORY_MAX_RECORDS


def _ensure_dir():
    os.makedirs(HISTORY_DIR, exist_ok=True)


def _history_file() -> str:
    _ensure_dir()
    return os.path.join(HISTORY_DIR, "records.json")


def _load_all() -> List[dict]:
    path = _history_file()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_all(records: List[dict]):
    path = _history_file()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def save_record(input_text: str, result: dict) -> str:
    """
    保存一条记录

    Args:
        input_text: 用户输入
        result: 解析后的结构化结果

    Returns:
        记录 ID
    """
    records = _load_all()
    record_id = uuid.uuid4().hex[:12]

    record = {
        "id": record_id,
        "timestamp": datetime.now().isoformat(),
        "input_text": input_text,
        "title": result.get("title", ""),
        "qa_list": result.get("qa_list", []),
        "summary": result.get("summary", ""),
        "tags": result.get("tags", []),
        "raw": result.get("raw", ""),
    }

    records.insert(0, record)

    if len(records) > HISTORY_MAX_RECORDS:
        records = records[:HISTORY_MAX_RECORDS]

    _save_all(records)
    return record_id


def load_records() -> List[dict]:
    """加载所有记录（按时间倒序）"""
    return _load_all()


def load_record(record_id: str) -> Optional[dict]:
    """加载单条记录"""
    for r in _load_all():
        if r.get("id") == record_id:
            return r
    return None


def delete_record(record_id: str) -> bool:
    """删除一条记录"""
    records = _load_all()
    new_records = [r for r in records if r.get("id") != record_id]
    if len(new_records) < len(records):
        _save_all(new_records)
        return True
    return False


def update_record(record_id: str, updated: dict) -> bool:
    """更新一条历史记录的内容字段"""
    records = _load_all()
    for r in records:
        if r.get("id") == record_id:
            r["title"] = updated.get("title", r.get("title", ""))
            r["qa_list"] = updated.get("qa_list", r.get("qa_list", []))
            r["summary"] = updated.get("summary", r.get("summary", ""))
            r["tags"] = updated.get("tags", r.get("tags", []))
            r["raw"] = updated.get("raw", r.get("raw", ""))
            _save_all(records)
            return True
    return False
