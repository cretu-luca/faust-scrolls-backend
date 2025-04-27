import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datalink.db_connection import SessionLocal, Base, engine
from datalink.models import User, Article
from sqlalchemy.orm import Session

Base.metadata.create_all(bind=engine)

def import_articles_from_json(json_file_path):
    with SessionLocal() as db:
        default_user = db.query(User).first()
        if not default_user:
            default_user = User(
                name="Admin User",
                username="admin",
                password="hashed_password_here"
            )
            db.add(default_user)
            db.commit()
            db.refresh(default_user)
            print(f"Created default user with ID: {default_user.user_id}")
        
        with open(json_file_path, 'r') as file:
            articles_data = json.load(file)
        
        for article_data in articles_data:
            article = Article(
                user_id=default_user.user_id,
                title=article_data.get('title', '').replace('\n', ' ').strip(),
                content=article_data.get('abstract', ''),
                abstract=article_data.get('abstract', ''),
                year=int(article_data.get('year', 0)),
                citations=int(article_data.get('citations', 0)),
                authors=article_data.get('authors', 'Unknown'),
                journal=article_data.get('journal', 'Unknown'),
                coordinate_x=float(article_data.get('coordinates', {}).get('x', 0.0)),
                coordinate_y=float(article_data.get('coordinates', {}).get('y', 0.0)),
                embeddings=article_data.get('embedding', [])
            )
            
            db.add(article)
        
        db.commit()
        print(f"Imported {len(articles_data)} articles into the database")

if __name__ == "__main__":
    json_file_path = "/Users/cretuluca/uni/faust-scrolls-full/faust-scrolls-backend/data/raw/articles-with-embeddings.json"
    import_articles_from_json(json_file_path)