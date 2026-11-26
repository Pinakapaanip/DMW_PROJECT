from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    department: str = Field(default="", max_length=180)
    bio: str = Field(default="", max_length=1000)
    interests: list[str] = Field(default_factory=list, max_length=50)