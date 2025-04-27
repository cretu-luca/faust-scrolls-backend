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
    embeddings: list[float] = Field(default_factory=list)
    index: int = None
    id: str = None
    user_id: int = None
    
    def __init__(self, **data):
        if 'index' in data and data['index'] is not None:
            try:
                data['index'] = int(data['index'])
            except (ValueError, TypeError):
                print(f"WARNING: Invalid index value: {data['index']}, type: {type(data['index'])}")
        
        super().__init__(**data)