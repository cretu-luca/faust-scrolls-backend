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
        # CRITICAL DEBUG: Print all current article indices
        print("\n=== ARTICLES BEFORE ADDING ===")
        for i, art in enumerate(repository.articles):
            art_index = art.index
            print(f"Article [{i}] - index: {art_index} (type: {type(art_index)})")
        
        # Find maximum index value
        max_index = 0
        for article in repository.articles:
            article_index = int(article.index) if article.index is not None else 0
            if article_index > max_index:
                max_index = article_index
        
        # Calculate new index - ensure it's stored as an integer!
        new_index = max_index + 1
        print(f"Highest existing index: {max_index}, assigning new index: {new_index}")
        
        # Create the new article with explicit new index
        article = Article(
            authors=article_input.authors,
            title=article_input.title,
            journal=article_input.journal,
            abstract=article_input.abstract,
            year=article_input.year,
            citations=article_input.citations,
            coordinates=Coordinates(x=0.0, y=0.0),
            index=new_index  # Set as integer
        )
        
        # Don't rely on service to set the index, verify it here
        print(f"Created new article with index: {article.index} (type: {type(article.index)})")
        
        # Add to repository through service
        service.add_article(article)
        
        # Verify the article was added with the correct index
        print("\n=== ARTICLES AFTER ADDING ===")
        for i, art in enumerate(repository.articles):
            art_index = art.index
            art_id = getattr(art, 'id', None)
            print(f"Article [{i}] - index: {art_index} (type: {type(art_index)}), id: {art_id}")
            
            # Verify the added article has the exact expected index
            if i == len(repository.articles) - 1:  # Last item should be our new article
                if art.index != new_index:
                    print(f"WARNING: Added article has index {art.index}, expected {new_index}")
        
        # Return the article with index confirmed
        print(f"Successfully added article with index: {article.index}")
        return article
        
    except Exception as e:
        print(f"Error adding article: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/articles/{article_id}")
def update_article(article_id: str, article_input: ArticleInput):
    try:
        # CRITICAL DEBUG: Dump ALL articles by exact index value to diagnose the issue
        print("\n=== DEBUG: DUMPING ALL ARTICLE INDICES ===")
        print(f"Looking for article with ID/index: {article_id}")
        for i, art in enumerate(repository.articles):
            art_index = art.index
            art_id = getattr(art, 'id', None)
            print(f"Article [{i}] - index: {art_index} (type: {type(art_index)}), id: {art_id}")
        print("============================================\n")
        
        # First check if article_id matches any article.id directly
        found_article = None
        found_index = None
        
        # Check for direct ID match first
        for i, article in enumerate(repository.articles):
            if hasattr(article, 'id') and article.id == article_id:
                found_article = article
                found_index = i
                print(f"Found article by ID match at position {i}")
                break
        
        # If not found by ID, try as an index
        if not found_article:
            try:
                index = int(article_id)
                print(f"Parsed index: {index} (type: {type(index)})")
                
                # DIRECT LOOKUP: Find article directly in repository by exact index
                for i, article in enumerate(repository.articles):
                    # Force string comparison to match exactly what's stored
                    article_index_str = str(article.index)
                    article_id_str = str(article_id)
                    print(f"Checking #{i}: article index={article_index_str}, requested={article_id_str}")
                    
                    # Try both integer and string comparisons
                    if str(article.index) == str(index) or article.index == index:
                        found_article = article
                        found_index = i
                        print(f"MATCH FOUND at position {i}!")
                        break
            except ValueError:
                # Only treat as non-numeric ID if we couldn't parse as int AND couldn't find as ID
                print(f"Non-numeric value and not a valid ID: {article_id}")
        
        if found_article:
            print(f"Found article: {found_article}")
            # Update article with new values
            updated_article = Article(
                title=article_input.title,
                authors=article_input.authors,
                journal=article_input.journal,
                abstract=article_input.abstract,
                year=article_input.year,
                citations=article_input.citations,
                coordinates=found_article.coordinates,
                embeddings=found_article.embeddings,
                index=found_article.index  # Keep the original index
            )
            
            # Keep the original ID
            if hasattr(found_article, 'id') and found_article.id:
                updated_article.id = found_article.id
            
            # Update the article in place using service
            try:
                service.update_article(updated_article)
                print(f"Successfully updated article at index {found_article.index}")
                return updated_article
            except Exception as e:
                print(f"Error updating article through service: {str(e)}")
                # Direct update as fallback
                repository.articles[found_index] = updated_article
                print(f"Fallback: directly updated article at index {found_article.index}")
                return updated_article
        else:
            # This is the key error - be VERY explicit to help diagnose
            print(f"ERROR: Article with ID/index {article_id} NOT FOUND in repository")
            all_indices = [str(a.index) for a in repository.articles]
            print(f"Available indices: {all_indices}")
            
            raise HTTPException(status_code=404, detail=f"Article with ID/index {article_id} not found")
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/articles/{article_id}")
def delete_article(article_id: str):
    try:
        # Try to parse as an index first
        try:
            index = int(article_id)
            # Find article by index
            all_articles = service.get_all_articles()
            for article in all_articles:
                if article.index == index:
                    service.delete_article_by_index(index)
                    return {"message": "Article deleted successfully"}
            
            raise HTTPException(status_code=404, detail=f"Article with index {index} not found")
        except ValueError:
            # If not an integer, treat as ID
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