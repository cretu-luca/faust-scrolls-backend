import sys
from pathlib import Path

project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from services.service import Service
from repository.repository import Repository
from data.domain.article import Article, Coordinates
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ArticleInput(BaseModel):
    title: str
    authors: str
    journal: str
    citations: int
    year: int
    abstract: str

repository = Repository()
service = Service(repository)

@app.get("/all_articles")
def get_all():
    return service.get_all_articles()

@app.get("/sorted_articles")
def get_sorted_articles(sort_by: str = 'citations', order: str = 'desc'):
    return service.get_sorted_articles(sort_by, order)

@app.get("/articles_by_year")
def get_articles_by_year(year: int):
    return service.get_articles_by_year(year)

@app.get("/article/{index}")
def get_article_by_index(index: int):
    try:
        all_articles = service.get_all_articles()

        for article in all_articles:
            if article.index == index:
                return article
        
        raise HTTPException(status_code=404, detail=f"Article with index {index} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add_article")
def add_article(article_input: ArticleInput):
    try:

        max_index = 0
        for article in repository.articles:
            article_index = int(article.index) if article.index is not None else 0
            if article_index > max_index:
                max_index = article_index
        
        new_index = max_index + 1
        
        article = Article(
            authors=article_input.authors,
            title=article_input.title,
            journal=article_input.journal,
            abstract=article_input.abstract,
            year=article_input.year,
            citations=article_input.citations,
            coordinates=Coordinates(x=0.0, y=0.0),
            index=new_index
        )
        
        service.add_article(article)

        return article
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/articles/{article_id}")
def update_article(article_id: str, article_input: ArticleInput):
    try:
        found_article = None
        found_index = None
        
        for i, article in enumerate(repository.articles):
            if hasattr(article, 'id') and article.id == article_id:
                found_article = article
                found_index = i
                break
        
        if not found_article:
            try:
                index = int(article_id)
                
                for i, article in enumerate(repository.articles):
                    article_index_str = str(article.index)
                    article_id_str = str(article_id)

                    if str(article.index) == str(index) or article.index == index:
                        found_article = article
                        found_index = i
                        break
            except ValueError:
                print(f"Non-numeric value and not a valid ID: {article_id}")
        
        if found_article:
            updated_article = Article(
                title=article_input.title,
                authors=article_input.authors,
                journal=article_input.journal,
                abstract=article_input.abstract,
                year=article_input.year,
                citations=article_input.citations,
                coordinates=found_article.coordinates,
                embeddings=found_article.embeddings,
                index=found_article.index
            )
            
            if hasattr(found_article, 'id') and found_article.id:
                updated_article.id = found_article.id
            
            try:
                service.update_article(updated_article)
                return updated_article
            except Exception as e:
                repository.articles[found_index] = updated_article
                return updated_article
        else:
            raise HTTPException(status_code=404, detail=f"Article with ID/index {article_id} not found")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/articles/{article_id}")
def delete_article(article_id: str):
    try:
        try:
            index = int(article_id)
            all_articles = service.get_all_articles()
            for article in all_articles:
                if article.index == index:
                    service.delete_article_by_index(index)
                    return {"message": "Article deleted successfully"}
            
            raise HTTPException(status_code=404, detail=f"Article with index {index} not found")
        except ValueError:
            service.delete_article(article_id)
            return {"message": "Article deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
def search_articles(query: str = Query(..., min_length=1)):
    try:
        results = service.search_articles(query)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)