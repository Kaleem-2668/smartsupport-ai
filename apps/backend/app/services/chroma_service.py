import uuid

from app.core.config import get_settings

settings = get_settings()


class ChromaService:
    """Service for interacting with ChromaDB vector database."""

    def __init__(self) -> None:
        self._client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize ChromaDB client.
        
        Supports two modes:
        - "http": Connects to an external ChromaDB server (default for production with separate service)
        - "embedded": Uses ChromaDB in-process with persistent storage (for Railway free tier)
        """
        try:
            import chromadb

            if settings.chroma_mode == "embedded":
                self._client = chromadb.PersistentClient(path=settings.chroma_data_path)
            else:
                self._client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
        except Exception as exc:
            raise RuntimeError(f"Failed to initialize ChromaDB client: {exc}") from exc

    def get_or_create_collection(self, user_id: uuid.UUID, knowledge_base_id: uuid.UUID | None = None) -> object:
        """Get or create a collection for a specific user and knowledge base.
        If knowledge_base_id is None, uses the default user collection for backward compatibility."""
        if knowledge_base_id:
            collection_name = f"kb_{knowledge_base_id}"
        else:
            collection_name = f"user_{user_id}"
        try:
            collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            return collection
        except Exception as exc:
            raise RuntimeError(f"Failed to get or create collection: {exc}") from exc

    def add_embeddings(
        self,
        user_id: uuid.UUID,
        document_id: uuid.UUID,
        chunks: list[dict],
        embeddings: list[list[float]],
        knowledge_base_id: uuid.UUID | None = None,
    ) -> None:
        """Add embeddings to ChromaDB for a document."""
        collection = self.get_or_create_collection(user_id, knowledge_base_id)

        ids = [f"{document_id}_{chunk['index']}" for chunk in chunks]
        documents = [chunk["content"] for chunk in chunks]
        metadatas = [
            {
                "document_id": str(document_id),
                "chunk_index": chunk["index"],
                "user_id": str(user_id),
            }
            for chunk in chunks
        ]

        try:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to add embeddings: {exc}") from exc

    def delete_document_embeddings(self, user_id: uuid.UUID, document_id: uuid.UUID) -> None:
        """Delete all embeddings for a specific document."""
        collection = self.get_or_create_collection(user_id)

        try:
            # Get all IDs for this document
            results = collection.get(where={"document_id": str(document_id)})
            if results and results["ids"]:
                collection.delete(ids=results["ids"])
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
        collection = self.get_or_create_collection(user_id, knowledge_base_id)

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
            )
            return results
        except Exception as exc:
            raise RuntimeError(f"Failed to search embeddings: {exc}") from exc

    def delete_user_collection(self, user_id: uuid.UUID) -> None:
        """Delete a user's entire collection."""
        collection_name = f"user_{user_id}"
        try:
            self._client.delete_collection(name=collection_name)
        except Exception as exc:
            raise RuntimeError(f"Failed to delete collection: {exc}") from exc
