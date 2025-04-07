import sys
from pathlib import Path
import os

project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from services.service import Service
from repository.repository import Repository
from data.domain.article import Article, Coordinates
from fastapi import FastAPI, HTTPException, Query, WebSocket, BackgroundTasks, UploadFile, File, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import asyncio
import random
import time
import shutil
from typing import List, Dict, Any

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path(project_root) / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Mount the uploads directory to make files accessible via HTTP
app.mount("/files", StaticFiles(directory=str(UPLOAD_DIR)), name="files")

# Add direct download endpoint with proper headers
@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine content type
    content_type = "application/octet-stream"  # Default for unknown file types
    file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if file_extension in ['jpg', 'jpeg', 'png', 'gif']:
        content_type = f"image/{file_extension}"
    elif file_extension == 'pdf':
        content_type = "application/pdf"
    elif file_extension in ['mp4', 'webm']:
        content_type = f"video/{file_extension}"
    
    # Return file with Content-Disposition header to force download
    headers = {
        "Content-Disposition": f"attachment; filename={filename}"
    }
    
    return Response(
        content=file_path.read_bytes(),
        media_type=content_type,
        headers=headers
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

# File upload endpoints
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Generate a safe filename
        file_location = UPLOAD_DIR / file.filename
        
        # Save the file in chunks to handle large files efficiently
        with open(file_location, "wb") as buffer:
            # Read and write the file in chunks of 1MB
            chunk_size = 1024 * 1024  # 1MB chunks
            while chunk := await file.read(chunk_size):
                buffer.write(chunk)
        
        # Return success response with file info
        file_size = os.path.getsize(file_location)
        
        print(f"File uploaded successfully: {file.filename}, Size: {file_size} bytes")
        
        return {
            "filename": file.filename,
            "size": file_size,
            "url": f"/files/{file.filename}"
        }
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.get("/api/files/list")
async def list_files():
    try:
        files = []
        for file_path in UPLOAD_DIR.glob("*"):
            if file_path.is_file():
                files.append({
                    "filename": file_path.name,
                    "size": os.path.getsize(file_path),
                    "url": f"/files/{file_path.name}",
                    "uploaded_at": os.path.getctime(file_path)
                })
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

@app.delete("/api/files/{filename}")
async def delete_file(filename: str):
    try:
        file_path = UPLOAD_DIR / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        os.remove(file_path)
        return {"message": f"File {filename} deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

# WebSocket connections store
active_connections: List[WebSocket] = []

# WebSocket connection management
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Wait for client messages
            data = await websocket.receive_text()
            
            if data == "start_generation":
                # Start background task to generate articles
                asyncio.create_task(generate_articles_async(websocket))
            elif data == "stop_generation":
                # Client wants to stop (implementation would require a more sophisticated
                # mechanism to track and stop specific generation tasks)
                await websocket.send_json({"type": "status", "data": {"message": "Generation stopped"}})
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Remove connection when client disconnects
        if websocket in active_connections:
            active_connections.remove(websocket)

# Background task to generate articles
async def generate_articles_async(websocket: WebSocket):
    """Generate random articles asynchronously and send updates via WebSocket"""
    try:
        # Send initial status
        await websocket.send_json({"type": "status", "data": {"message": "Starting article generation"}})
        
        # Generate 5 articles with a delay between each
        for i in range(5):
            # Create a random article
            new_article = generate_random_article(i)
            
            # Add article to repository
            service.add_article(new_article)
            
            # Broadcast to client
            await websocket.send_json({
                "type": "new_article", 
                "data": new_article.dict()
            })
            
            # Wait for 3 seconds before generating next article
            await asyncio.sleep(3)
        
        # Send completion status
        await websocket.send_json({"type": "status", "data": {"message": "Article generation complete"}})
    
    except Exception as e:
        print(f"Error generating articles: {e}")
        await websocket.send_json({"type": "status", "data": {"message": f"Error: {str(e)}"}})

# Helper function to generate random articles
def generate_random_article(counter: int) -> Article:
    """Generate a random article for demonstration purposes"""
    journals = ["Nature", "Science", "Cell", "PNAS", "Physical Review Letters"]
    topics = ["Quantum Computing", "Machine Learning", "Climate Change", "Genetic Engineering", "Neuroscience"]
    
    current_time = int(time.time())
    title = f"Generated Article on {topics[counter % len(topics)]} #{current_time}"
    
    return Article(
        title=title,
        authors=f"Auto Generator Bot {counter+1}",
        journal=journals[counter % len(journals)],
        abstract=f"This is an automatically generated article abstract with random data for demonstration purposes. Topic: {topics[counter % len(topics)]}",
        year=random.randint(2010, 2024),
        citations=random.randint(0, 50000),
        coordinates=Coordinates(x=random.uniform(-50, 50), y=random.uniform(-50, 50)),
        index=service.get_next_index()
    )

@app.get("/health")
def health_check():
    """
    Health check endpoint to verify server availability
    """
    return {"status": "ok", "message": "Server is running"}

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