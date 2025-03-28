from repository import repository

class Service:
    _repository: repository

    def __init__(self, _repository):
        self.repository = _repository

    def get_articles_by_year(self, year: int):
        all_articles = self.repository.get_articles()

        return [article for article in all_articles if article.year == year]
    
    def get_article_by_