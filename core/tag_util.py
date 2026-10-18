import json
from typing import List, Any, Dict

def parse_mps_ids(mps_id_data: Any) -> List[str]:
    """安全解析公众号ID集合，兼容字符串、字典对象或已解析的列表"""
    if not mps_id_data:
        return []
    try:
        raw = json.loads(mps_id_data) if isinstance(mps_id_data, str) else mps_id_data
        if not isinstance(raw, list):
            return []
        ids: List[str] = []
        for item in raw:
            if isinstance(item, dict) and "id" in item:
                ids.append(str(item["id"]))
            elif isinstance(item, (str, int)):
                ids.append(str(item))
        return ids
    except Exception:
        return []

def format_tag_dict(tag: Any) -> Dict[str, Any]:
    """格式化标签输出字典"""
    mps_ids = parse_mps_ids(getattr(tag, "mps_id", None))
    created_at = getattr(tag, "created_at", None)
    updated_at = getattr(tag, "updated_at", None)
    return {
        "id": getattr(tag, "id", ""),
        "name": getattr(tag, "name", "") or "",
        "cover": getattr(tag, "cover", "") or "",
        "intro": getattr(tag, "intro", "") or "",
        "status": getattr(tag, "status", 1) if getattr(tag, "status", None) is not None else 1,
        "mps_id": getattr(tag, "mps_id", "") or "[]",
        "mps_list": mps_ids,
        "mp_count": len(mps_ids),
        "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at and hasattr(created_at, "strftime") else (str(created_at) if created_at else ""),
        "updated_at": updated_at.strftime("%Y-%m-%d %H:%M:%S") if updated_at and hasattr(updated_at, "strftime") else (str(updated_at) if updated_at else ""),
    }
