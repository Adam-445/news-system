from .article import ArticleBase, ArticleCreate, ArticleResponse, ArticleUpdate
from .user import UserBase, UserCreate, UserResponse, UserUpdate

# Optional: Group imports for easier access in other files
__all__ = [
    "ArticleCreate",
    "ArticleBase",
    "ArticleResponse"
    "ArticleUpdate",
    "UserBase",
    "UserCreate",
    "UserResponse",
    "UserUpdate"
]