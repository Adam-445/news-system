from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from uuid import UUID



class UserPreferenceBase(BaseModel):
    preferred_categories: Optional[List[str]] = None
    preferred_sources: Optional[List[str]] = None
    saved_articles: Optional[List[int]] = None


class UserPreferenceResponse(UserPreferenceBase):
    user_id: str

    model_config = ConfigDict(from_attributes=True)


class UserPreferenceUpdate(UserPreferenceBase):
    user_id: UUID
