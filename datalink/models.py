from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from .db_connection import Base

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    
    articles = relationship("Article", back_populates="user", cascade="all, delete-orphan")

class Article(Base):
    __tablename__ = "articles"
    
    article_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    title = Column(Text, nullable=False)
    content = Column(Text)
    abstract = Column(Text)
    year = Column(Integer)
    citations = Column(Integer, default=0)
    authors = Column(Text, nullable=False, default="Unknown")
    journal = Column(Text, nullable=False, default="Unknown")
    coordinate_x = Column(Float, default=0.0)
    coordinate_y = Column(Float, default=0.0)
    embeddings = Column(ARRAY(Float), default=[])
    
    user = relationship("User", back_populates="articles")