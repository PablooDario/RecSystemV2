from pydantic import BaseModel
from typing import Optional

class ActorResponse(BaseModel):
    id: int
    tmdb_id: Optional[int]
    name: str
    profile_path: Optional[str]