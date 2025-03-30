from sentence_transformers import SentenceTransformer
from sklearn.manifold import TSNE

class AbstractsEncoder:
    def __init__(self):
        self._model = None
        self._tsne = None
        
    @property
    def model(self):
        if self._model is None:
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
        return self._model
    
    @property
    def tsne(self):
        if self._tsne is None:
            self._tsne = TSNE(n_components=2, random_state=42, perplexity=30)
        return self._tsne

    def encode(self, abstract: str) -> list[float]:
        return self.model.encode(abstract).tolist()

    def get_coordinates(self, embedding: list[float]) -> list[float]:
        return self.tsne.fit_transform([embedding]).tolist()[0]
