import unittest
from unittest.mock import Mock, patch
from services.service import Service
from data.domain.article import Article, Coordinates

class TestService(unittest.TestCase):
    def setUp(self):
        self.mock_repository = Mock()
        self.service = Service(self.mock_repository)
        
        self.test_article = Article(
            authors="Test Author",
            title="Test Title",
            journal="Test Journal",
            abstract="Test Abstract",
            year=2024,
            citations=10,
            coordinates=Coordinates(x=0.1, y=0.2)
        )

    def test_get_all_articles(self):
        expected_articles = [self.test_article]
        self.mock_repository.get_articles.return_value = expected_articles
        
        result = self.service.get_all_articles()
        
        self.assertEqual(result, expected_articles)
        self.mock_repository.get_articles.assert_called_once()

    def test_get_articles_by_year(self):
        articles = [
            Article(authors="Author 1", title="Title 1", journal="Journal 1", 
                   abstract="Abstract 1", year=2024, citations=10, 
                   coordinates=Coordinates(x=0.1, y=0.2)),
            Article(authors="Author 2", title="Title 2", journal="Journal 2", 
                   abstract="Abstract 2", year=2023, citations=20, 
                   coordinates=Coordinates(x=0.3, y=0.4))
        ]
        self.mock_repository.get_articles.return_value = articles
        
        result = self.service.get_articles_by_year(2024)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].year, 2024)

    def test_add_article(self):
        self.service.add_article(self.test_article)
    
        self.mock_repository.add_article.assert_called_once_with(self.test_article)
        self.assertEqual(len(self.test_article.embeddings), 3)
        self.assertIsInstance(self.test_article.coordinates, Coordinates)

    def test_delete_article(self):
        self.service.delete_article("test-id")
        
        self.mock_repository.delete_article.assert_called_once_with("test-id")

    def test_search_articles(self):
        articles = [
            Article(authors="Author 1", title="Test Title", journal="Journal 1", 
                   abstract="Abstract 1", year=2024, citations=10, 
                   coordinates=Coordinates(x=0.1, y=0.2)),
            Article(authors="Author 2", title="Title 2", journal="Journal 2", 
                   abstract="Abstract 2", year=2023, citations=20, 
                   coordinates=Coordinates(x=0.3, y=0.4))
        ]
        self.mock_repository.get_articles.return_value = articles
        
        result = self.service.search_articles("Test")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "Test Title")

if __name__ == '__main__':
    unittest.main()
