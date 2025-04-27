import sys
import os
import random
import time
import asyncio
import uvicorn
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Query, WebSocket, BackgroundTasks, UploadFile, File, Response, WebSocketDisconnect, Depends, status
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from services.service import Service
from repository.repository import Repository
from data.domain.article import Article, Coordinates
from datalink.db_connection import SessionLocal
from datalink.models import User

project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
# SECRET_KEY = "secret"
# ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UserBase(BaseModel):
    username: str
    name: str = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str = None

app = FastAPI()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db, username, password):
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return False
        if not verify_password(password, user.password):
            return False
        return user

def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == token_data.username).first()
        if user is None:
            raise credentials_exception
    
    return UserResponse(id=str(user.user_id), username=user.username, name=user.name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(project_root) / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app.mount("/files", StaticFiles(directory=str(UPLOAD_DIR)), name="files")

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    content_type = "application/octet-stream"
    file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if file_extension in ['jpg', 'jpeg', 'png', 'gif']:
        content_type = f"image/{file_extension}"
    elif file_extension == 'pdf':
        content_type = "application/pdf"
    elif file_extension in ['mp4', 'webm']:
        content_type = f"video/{file_extension}"
    
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

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_location = UPLOAD_DIR / file.filename
        
        with open(file_location, "wb") as buffer:
            chunk_size = 1024 * 1024
            while chunk := await file.read(chunk_size):
                buffer.write(chunk)
        
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

active_connections: List[WebSocket] = []

async def broadcast_message(message: dict):
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception as e:
            print(f"Error broadcasting to a client: {e}")
            if connection in active_connections:
                active_connections.remove(connection)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            if data == "start_generation":
                asyncio.create_task(generate_articles_async(websocket))
            elif data == "stop_generation":
                await websocket.send_json({"type": "status", "data": {"message": "Generation stopped"}})
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)

async def generate_articles_async(websocket: WebSocket):
    """Generate random articles asynchronously and send updates via WebSocket"""
    try:
        await websocket.send_json({"type": "status", "data": {"message": "Starting article generation"}})
        
        for i in range(5):
            new_article = generate_random_article(i)
            
            service.add_article(new_article)
            
            await websocket.send_json({
                "type": "new_article", 
                "data": new_article.dict()
            })
            
            await asyncio.sleep(3)
        
        await websocket.send_json({"type": "status", "data": {"message": "Article generation complete"}})
    
    except Exception as e:
        print(f"Error generating articles: {e}")
        await websocket.send_json({"type": "status", "data": {"message": f"Error: {str(e)}"}})

def generate_random_article(counter: int) -> Article:
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
        index=service.get_next_index(),
        user_id=1
    )

@app.get("/health")
def health_check():
    """Simple health check endpoint"""
    return {"status": "ok"}

@app.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    """Register a new user"""
    with SessionLocal() as db:
        existing_user = db.query(User).filter(User.username == user.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            name=user.name or user.username,
            password=hashed_password
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return UserResponse(
            id=str(db_user.user_id),
            username=db_user.username,
            name=db_user.name
        )

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token"""
    with SessionLocal() as db:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: UserResponse = Depends(get_current_user)):
    """Get the current logged in user"""
    return current_user

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
def add_article(article_input: ArticleInput, background_tasks: BackgroundTasks, current_user: UserResponse = Depends(get_current_user)):
    try:

        all_articles = service.get_all_articles()
        for existing_article in all_articles:
            if (existing_article.title.lower() == article_input.title.lower() and
                existing_article.authors.lower() == article_input.authors.lower()):
                print(f"Duplicate article detected: {article_input.title}")
                return existing_article
        
        article = Article(
            authors=article_input.authors,
            title=article_input.title,
            journal=article_input.journal,
            abstract=article_input.abstract,
            year=article_input.year,
            citations=article_input.citations,
            coordinates=Coordinates(x=0.0, y=0.0),
            user_id=int(current_user.id)
        )
        
        saved_article = service.add_article(article)
        
        background_tasks.add_task(
            broadcast_message, 
            {"type": "new_article", "data": saved_article.dict()}
        )

        return saved_article
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/articles/{article_id}")
def update_article(article_id: str, article_input: ArticleInput, background_tasks: BackgroundTasks, current_user: UserResponse = Depends(get_current_user)):
    try:
        all_articles = service.get_all_articles()
        found_article = None
        
        for article in all_articles:
            if hasattr(article, 'id') and article.id == article_id:
                found_article = article
                break
        
        if not found_article:
            try:
                index = int(article_id)
                for article in all_articles:
                    if article.index == index:
                        found_article = article
                        break
            except ValueError:
                print(f"Non-numeric value and not a valid ID: {article_id}")
        
        if found_article:
            if found_article.user_id != int(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to modify this article"
                )
                
            updated_article = Article(
                title=article_input.title,
                authors=article_input.authors,
                journal=article_input.journal,
                abstract=article_input.abstract,
                year=article_input.year,
                citations=article_input.citations,
                coordinates=found_article.coordinates,
                embeddings=found_article.embeddings,
                index=found_article.index,
                user_id=int(current_user.id)
            )
            
            if hasattr(found_article, 'id') and found_article.id:
                updated_article.id = found_article.id
            
            service.update_article(updated_article)
            
            background_tasks.add_task(
                broadcast_message, 
                {"type": "article_updated", "data": updated_article.dict()}
            )
            
            return updated_article
        else:
            raise HTTPException(status_code=404, detail=f"Article with ID/index {article_id} not found")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/articles/{article_id}")
def delete_article(article_id: str, current_user: UserResponse = Depends(get_current_user)):
    try:
        all_articles = service.get_all_articles()
        found_article = None
        
        try:
            index = int(article_id)
            for article in all_articles:
                if article.index == index:
                    found_article = article
                    break
        except ValueError:

            for article in all_articles:
                if hasattr(article, 'id') and article.id == article_id:
                    found_article = article
                    break
        
        if found_article:
            if found_article.user_id != int(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to delete this article"
                )
                
            if isinstance(article_id, int) or article_id.isdigit():
                service.delete_article_by_index(int(article_id))
            else:
                service.delete_article(article_id)
                
            return {"message": "Article deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Article with ID/index {article_id} not found")
    except HTTPException as he:
        raise he
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