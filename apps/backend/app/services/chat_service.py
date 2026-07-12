import uuid

from app.core.config import get_settings
from app.domain.exceptions import ConversationNotFoundError, LLMError
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.message_repository import MessageRepository
from app.services.chroma_service import ChromaService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService

settings = get_settings()

_CONTEXT_INSTRUCTIONS = """Answer the user's question using ONLY the context below, which was \
retrieved from their own uploaded documents. Each excerpt is labeled with the document (and \
page, where available) it came from. If the context does not contain enough information to \
answer confidently, say so plainly rather than guessing.

When the context includes excerpts from more than one document, synthesize across them rather \
than treating each in isolation: connect related points, and explicitly note it if two sources \
agree, disagree, or add complementary detail. When you state something specific, mention which \
document it came from.

Context:
{context}
"""

PERSONALITY_PROMPTS: dict[str, str] = {
    "professional": (
        "You are Orin, a precise and professional knowledge assistant. Answer clearly, "
        "concisely, and factually, in the tone of a knowledgeable colleague. Avoid filler "
        "and unnecessary hedging.\n\n" + _CONTEXT_INSTRUCTIONS
    ),
    "tutor": (
        "You are Orin, acting as a patient tutor. Explain concepts step by step, define "
        "any terms that might be unfamiliar, and where useful check the user's "
        "understanding or suggest what to explore next. Prioritize clarity over brevity, "
        "but stay on topic.\n\n" + _CONTEXT_INSTRUCTIONS
    ),
    "friendly": (
        "You are Orin, a warm and approachable assistant. Answer in a conversational, "
        "down-to-earth tone, like a helpful friend who happens to know the material well. "
        "Stay accurate and avoid sounding stiff or overly formal.\n\n" + _CONTEXT_INSTRUCTIONS
    ),
    "playful": (
        "You are Orin, an upbeat and playful assistant. Answer accurately, but with "
        "energy, light humor, and the occasional emoji where it fits naturally. Keep it "
        "fun without burying the actual answer.\n\n" + _CONTEXT_INSTRUCTIONS
    ),
    "roast": (
        "You are Orin in Roast Mode: witty, sarcastic, and irreverent, like a friend who "
        "teases you while still having your back. Feel free to gently roast the user's "
        "question, the document's writing quality, or the situation in general — but keep "
        "it good-natured, never mean-spirited, and never targeting personal "
        "characteristics like appearance, identity, or ability. However you deliver it, "
        "you must still answer the actual question correctly and completely — the roast is "
        "garnish, not a substitute for the real answer.\n\n" + _CONTEXT_INSTRUCTIONS
    ),
}

DEFAULT_PERSONALITY = "professional"

NO_CONTEXT_PLACEHOLDER = "(No relevant documents were found in the knowledge base.)"


class ChatService:
    """Orchestrates the RAG chat pipeline: retrieve context -> call LLM -> persist turn."""

    def __init__(
        self,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
        document_repository: DocumentRepository,
    ) -> None:
        self._conversations = conversation_repository
        self._messages = message_repository
        self._documents = document_repository
        # Constructed lazily (only when a question is actually asked) so that read-only
        # endpoints — listing conversations/messages — don't require AI_API_KEY or a live
        # ChromaDB connection.
        self._embedder: EmbeddingService | None = None
        self._chroma: ChromaService | None = None
        self._llm: LLMService | None = None

    def _ensure_ai_services(self) -> None:
        if self._embedder is None:
            self._embedder = EmbeddingService()
        if self._chroma is None:
            self._chroma = ChromaService()
        if self._llm is None:
            self._llm = LLMService()

    async def _get_or_create_conversation(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID | None,
        question: str,
        personality: str | None,
    ) -> Conversation:
        if conversation_id is None:
            title = question[:80]
            return await self._conversations.create(
                user_id=user_id, title=title, personality=personality or DEFAULT_PERSONALITY
            )

        conversation = await self._conversations.get_by_id(conversation_id)
        if conversation is None or conversation.user_id != user_id:
            raise ConversationNotFoundError(f"Conversation with ID {conversation_id} not found")
        return conversation

    async def _retrieve_context(
        self, user_id: uuid.UUID, question: str, knowledge_base_id: uuid.UUID | None = None
    ) -> tuple[str, list[dict]]:
        """Return (formatted context string, source metadata list) for the given question."""
        query_embedding = await self._embedder.generate_query_embedding(question)
        results = self._chroma.search_embeddings(
            user_id=user_id,
            query_embedding=query_embedding,
            n_results=settings.chat_retrieval_top_k,
            knowledge_base_id=knowledge_base_id,
        )

        documents = results.get("documents") or [[]]
        metadatas = results.get("metadatas") or [[]]
        distances = results.get("distances") or [[]]
        chunk_texts = documents[0] if documents else []
        chunk_metadatas = metadatas[0] if metadatas else []
        chunk_distances = distances[0] if distances else []

        if not chunk_texts:
            return NO_CONTEXT_PLACEHOLDER, []

        # Resolve document_id -> filename in a single batch query rather than one per source.
        document_ids = {
            metadata.get("document_id")
            for metadata in chunk_metadatas
            if metadata.get("document_id")
        }
        matched_documents = await self._documents.get_by_ids(
            [uuid.UUID(doc_id) for doc_id in document_ids]
        )
        names_by_id = {str(doc.id): doc.original_filename for doc in matched_documents}

        context_parts = []
        sources = []
        for i, (text, metadata) in enumerate(zip(chunk_texts, chunk_metadatas, strict=False)):
            document_id = metadata.get("document_id")
            document_name = names_by_id.get(document_id, "Unknown document")
            page_number = metadata.get("page_number")
            # Label each chunk with its source so the model can attribute claims to a
            # specific document and reason across documents rather than treating the
            # context as one undifferentiated blob.
            label = f"[Source: {document_name}" + (f", page {page_number}]" if page_number else "]")
            context_parts.append(f"{label}\n{text}")

            # Cosine distance -> similarity confidence in [0, 1]; Chroma's cosine space
            # returns distance = 1 - cosine_similarity, so similarity = 1 - distance.
            confidence = None
            if i < len(chunk_distances):
                confidence = round(max(0.0, min(1.0, 1 - chunk_distances[i])), 3)
            sources.append(
                {
                    "document_id": document_id,
                    "document_name": document_name,
                    "chunk_index": metadata.get("chunk_index"),
                    "page_number": page_number,
                    "confidence": confidence,
                    "snippet": text[:200],
                }
            )

        return "\n\n---\n\n".join(context_parts), sources

    async def ask(
        self,
        user_id: uuid.UUID,
        question: str,
        conversation_id: uuid.UUID | None,
        knowledge_base_id: uuid.UUID | None = None,
        personality: str | None = None,
    ) -> tuple[uuid.UUID, Message]:
        """Answer a question, persisting both the user's message and the assistant's reply."""
        self._ensure_ai_services()
        conversation = await self._get_or_create_conversation(
            user_id, conversation_id, question, personality
        )

        await self._messages.create(
            conversation_id=conversation.id, role=MessageRole.USER.value, content=question
        )

        context, sources = await self._retrieve_context(user_id, question, knowledge_base_id)
        prompt_template = PERSONALITY_PROMPTS.get(
            conversation.personality, PERSONALITY_PROMPTS[DEFAULT_PERSONALITY]
        )
        system_prompt = prompt_template.format(context=context)

        try:
            answer = await self._llm.generate_answer(system_prompt, question)
        except RuntimeError as exc:
            raise LLMError(str(exc)) from exc

        assistant_message = await self._messages.create(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT.value,
            content=answer,
            sources=sources,
        )

        await self._conversations.touch(conversation.id)

        return conversation.id, assistant_message

    async def get_user_conversations(self, user_id: uuid.UUID) -> list[Conversation]:
        return await self._conversations.get_by_user(user_id)

    async def get_conversation_messages(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> list[Message]:
        conversation = await self._conversations.get_by_id(conversation_id)
        if conversation is None or conversation.user_id != user_id:
            raise ConversationNotFoundError(f"Conversation with ID {conversation_id} not found")
        return await self._messages.get_by_conversation(conversation_id)

    async def delete_conversation(self, user_id: uuid.UUID, conversation_id: uuid.UUID) -> None:
        conversation = await self._conversations.get_by_id(conversation_id)
        if conversation is None or conversation.user_id != user_id:
            raise ConversationNotFoundError(f"Conversation with ID {conversation_id} not found")
        await self._conversations.delete(conversation_id)

    async def update_conversation(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        title: str | None = None,
        personality: str | None = None,
    ) -> Conversation:
        conversation = await self._conversations.get_by_id(conversation_id)
        if conversation is None or conversation.user_id != user_id:
            raise ConversationNotFoundError(f"Conversation with ID {conversation_id} not found")

        if title is not None:
            conversation = await self._conversations.set_title(conversation_id, title)
        if personality is not None:
            conversation = await self._conversations.set_personality(conversation_id, personality)

        assert conversation is not None  # existence already confirmed above
        return conversation
