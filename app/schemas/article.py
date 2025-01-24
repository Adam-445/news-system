from datetime import datetime
from pydantic import BaseModel

class ArticleBase(BaseModel):
    title: str
    content: str

class ArticleCreate(ArticleBase):
    pass

class ArticleResponse(ArticleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True