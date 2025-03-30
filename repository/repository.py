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
            print ("error: reading/decoding {config_file_path} config file")
            return []
        except FileNotFoundError: 
            print ("error: cannot find file {config_file_path}")
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
                print(f"error: unexpected data format in {file_path}")
                return []
        
        except json.JSONDecodeError:
            print ("error: reading {file_path} data path")
            return []
        except FileNotFoundError:
            print ("error: cannot find file {file_path}")
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
        # Only set index if it's not already set
        if article.index is None:
            article.index = len(self.articles) + 1
            
        print(f"Repository: Adding article with index: {article.index}")
        self.articles.append(article)
        print(f"Repository: Article added successfully, total articles: {len(self.articles)}")

    def update_article(self, article: Article) -> None:
        target_index = int(article.index) if article.index is not None else None
        print(f"Repository: Updating article with index: {target_index} (type: {type(target_index)})")
        
        # Use string comparison for consistency
        target_index_str = str(target_index)
        
        print("Repository: Current articles:")
        for i, art in enumerate(self.articles):
            art_index = int(art.index) if art.index is not None else None
            art_index_str = str(art_index)
            print(f"  [{i}] Index: {art_index} (type: {type(art_index)}), str: '{art_index_str}'")
        
        found = False
        for index, existing_article in enumerate(self.articles):
            # Convert both to strings for comparison
            existing_index_str = str(existing_article.index)
            
            print(f"Repository: Comparing '{existing_index_str}' with target '{target_index_str}'")
            
            # First try exact string match, then try integer match
            if existing_index_str == target_index_str:
                found = True
                print(f"Repository: Found article at position {index} by string comparison")
                self.articles[index] = article
                print("Repository: Article updated successfully")
                return
            # Also try integer comparison as backup
            elif int(existing_article.index) == target_index:
                found = True
                print(f"Repository: Found article at position {index} by integer comparison")
                self.articles[index] = article
                print("Repository: Article updated successfully")
                return
                
        if not found:
            all_indices = [str(a.index) for a in self.articles]
            print(f"Repository: Article with index {target_index_str} not found")
            print(f"Repository: Available indices: {all_indices}")
            raise ValueError(f"Article with index {target_index} not found")
    
    def delete_article(self, article_id: str) -> None:
        self.articles = [article for article in self.articles if article.id != article_id]
        
    def delete_article_by_index(self, index: int) -> None:
        self.articles = [article for article in self.articles if article.index != index]
        