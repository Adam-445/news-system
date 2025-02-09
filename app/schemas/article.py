from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, ConfigDict, field_validator
from typing import Optional, List


class ArticleBase(BaseModel):
    title: str
    content: str
    source: Optional[str] = None
    category: Optional[str] = None
    url: str
    published_at: Optional[datetime] = None

    @field_validator("url")
    def validate_url(cls, v):
        return str(HttpUrl(v))


class ArticleCreate(ArticleBase):
    pass


class ArticleResponse(ArticleBase):
    id: int
    views: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    published_at: Optional[datetime] = None
