from pydantic import BaseModel, Field


class PostCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
    tags: list[str] = Field(default_factory=list, max_length=20)


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)