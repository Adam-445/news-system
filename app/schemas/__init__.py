from .article import ArticleBase, ArticleCreate, ArticleResponse, ArticleUpdate, ArticleFilters
from .user import UserBase, UserCreate, UserResponse, UserUpdate, Token, TokenData
from .preference import UserPreferenceResponse, UserPreferenceUpdate
from .role import RoleCreate, RoleResponse, RoleUpdate
from .permission import PermissionCreate, PermissionResponse

# Optional: Group imports for easier access in other files
__all__ = [
    "ArticleCreate",
    "ArticleBase",
    "ArticleResponse",
    "ArticleUpdate",
    "ArticleFilters",
    "UserBase",
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    "Token",
    "TokenData",
    "UserPreferenceResponse",
    "UserPreferenceUpdate",
    "RoleCreate",
    "RoleResponse",
    "RoleUpdate",
    "PermissionCreate",
    "PermissionResponse"
]