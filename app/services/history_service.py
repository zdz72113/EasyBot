"""
历史记录管理服务
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from app.models.schemas import HistoryRecord, ContentResult
from app.core.config import settings


class HistoryService:
    """历史记录服务"""
    
    def __init__(self):
        self.history_dir = settings.HISTORY_DIR
        self.history_dir.mkdir(exist_ok=True)
    
    def _get_record_path(self, record_id: str) -> Path:
        """获取记录文件路径"""
        return self.history_dir / f"{record_id}.json"
    
    def save_record(self, query: str, result: ContentResult) -> str:
        """保存记录"""
        record_id = str(uuid.uuid4())[:8]
        
        record = {
            "id": record_id,
            "query": query,
            "title": result.title,
            "qa_list": [qa.model_dump() for qa in result.qa_list],
            "summary": result.summary,
            "tags": result.tags,
            "raw": result.raw,
            "created_at": datetime.now().isoformat(),
        }
        
        path = self._get_record_path(record_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        
        return record_id
    
    def update_record(self, record_id: str, result: ContentResult) -> bool:
        """更新记录"""
        path = self._get_record_path(record_id)
        if not path.exists():
            return False
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                record = json.load(f)
            
            record.update({
                "title": result.title,
                "qa_list": [qa.model_dump() for qa in result.qa_list],
                "summary": result.summary,
                "tags": result.tags,
                "raw": result.raw,
            })
            
            with open(path, "w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception:
            return False
    
    def get_record(self, record_id: str) -> Optional[HistoryRecord]:
        """获取单条记录"""
        path = self._get_record_path(record_id)
        if not path.exists():
            return None
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return HistoryRecord(**data)
        except Exception:
            return None
    
    def list_records(self, limit: int = 100) -> List[HistoryRecord]:
        """列出所有记录"""
        records = []
        
        for path in sorted(self.history_dir.glob("*.json"), reverse=True):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                records.append(HistoryRecord(**data))
            except Exception:
                continue
        
        return records[:limit]
    
    def delete_record(self, record_id: str) -> bool:
        """删除记录"""
        path = self._get_record_path(record_id)
        if path.exists():
            path.unlink()
            return True
        return False
