from data.domain.article import Article

class ValidationService:
    def validate_article(self, article: Article) -> bool:
        if article.title is None or article.title == "":
            return False
        
        if article.authors is None or article.authors == "":
            return False
        
        if article.journal is None or article.journal == "":
            return False

        if article.abstract is None or article.abstract == "":
            return False

        if article.year is None or article.year == "":
            return False
        
        if article.citations is None or article.citations == "":
            return False
        
        if article.year < 0 or article.year > 2025:
            return False
        
        if article.citations < 0:
            return False
        
        return True