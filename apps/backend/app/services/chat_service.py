import uuid

from app.core.config import get_settings
from app.domain.exceptions import ConversationNotFoundError, LLMError
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.services.chroma_service import ChromaService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService

settings = get_settings()

SYSTEM_PROMPT_TEMPLATE = """You are a customer support assistant for this business. Answer the \
user's question using ONLY the context below, which was retrieved from the business's own \
knowledge base. If the context does not contain enough information to answer confidently, say \
that you don't have enough information rather than guessing.

Context:
{context}
"""

NO_CONTEXT_PLACEHOLDER = "(No relevant documents were found in the knowledge base.)"


class ChatService:
    """Orchestrates the RAG chat pipeline: retrieve context -> call LLM -> persist turn."""

    def __init__(
        self,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
    ) -> None:
        self._conversations = conversation_repository
        self._messages = message_repository
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
        self, user_id: uuid.UUID, conversation_id: uuid.UUID | None, question: str
    ) -> Conversation:
        if conversation_id is None:
            title = question[:80]
            return await self._conversations.create(user_id=user_id, title=title)

        conversation = await self._conversations.get_by_id(conversation_id)
        if conversation is None or conversation.user_id != user_id:
            raise ConversationNotFoundError(f"Conversation with ID {conversation_id} not found")
        return conversation

    async def _retrieve_context(self, user_id: uuid.UUID, question: str) -> tuple[str, list[dict]]:
        """Return (formatted context string, source metadata list) for the given question."""
        query_embedding = await self._embedder.generate_query_embedding(question)
        results = self._chroma.search_embeddings(
            user_id=user_id,
            query_embedding=query_embedding,
            n_results=settings.chat_retrieval_top_k,
        )

        documents = results.get("documents") or [[]]
        metadatas = results.get("metadatas") or [[]]
        chunk_texts = documents[0] if documents else []
        chunk_metadatas = metadatas[0] if metadatas else []

        if not chunk_texts:
            return NO_CONTEXT_PLACEHOLDER, []

        context_parts = []
        sources = []
        for text, metadata in zip(chunk_texts, chunk_metadatas, strict=False):
            context_parts.append(text)
            sources.append(
                {
                    "document_id": metadata.get("document_id"),
                    "chunk_index": metadata.get("chunk_index"),
                    "snippet": text[:200],
                }
            )

        return "\n\n---\n\n".join(context_parts), sources

    async def ask(
        self, user_id: uuid.UUID, question: str, conversation_id: uuid.UUID | None
    ) -> tuple[uuid.UUID, Message]:
        """Answer a question, persisting both the user's message and the assistant's reply."""
        self._ensure_ai_services()
        conversation = await self._get_or_create_conversation(user_id, conversation_id, question)

        await self._messages.create(
            conversation_id=conversation.id, role=MessageRole.USER.value, content=question
        )

        context, sources = await self._retrieve_context(user_id, question)
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)

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
