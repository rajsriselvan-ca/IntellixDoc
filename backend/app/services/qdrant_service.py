from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict, Optional
from app.config import settings
import uuid

COLLECTION_NAME = "document_chunks"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2 produces 384-dimensional vectors

__all__ = ['QdrantService', 'qdrant_service', 'COLLECTION_NAME']


class QdrantService:
    def __init__(self):
        self.client = QdrantClient(url=settings.qdrant_url)
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if COLLECTION_NAME not in collection_names:
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=VECTOR_SIZE,
                        distance=Distance.COSINE
                    )
                )
        except Exception as e:
            print(f"Error ensuring collection: {e}")
    
    def add_vectors(
        self,
        vectors: List[List[float]],
        payloads: List[Dict],
        ids: Optional[List[str]] = None
    ):
        """Add vectors to Qdrant."""
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in vectors]
        
        points = [
            PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )
            for point_id, vector, payload in zip(ids, vectors, payloads)
        ]
        
        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        
        return ids
    
    def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.5
    ) -> List[Dict]:
        """Search for similar vectors."""
        results = self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold
        )
        
        return [
            {
                "id": result.id,
                "score": result.score,
                "payload": result.payload
            }
            for result in results
        ]
    
    def delete_vectors(self, ids: List[str]):
        """Delete vectors by IDs."""
        self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=ids
        )
    
    def delete_document_vectors(self, document_id: int):
        """Delete all vectors for a specific document."""
        self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )


qdrant_service = QdrantService()

