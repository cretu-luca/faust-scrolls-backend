from data.domain import Article
import numpy as np

class SearchService:
    EXACT_MATCH_SCORE = 0.9
    HIGH_SIMILARITY_SCORE = 0.8
    DEFAULT_THRESHOLD = 0.6

    def search_by_keyword(articles: list[Article], search_query: str) -> list[Article]: 
        pass

    def levenshtein_similarity(source: str, target: str) -> float:
        n = len(source)
        m = len(target)
        distance = np.zeros(n + 1, m + 1)

        for i in range(n + 1):
            distance[i][0] = i

        for j in range(m + 1):
            distance[0][j] = j

        for i in range(1, n + 1):
            for j in range(m + 1):
                cost = 0 if source[i - 1] == target[j - 1] else 1
            
                distance[i, j] = min(
                    distance[i - 1, j] + 1,
                    distance[i, j - 1] + 1,
                    distance[i - 1, j - 1] + cost
                )
                
        max_length = max(n, m)

        return 1.0 if max_length == 0 else 1.0 - (distance[n][m] / max_length)