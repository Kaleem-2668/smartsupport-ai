import json
import logging
import uuid

from app.core.config import get_settings
from app.domain.exceptions import InvalidFileError, StorageError
from app.models.document import Document, DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.services.chroma_service import ChromaService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.text_extraction_service import TextExtractionService

settings = get_settings()
logger = logging.getLogger(__name__)

# How much of a document's extracted text to feed the LLM when generating a summary and
# suggested questions. This is a enrichment step, not the retrieval path, so a generous
# but bounded prefix keeps cost/latency predictable without needing the whole document.
MAX_INTELLIGENCE_INPUT_CHARS = 12000

INTELLIGENCE_PROMPT = """You are analyzing a document to help a user quickly understand what \
it contains. Based on the document text below, respond with ONLY a JSON object (no markdown \
fences, no commentary) in exactly this shape:

{{"summary": "a concise 2-4 sentence summary of the document", \
"suggested_questions": ["question 1", "question 2", "question 3", "question 4"]}}

The suggested_questions should be genuinely answerable from this document's content, and \
varied in what they ask about.

Document text:
{text}
"""


class DocumentProcessingService:
    """Service for orchestrating document processing pipeline: extraction → chunking → embedding → storage."""

    def __init__(
        self,
        document_repository: DocumentRepository,
    ) -> None:
        self._documents = document_repository
        self._text_extractor = TextExtractionService()
        self._chunker = ChunkingService(
            chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
        )
        self._embedder = EmbeddingService()
        self._chroma = ChromaService()
        self._llm: LLMService | None = None
        # Constructed lazily since it's only needed for the optional summary/questions
        # enrichment step, not the core embedding pipeline.

    async def process_document(self, document_id: uuid.UUID, user_id: uuid.UUID) -> Document:
        """Process a document through the full pipeline."""
        # Get document
        document = await self._documents.get_by_id(document_id)
        if document is None:
            raise InvalidFileError(f"Document with ID {document_id} not found")

        if document.user_id != user_id:
            raise InvalidFileError("Document does not belong to user")

        # Update status to processing
        await self._documents.update_status(document_id, DocumentStatus.PROCESSING)

        try:
            # Step 1: Extract text (page-aware, so citations can report a page number)
            pages = await self._text_extractor.extract_pages(document.file_path, document.mime_type)

            if not pages or not any(page["text"].strip() for page in pages):
                raise InvalidFileError("No text could be extracted from document")

            # Step 2: Chunk text, keeping each chunk within a single page
            chunks = self._chunker.chunk_pages(pages)

            if not chunks:
                raise InvalidFileError("Document could not be chunked")

            # Step 3: Generate embeddings
            chunk_texts = [chunk["content"] for chunk in chunks]
            embeddings = await self._embedder.generate_embeddings(chunk_texts)

            # Step 4: Store in ChromaDB (using knowledge base collection if available)
            # ChromaService methods are synchronous (the chromadb client is sync),
            # so this is a plain call, not awaited.
            self._chroma.add_embeddings(
                user_id=user_id,
                document_id=document_id,
                chunks=chunks,
                embeddings=embeddings,
                knowledge_base_id=document.knowledge_base_id,
            )

            # Step 5: Mark as processed
            processed_document = await self._documents.mark_processed(document_id, len(chunks))

            # Step 6: Generate a summary and suggested questions. This is an enrichment,
            # not part of the core RAG pipeline, so a failure here must not undo the
            # successful processing above — it just leaves summary/suggested_questions null.
            try:
                await self._generate_intelligence(document_id, pages)
            except Exception:
                logger.warning(
                    "Failed to generate summary/suggested questions for document %s",
                    document_id,
                    exc_info=True,
                )

            return processed_document

        except Exception as exc:
            # Mark as error
            await self._documents.update_status(
                document_id, DocumentStatus.ERROR, error_message=str(exc)
            )
            raise StorageError(f"Document processing failed: {exc}") from exc

    async def _generate_intelligence(self, document_id: uuid.UUID, pages: list[dict]) -> None:
        """Generate and store a summary and suggested questions for a processed document."""
        full_text = "\n\n".join(page["text"] for page in pages if page["text"].strip())
        if not full_text.strip():
            return

        if self._llm is None:
            self._llm = LLMService()

        prompt = INTELLIGENCE_PROMPT.format(text=full_text[:MAX_INTELLIGENCE_INPUT_CHARS])
        response = await self._llm.generate_answer(prompt, "Generate the JSON now.")

        parsed = _parse_intelligence_response(response)
        if parsed is None:
            logger.warning("Could not parse intelligence response for document %s", document_id)
            return

        summary, suggested_questions = parsed
        await self._documents.set_intelligence(document_id, summary, suggested_questions)

    async def delete_document_embeddings(self, document_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete embeddings for a document from ChromaDB."""
        try:
            self._chroma.delete_document_embeddings(user_id, document_id)
        except Exception as exc:
            raise StorageError(f"Failed to delete embeddings: {exc}") from exc


def _parse_intelligence_response(response: str) -> tuple[str, list[str]] | None:
    """Parse the LLM's JSON response, tolerating markdown code fences some models add
    despite being told not to. Returns None if the response isn't usable."""
    text = response.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(data, dict):
        return None

    summary = data.get("summary")
    questions = data.get("suggested_questions")

    if not isinstance(summary, str) or not summary.strip():
        return None
    if not isinstance(questions, list):
        questions = []

    clean_questions = [q.strip() for q in questions if isinstance(q, str) and q.strip()][:6]
    return summary.strip(), clean_questions
