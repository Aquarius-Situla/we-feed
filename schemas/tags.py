from datetime import datetime
from typing import Optional, Union, List, Any
from pydantic import BaseModel
import json

class TagsBase(BaseModel):
    name: str
    cover: Optional[str] = ""
    intro: Optional[str] = ""
    mps_id: Optional[Union[str, List[Any]]] = "[]"
    status: Optional[int] = 1

class TagsCreate(TagsBase):
    pass

class Tags(TagsBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True