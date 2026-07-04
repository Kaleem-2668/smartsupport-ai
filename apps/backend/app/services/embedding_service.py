from app.core.config import get_settings

settings = get_settings()


class EmbeddingService:
    """Service for generating text embeddings using LangChain."""

    def __init__(self) -> None:
        self._embedding_function = None
        self._initialize_embedding_function()

    def _initialize_embedding_function(self) -> None:
        """Initialize the embedding function based on provider."""
        if settings.ai_provider == "openai":
            self._initialize_openai()
        else:
            raise ValueError(f"Unsupported AI provider: {settings.ai_provider}")

    def _initialize_openai(self) -> None:
        """Initialize OpenAI embedding function."""
        try:
            from langchain_openai import OpenAIEmbeddings

            if not settings.ai_api_key:
                raise ValueError("AI_API_KEY is required for OpenAI embeddings")

            self._embedding_function = OpenAIEmbeddings(
                model=settings.ai_model,
                openai_api_key=settings.ai_api_key,
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to initialize OpenAI embeddings: {exc}") from exc

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        if not self._embedding_function:
            raise RuntimeError("Embedding function not initialized")

        try:
            embeddings = self._embedding_function.embed_documents(texts)
            return embeddings
        except Exception as exc:
            raise RuntimeError(f"Failed to generate embeddings: {exc}") from exc

    async def generate_query_embedding(self, query: str) -> list[float]:
        """Generate embedding for a single query."""
        if not self._embedding_function:
            raise RuntimeError("Embedding function not initialized")

        try:
            embedding = self._embedding_function.embed_query(query)
            return embedding
        except Exception as exc:
            raise RuntimeError(f"Failed to generate query embedding: {exc}") from exc
