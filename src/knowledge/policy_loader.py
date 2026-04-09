"""Load company policy documents from the knowledge_base directory."""

from pathlib import Path
from src.config import KNOWLEDGE_BASE_DIR

# Supported file extensions
TEXT_EXTENSIONS = {".md", ".txt", ".rst"}
PDF_EXTENSIONS = {".pdf"}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | PDF_EXTENSIONS


def load_file(path: Path) -> str:
    """Read a single policy file and return its contents."""
    try:
        if path.suffix.lower() in PDF_EXTENSIONS:
            return _load_pdf(path)
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _load_pdf(path: Path) -> str:
    """Extract text from a PDF file."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)
    except ImportError:
        return f"[PDF file: {path.name} - install pypdf to read]"
    except Exception:
        return ""


def load_all_policies() -> str:
    """Load all policy documents and concatenate them.

    Scans the knowledge_base/ directory for .md and .txt files,
    reads each one, and returns them joined with section headers.
    """
    if not KNOWLEDGE_BASE_DIR.exists():
        return ""

    sections: list[str] = []
    for path in sorted(KNOWLEDGE_BASE_DIR.iterdir()):
        if path.suffix.lower() in SUPPORTED_EXTENSIONS and path.is_file():
            content = load_file(path)
            if content.strip():
                sections.append(f"### {path.stem.replace('_', ' ').title()}\n\n{content}")

    return "\n\n---\n\n".join(sections)


def load_policy_by_name(name: str) -> str | None:
    """Load a specific policy file by name (without extension)."""
    for ext in SUPPORTED_EXTENSIONS:
        path = KNOWLEDGE_BASE_DIR / f"{name}{ext}"
        if path.exists():
            return load_file(path)
    return None


def list_policies() -> list[str]:
    """List all available policy document names."""
    if not KNOWLEDGE_BASE_DIR.exists():
        return []
    return [
        p.stem
        for p in sorted(KNOWLEDGE_BASE_DIR.iterdir())
        if p.suffix.lower() in SUPPORTED_EXTENSIONS and p.is_file()
    ]
