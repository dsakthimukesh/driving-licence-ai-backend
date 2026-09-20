from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingProvider(ABC):
    """
    Abstract Base Class for text embedding providers.
    """

    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generates dense vector embeddings for a list of input texts.
        Returns a list of float vectors, each matching configured dimensions.
        """
        pass
