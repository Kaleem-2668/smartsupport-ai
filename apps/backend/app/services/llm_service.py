from app.core.config import get_settings

settings = get_settings()


class LLMService:
    """Service for generating chat completions using LangChain, provider-agnostic."""

    def __init__(self) -> None:
        self._chat_model = None
        self._initialize_chat_model()

    def _initialize_chat_model(self) -> None:
        """Initialize the chat model based on provider."""
        if settings.ai_provider == "openai":
            self._initialize_openai()
        else:
            raise ValueError(f"Unsupported AI provider: {settings.ai_provider}")

    def _initialize_openai(self) -> None:
        """Initialize OpenAI chat model."""
        try:
            from langchain_openai import ChatOpenAI

            if not settings.ai_api_key:
                raise ValueError("AI_API_KEY is required for OpenAI chat completions")

            self._chat_model = ChatOpenAI(
                model=settings.ai_chat_model,
                openai_api_key=settings.ai_api_key,
                temperature=settings.ai_chat_temperature,
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to initialize OpenAI chat model: {exc}") from exc

    async def generate_answer(self, system_prompt: str, question: str) -> str:
        """Generate a chat completion given a system prompt (with context) and a question."""
        if not self._chat_model:
            raise RuntimeError("Chat model not initialized")

        try:
            from langchain_core.messages import HumanMessage, SystemMessage

            messages = [SystemMessage(content=system_prompt), HumanMessage(content=question)]
            response = await self._chat_model.ainvoke(messages)
            return response.content
        except Exception as exc:
            raise RuntimeError(f"Failed to generate chat completion: {exc}") from exc
