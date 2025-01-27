from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List

class ArticleBase(BaseModel):
    title: str
    content: str
    source: Optional[str] = Field(None, example="CNN")
    category: Optional[str] = Field(None, example="tech")
    url: HttpUrl  # Ensure valid URL format
    published_at: Optional[datetime] = None

class ArticleCreate(ArticleBase):
    pass

class ArticleResponse(ArticleBase):
    id: int
    embedding: Optional[List[float]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None