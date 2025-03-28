from pydantic import BaseModel, Field

class Coordinates(BaseModel):
    x: float
    y: float

class Article(BaseModel):
    authors: str
    title: str
    journal: str
    abstract: str
    year: int
    citations: int
    coordinates: Coordinates
    embeddings: list[int]