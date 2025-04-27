from sqlalchemy.orm import Session
from . import models
from data.domain import Article as DomainArticle, Coordinates
from typing import List, Optional

class DataLink:
    def get_articles(self, db: Session) -> List[DomainArticle]:
        db_articles = db.query(models.Article).all()
        return [self._map_to_domain_article(article) for article in db_articles]
    
    def get_articles_by_year(self, db: Session, year: int) -> List[DomainArticle]:
        db_articles = db.query(models.Article).filter(models.Article.year == year).all()
        return [self._map_to_domain_article(article) for article in db_articles]
    
    def add_article(self, db: Session, article: DomainArticle) -> DomainArticle:
        db_article = models.Article(
            user_id=article.user_id,
            title=article.title,
            content=article.abstract,
            abstract=article.abstract,
            year=article.year,
            citations=article.citations,
            authors=article.authors,
            journal=article.journal,
            coordinate_x=article.coordinates.x if article.coordinates else 0.0,
            coordinate_y=article.coordinates.y if article.coordinates else 0.0,
            embeddings=article.embeddings if article.embeddings else []
        )
        db.add(db_article)
        db.commit()
        db.refresh(db_article)
        return self._map_to_domain_article(db_article)
    
    def update_article(self, db: Session, article: DomainArticle) -> Optional[DomainArticle]:
        article_id = int(article.id) if article.id else article.index
        db_article = db.query(models.Article).filter(models.Article.article_id == article_id).first()
        if not db_article:
            return None
            
        db_article.title = article.title
        db_article.content = article.abstract
        db_article.abstract = article.abstract
        db_article.year = article.year
        db_article.citations = article.citations
        db_article.authors = article.authors
        db_article.journal = article.journal
        if article.coordinates:
            db_article.coordinate_x = article.coordinates.x
            db_article.coordinate_y = article.coordinates.y
        db_article.embeddings = article.embeddings if article.embeddings else []
        
        db.commit()
        db.refresh(db_article)
        return self._map_to_domain_article(db_article)
    
    def delete_article(self, db: Session, article_id: int) -> bool:
        db_article = db.query(models.Article).filter(models.Article.article_id == article_id).first()
        if not db_article:
            return False
            
        db.delete(db_article)
        db.commit()
        return True
    
    def _map_to_domain_article(self, db_article: models.Article) -> DomainArticle:
        coordinates = Coordinates(
            x=db_article.coordinate_x,
            y=db_article.coordinate_y
        )
        
        return DomainArticle(
            id=str(db_article.article_id),
            index=db_article.article_id,
            title=db_article.title,
            abstract=db_article.content or db_article.abstract or "",
            authors=db_article.authors,
            journal=db_article.journal,
            year=db_article.year,
            citations=db_article.citations,
            coordinates=coordinates,
            embeddings=db_article.embeddings or [],
            user_id=db_article.user_id
        )