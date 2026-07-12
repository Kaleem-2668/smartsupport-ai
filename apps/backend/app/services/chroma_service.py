import uuid

from app.core.config import get_settings

settings = get_settings()


class ChromaService:
    """Service for interacting with ChromaDB vector database."""

    def __init__(self) -> None:
        self._client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize ChromaDB client."""
        try:
            import chromadb

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
        metadatas = []
        for chunk in chunks:
            metadata = {
                "document_id": str(document_id),
                "chunk_index": chunk["index"],
                "user_id": str(user_id),
            }
            if chunk.get("page_number") is not None:
                metadata["page_number"] = chunk["page_number"]
            metadatas.append(metadata)

        try:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to add embeddings: {exc}") from exc

    def delete_document_embeddings(
        self, user_id: uuid.UUID, document_id: uuid.UUID, knowledge_base_id: uuid.UUID | None = None
    ) -> None:
        """Delete all embeddings for a specific document. Must target the same collection
        the embeddings were originally written to (per-user by default, or per-knowledge-base
        if the document belongs to one) — otherwise the embeddings are silently orphaned."""
        collection = self.get_or_create_collection(user_id, knowledge_base_id)

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

    def find_related_documents(
        self,
        user_id: uuid.UUID,
        document_id: uuid.UUID,
        knowledge_base_id: uuid.UUID | None = None,
        n_results: int = 5,
    ) -> list[dict]:
        """Find documents related to the given one, using one of its own chunk embeddings
        (already computed at processing time) as the similarity query — no new embedding
        call needed. Searches the same collection the document's embeddings live in, so
        results stay scoped the same way chat retrieval is (per-knowledge-base, or the
        user's default collection)."""
        collection = self.get_or_create_collection(user_id, knowledge_base_id)

        try:
            own_chunks = collection.get(
                where={"document_id": str(document_id)}, limit=1, include=["embeddings"]
            )
            if own_chunks is None or len(own_chunks.get("ids") or []) == 0:
                return []
            query_embedding = own_chunks["embeddings"][0]

            # Over-fetch since many of the nearest chunks will belong to this same document.
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results * 5 + 5,
                include=["metadatas", "distances"],
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to find related documents: {exc}") from exc

        metadatas = results.get("metadatas") or [[]]
        distances = results.get("distances") or [[]]

        best_distance_by_document: dict[str, float] = {}
        for metadata, distance in zip(metadatas[0], distances[0], strict=False):
            other_id = metadata.get("document_id")
            if not other_id or other_id == str(document_id):
                continue
            if other_id not in best_distance_by_document or distance < best_distance_by_document[other_id]:
                best_distance_by_document[other_id] = distance

        ranked = sorted(best_distance_by_document.items(), key=lambda item: item[1])[:n_results]
        return [
            {"document_id": doc_id, "similarity": round(max(0.0, min(1.0, 1 - distance)), 3)}
            for doc_id, distance in ranked
        ]

    def delete_user_collection(self, user_id: uuid.UUID) -> None:
        """Delete a user's entire collection."""
        collection_name = f"user_{user_id}"
        try:
            self._client.delete_collection(name=collection_name)
        except Exception as exc:
            raise RuntimeError(f"Failed to delete collection: {exc}") from exc
