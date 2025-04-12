from datetime import datetime
from typing import Optional

from pydantic import UUID4, BaseModel, ConfigDict, HttpUrl, field_validator


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
    id: UUID4
    views: int
    is_deleted: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    published_at: Optional[datetime] = None


class ArticleFilters(BaseModel):
    category: Optional[str] = None
    source: Optional[str] = None
    keyword: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sort_by: Optional[str] = "published_at"
    order: Optional[str] = "desc"
