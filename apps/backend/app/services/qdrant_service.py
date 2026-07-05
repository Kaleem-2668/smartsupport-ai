import uuid

from app.core.config import get_settings

settings = get_settings()


class QdrantService:
    """Service for interacting with Qdrant vector database."""

    def __init__(self) -> None:
        self._client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Qdrant client."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams

            if settings.qdrant_api_key:
                self._client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
            else:
                self._client = QdrantClient(url=settings.qdrant_url)
        except Exception as exc:
            raise RuntimeError(f"Failed to initialize Qdrant client: {exc}") from exc

    def _get_collection_name(self, user_id: uuid.UUID, knowledge_base_id: uuid.UUID | None = None) -> str:
        """Get collection name for a specific user and knowledge base."""
        if knowledge_base_id:
            return f"kb_{knowledge_base_id}"
        return f"user_{user_id}"

    def _ensure_collection(self, user_id: uuid.UUID, knowledge_base_id: uuid.UUID | None = None) -> None:
        """Ensure collection exists for user/knowledge base."""
        from qdrant_client.models import Distance, VectorParams

        collection_name = self._get_collection_name(user_id, knowledge_base_id)
        
        try:
            collections = self._client.get_collections().collections
            collection_exists = any(c.name == collection_name for c in collections)
            
            if not collection_exists:
                self._client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=settings.ai_embedding_dimensions,
                        distance=Distance.COSINE
                    )
                )
        except Exception as exc:
            raise RuntimeError(f"Failed to ensure collection exists: {exc}") from exc

    def add_embeddings(
        self,
        user_id: uuid.UUID,
        document_id: uuid.UUID,
        chunks: list[dict],
        embeddings: list[list[float]],
        knowledge_base_id: uuid.UUID | None = None,
    ) -> None:
        """Add embeddings to Qdrant for a document."""
        from qdrant_client.models import PointStruct

        collection_name = self._get_collection_name(user_id, knowledge_base_id)
        self._ensure_collection(user_id, knowledge_base_id)

        points = [
            PointStruct(
                id=f"{document_id}_{chunk['index']}",
                vector=embedding,
                payload={
                    "document_id": str(document_id),
                    "chunk_index": chunk["index"],
                    "user_id": str(user_id),
                    "content": chunk["content"]
                }
            )
            for chunk, embedding in zip(chunks, embeddings, strict=False)
        ]

        try:
            self._client.upsert(collection_name=collection_name, points=points)
        except Exception as exc:
            raise RuntimeError(f"Failed to add embeddings: {exc}") from exc

    def delete_document_embeddings(self, user_id: uuid.UUID, document_id: uuid.UUID) -> None:
        """Delete all embeddings for a specific document."""
        collection_name = self._get_collection_name(user_id)
        
        try:
            self._client.delete(
                collection_name=collection_name,
                points_selector={
                    "filter": {
                        "must": [
                            {"key": "document_id", "match": {"value": str(document_id)}}
                        ]
                    }
                }
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to delete embeddings: {exc}") from exc

    def search_embeddings(
        self,
        user_id: uuid.UUID,
        query_embedding: list[float],
        n_results: int = 5,
        knowledge_base_id: uuid.UUID | None = None,
    ) -> dict:
        """Search for similar documents using query embedding."""
        collection_name = self._get_collection_name(user_id, knowledge_base_id)
        self._ensure_collection(user_id, knowledge_base_id)

        try:
            results = self._client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=n_results,
                with_payload=True
            )
            
            # Convert to format compatible with ChromaDB response
            documents = [[hit.payload.get("content", "") for hit in results]]
            metadatas = [[{
                "document_id": hit.payload.get("document_id"),
                "chunk_index": hit.payload.get("chunk_index"),
                "user_id": hit.payload.get("user_id")
            } for hit in results]]
            
            return {"documents": documents, "metadatas": metadatas}
        except Exception as exc:
            raise RuntimeError(f"Failed to search embeddings: {exc}") from exc

    def delete_user_collection(self, user_id: uuid.UUID) -> None:
        """Delete a user's entire collection."""
        collection_name = self._get_collection_name(user_id)
        try:
            self._client.delete_collection(collection_name=collection_name)
        except Exception as exc:
            raise RuntimeError(f"Failed to delete collection: {exc}") from exc
