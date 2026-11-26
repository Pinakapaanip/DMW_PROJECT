from pydantic import BaseModel, Field


class SavePaperIn(BaseModel):
    paper_id: str = Field(min_length=1, max_length=80)


class CollectionCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)