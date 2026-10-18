import json
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.models.tags import Tags as TagsModel
from core.database import get_db
from schemas.tags import Tags, TagsCreate
from .base import success_response, error_response
from core.auth import get_current_user_or_ak
from core.cache import clear_cache_pattern

# 标签管理API路由
# 提供标签的增删改查功能
# 需要管理员权限执行写操作
router = APIRouter(prefix="/tags", tags=["标签管理"])


from core.tag_util import parse_mps_ids, format_tag_dict



@router.get("", 
    summary="获取标签列表",
    description="分页获取所有标签信息")
async def get_tags(offset: int = 0, limit: int = 100, db: Session = Depends(get_db), cur_user: dict = Depends(get_current_user_or_ak)):
    """
    获取标签列表
    
    参数:
    - offset: 跳过记录数，用于分页
    - limit: 每页记录数，默认100
    
    返回:
    - 包含标签列表和分页信息的成功响应
    """
    query = db.query(TagsModel)
    total = query.count()
    tags = query.order_by(TagsModel.created_at.desc()).offset(offset).limit(limit).all()
    return success_response(data={
        "list": [format_tag_dict(t) for t in tags],
        "page": {
            "limit": limit,
            "offset": offset,
            "total": total
        },
        "total": total
    })


@router.post("",
    summary="创建新标签",
    description="创建一个新的标签"
)
async def create_tag(tag: TagsCreate, db: Session = Depends(get_db), cur_user: dict = Depends(get_current_user_or_ak)):
    """
    创建新标签
    
    参数:
    - tag: TagsCreate模型，包含标签信息
    """
    if not tag.name or not tag.name.strip():
        return error_response(code=400, message="标签名称不能为空")

    try:
        mps_id_str = "[]"
        if tag.mps_id is not None:
            if isinstance(tag.mps_id, list):
                mps_id_str = json.dumps(tag.mps_id, ensure_ascii=False)
            else:
                mps_id_str = str(tag.mps_id)

        db_tag = TagsModel(
            id=str(uuid.uuid4()),
            name=tag.name.strip(),
            cover=tag.cover or '',
            intro=tag.intro or '',
            mps_id=mps_id_str,
            status=tag.status if tag.status is not None else 1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(db_tag)
        db.commit()
        db.refresh(db_tag)
        
        # 清除相关缓存
        clear_cache_pattern("home_page")
        clear_cache_pattern("tag_detail")
        
        return success_response(data=format_tag_dict(db_tag))
    except Exception as e:
        db.rollback()
        from core.print import print_error
        print_error(e)
        return error_response(code=500, message=f"创建标签失败: {str(e)}")


@router.get("/{tag_id}", summary="获取单个标签详情", description="根据标签ID获取标签详细信息")
async def get_tag(tag_id: str, db: Session = Depends(get_db), cur_user: dict = Depends(get_current_user_or_ak)):
    """
    获取单个标签详情
    
    参数:
    - tag_id: 标签ID
    """
    tag = db.query(TagsModel).filter(TagsModel.id == tag_id).first()
    if not tag:
        return error_response(code=404, message="Tag not found")
    return success_response(data=format_tag_dict(tag))


@router.put("/{tag_id}",
    summary="更新标签信息",
    description="根据标签ID更新标签信息"
)
async def update_tag(tag_id: str, tag_data: TagsCreate, db: Session = Depends(get_db), cur_user: dict = Depends(get_current_user_or_ak)):
    """
    更新标签信息
    
    参数:
    - tag_id: 要更新的标签ID
    - tag_data: TagsCreate模型，包含要更新的标签信息
    """
    try:
        tag = db.query(TagsModel).filter(TagsModel.id == tag_id).first()
        if not tag:
            return error_response(code=404, message="Tag not found")
        
        if tag_data.name is not None:
            if not tag_data.name.strip():
                return error_response(code=400, message="标签名称不能为空")
            tag.name = tag_data.name.strip()
        if tag_data.cover is not None:
            tag.cover = tag_data.cover
        if tag_data.intro is not None:
            tag.intro = tag_data.intro
        if tag_data.status is not None:
            tag.status = tag_data.status
        if tag_data.mps_id is not None:
            if isinstance(tag_data.mps_id, list):
                tag.mps_id = json.dumps(tag_data.mps_id, ensure_ascii=False)
            else:
                tag.mps_id = str(tag_data.mps_id)
        tag.updated_at = datetime.now()
        
        db.commit()
        db.refresh(tag)
        
        # 清除相关缓存
        clear_cache_pattern("home_page")
        clear_cache_pattern("tag_detail")
        
        return success_response(data=format_tag_dict(tag))
    except Exception as e:
        db.rollback()
        return error_response(code=500, message=str(e))


@router.delete("/{tag_id}",
    summary="删除标签",
    description="根据标签ID删除标签"
)
async def delete_tag(tag_id: str, db: Session = Depends(get_db), cur_user: dict = Depends(get_current_user_or_ak)):
    """
    删除标签
    
    参数:
    - tag_id: 要删除的标签ID
    """
    try:
        tag = db.query(TagsModel).filter(TagsModel.id == tag_id).first()
        if not tag:
            return error_response(code=404, message="Tag not found")
        db.delete(tag)
        db.commit()
        
        # 清除相关缓存
        clear_cache_pattern("home_page")
        clear_cache_pattern("tag_detail")
        
        return success_response(message="Tag deleted successfully")
    except Exception as e:
        db.rollback()
        return error_response(code=500, message=str(e))