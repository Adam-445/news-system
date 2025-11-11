from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserPreferenceBase(BaseModel):
    preferred_categories: Optional[List[str]] = None
    preferred_sources: Optional[List[str]] = None
    saved_articles: Optional[List[int]] = None


class UserPreferenceResponse(UserPreferenceBase):
    user_id: UUID

    model_config = ConfigDict(from_attributes=True)


class UserPreferenceUpdate(UserPreferenceBase):
    pass
