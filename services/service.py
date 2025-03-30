from repository.repository import Repository
from data.domain.article import Article, Coordinates
from services.abstracts_encoder import AbstractsEncoder

class Service:
    _repository: Repository

    def __init__(self, repository: Repository):
        self.repository = repository
        # self.abstracts_encoder = AbstractsEncoder()

    def get_articles_by_year(self, year: int):
        all_articles = self.repository.get_articles()

        return [article for article in all_articles if article.year == year]

    def get_all_articles(self):
        return self.repository.get_articles()
    
    def get_sorted_articles(self, sort_by: str = 'citations', order: str = 'desc'):
        articles = self.repository.get_articles()
        
        if sort_by == 'citations':
            reverse = order.lower() == 'desc'
            return sorted(articles, key=lambda article: article.citations, reverse=reverse)
        elif sort_by == 'year':
            reverse = order.lower() == 'desc'
            return sorted(articles, key=lambda article: article.year, reverse=reverse)
        else:
            return articles
    
    def add_article(self, article: Article):
        # article.embeddings = self.abstracts_encoder.encode(article.abstract)
        # article.coordinates = self.abstracts_encoder.get_coordinates(article.embeddings)

        article.embeddings = [0.1, 0.2, 0.3]
        article.coordinates = Coordinates(x=0.1, y=0.2)

        self.repository.add_article(article)

    def update_article(self, article: Article):
        # article.embeddings = self.abstracts_encoder.encode(article.abstract)
        # article.coordinates = self.abstracts_encoder.get_coordinates(article.embeddings)

        article.embeddings = [0.1, 0.2, 0.3]
        article.coordinates = Coordinates(x=0.1, y=0.2)

        self.repository.update_article(article)

    def delete_article(self, article_id: str):
        self.repository.delete_article(article_id)
    
    def delete_article_by_index(self, index: int):
        self.repository.delete_article_by_index(index)
        
    def search_articles(self, query: str):
        if not query:
            return self.get_all_articles()
            
        all_articles = self.get_all_articles()
        results = []
        
        query_lower = query.lower()
        for article in all_articles:
            searchable_text = f"{article.title} {article.authors} {article.abstract} {article.journal}".lower()
            if query_lower in searchable_text:
                results.append(article)
                
        return results