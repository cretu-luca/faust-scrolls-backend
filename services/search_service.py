from data.domain import Article
import numpy as np

class SearchService:
    EXACT_MATCH_SCORE = 0.9
    HIGH_SIMILARITY_SCORE = 0.8
    DEFAULT_THRESHOLD = 0.6

    def search_by_keyword(self, candidate_articles: list[Article], search_query: str) -> list[Article]: 
        if not search_query:
            return []
        
        search_query = search_query.lower()
        matches = []

        for candidate in candidate_articles:
            candidate_lower = candidate.lower()
            levenstein_score = self.levenstein_similarity(search_query, candidate_lower)

            if levenstein_score >= self.DEFAULT_THRESHOLD:
                matches.append((candidate, levenstein_score))

            if search_query in candidate_lower:
                matches.append((candidate, self.EXACT_MATCH_SCORE))
            
            if candidate_lower in search_query:
                matches.append((candidate, self.HIGH_SIMILARITY_SCORE))

            if " " in candidate:
                words = candidate_lower.split()

                for word in words: 
                    word_score = self.levenshtein_similarity(search_query, word)

                    if word_score >= self.DEFAULT_THRESHOLD: 
                        matches.append((candidate, word_score))
                        break

        result_dict = {}
        for article, score in matches:
            if article not in result_dict or score > result_dict[article]:
                result_dict[article] = score

        return [article for article, _ in sorted(result_dict.items(), 
                                                key=lambda x: x[1], 
                                                reverse=True)]

    @staticmethod
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