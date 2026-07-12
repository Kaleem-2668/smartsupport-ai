from app.core.config import get_settings

settings = get_settings()


class ChunkingService:
    """Service for chunking documents into smaller pieces for embedding."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> list[str]:
        """Chunk text into smaller pieces using recursive character splitting."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        chunks = text_splitter.split_text(text)
        return chunks

    def chunk_document(self, text: str) -> list[dict]:
        """Chunk text and return chunks with metadata."""
        chunks = self.chunk_text(text)
        chunk_data = []
        for i, chunk in enumerate(chunks):
            chunk_data.append({"index": i, "content": chunk})
        return chunk_data

    def chunk_pages(self, pages: list[dict]) -> list[dict]:
        """Chunk a list of {"page_number", "text"} entries, keeping each chunk within a
        single page so citations can report an accurate page number. Returns chunks with
        a global sequential index plus the originating page_number."""
        chunk_data = []
        index = 0
        for page in pages:
            for piece in self.chunk_text(page["text"]):
                chunk_data.append(
                    {"index": index, "content": piece, "page_number": page["page_number"]}
                )
                index += 1
        return chunk_data
