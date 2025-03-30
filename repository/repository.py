import json
from data.domain import Article

# repository will become datalink when database is integrated
# not data without embeddings gets in the database

class Repository:
    config: dict
    articles: list[Article]
    
    def __init__(self):
        self.config = self.load_config() 
        self.articles = self.parse_data()

    def load_config(self):
        try:
            config_file_path = "config/config.json"
            with open(config_file_path, "r") as f:
                config = json.load(f)

            return config
        
        except json.JSONDecodeError:
            return []
        except FileNotFoundError:
            return []

    def parse_data(self) -> list[Article]:
        try:
            file_path = self.config["file_path"]

            with open(file_path, "r") as file:
                data_list = json.load(file)

            if isinstance(data_list, list):
                articles = [self.parse_article(item) for item in data_list]
                for i, article in enumerate(articles):
                    if article.index is None:
                        article.index = i + 1
                return articles
            else: 
                return []
        
        except json.JSONDecodeError:
            return []
        except FileNotFoundError:
            return []

    def parse_article(self, data_dict: dict) -> Article: 
        if isinstance(data_dict.get("year"), str):
            data_dict['year'] = int(data_dict['year'])

        if isinstance(data_dict.get("citations"), str): 
            data_dict['citations'] = int(data_dict['citations'])
        
        if 'coordinates' in data_dict:
            if isinstance(data_dict['coordinates'].get('x'), str):
                data_dict['coordinates']['x'] = float(data_dict['coordinates']['x'])
                data_dict['coordinates']['y'] = float(data_dict['coordinates']['y'])

        return Article(**data_dict)
    
    def get_articles(self) -> list[Article]:
        return self.articles
    
    def add_article(self, article: Article) -> None:            
        self.articles.append(article)

    def update_article(self, article: Article) -> None:
        target_index = int(article.index) if article.index is not None else None
        
        target_index_str = str(target_index)
        
        found = False
        for index, existing_article in enumerate(self.articles):
            existing_index_str = str(existing_article.index)
        
            if existing_index_str == target_index_str:
                found = True
                self.articles[index] = article
                return
            elif int(existing_article.index) == target_index:
                found = True
                self.articles[index] = article
                return
                
        if not found:
            raise ValueError(f"Article with index {target_index} not found")
    
    def delete_article(self, article_id: str) -> None:
        self.articles = [article for article in self.articles if article.id != article_id]
        
    def delete_article_by_index(self, index: int) -> None:
        self.articles = [article for article in self.articles if article.index != index]
        