import sys
from pathlib import Path

project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from services.service import Service
from repository.repository import Repository
from fastapi import FastAPI
import uvicorn

app = FastAPI()

repository = Repository()
service = Service(repository)

@app.get("/all_articles")
def get_all():
    return service.get_all_articles()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)