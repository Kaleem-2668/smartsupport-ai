from pathlib import Path

from app.domain.exceptions import InvalidFileError


class TextExtractionService:
    """Service for extracting text from various document formats."""

    async def extract_text(self, file_path: str, mime_type: str) -> str:
        """Extract text from a file based on its MIME type."""
        path = Path(file_path)

        if not path.exists():
            raise InvalidFileError(f"File not found: {file_path}")

        if mime_type == "text/plain":
            return await self._extract_from_text(path)
        elif mime_type == "text/markdown":
            return await self._extract_from_text(path)
        elif mime_type == "application/pdf":
            return await self._extract_from_pdf(path)
        elif mime_type == "application/msword":
            return await self._extract_from_doc(path)
        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return await self._extract_from_docx(path)
        else:
            raise InvalidFileError(f"Unsupported MIME type: {mime_type}")

    async def _extract_from_text(self, path: Path) -> str:
        """Extract text from plain text files (TXT, MD)."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(path, "r", encoding="latin-1") as f:
                return f.read()

    async def _extract_from_pdf(self, path: Path) -> str:
        """Extract text from PDF files."""
        try:
            from pypdf import PdfReader

            reader = PdfReader(path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as exc:
            raise InvalidFileError(f"Failed to extract text from PDF: {exc}") from exc

    async def _extract_from_doc(self, path: Path) -> str:
        """Extract text from legacy DOC files."""
        try:
            # Note: python-docx doesn't support legacy .doc files
            # For now, we'll raise an error. In production, you might use
            # antiword or another library for .doc support
            raise InvalidFileError(
                "Legacy .doc files are not currently supported. Please convert to .docx or PDF."
            )
        except Exception as exc:
            raise InvalidFileError(f"Failed to extract text from DOC: {exc}") from exc

    async def _extract_from_docx(self, path: Path) -> str:
        """Extract text from DOCX files."""
        try:
            from docx import Document

            doc = Document(path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as exc:
            raise InvalidFileError(f"Failed to extract text from DOCX: {exc}") from exc
