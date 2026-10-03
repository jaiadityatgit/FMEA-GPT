"""Document loading and page-level extraction for FMEA-GPT RAG pipeline."""
import json
import os
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


@dataclass
class PageContent:
    """Represents the raw text and rich metadata of a single extracted page."""
    doc_id: str
    source_file: str
    doc_title: str
    publisher: str
    document_type: str
    page_number: int
    total_pages: int
    text: str
    relevance_category: str = "aerospace_guidance"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "source_file": self.source_file,
            "doc_title": self.doc_title,
            "publisher": self.publisher,
            "document_type": self.document_type,
            "page_number": self.page_number,
            "total_pages": self.total_pages,
            "text": self.text,
            "relevance_category": self.relevance_category,
            "metadata": self.metadata
        }


class DocumentLoader:
    """Loads PDF documents from disk and extracts page-by-page text with metadata."""

    def __init__(self, raw_dir: Path, metadata_file: Path):
        self.raw_dir = Path(raw_dir)
        self.metadata_file = Path(metadata_file)
        self.sources_metadata = self._load_sources_metadata()

    def _load_sources_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Load sources.json and map by local filename or doc_id."""
        mapping = {}
        if not self.metadata_file.exists():
            return mapping

        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    # Map by filename basename
                    local_filename = item.get("local_filename", "")
                    if local_filename and local_filename != "N/A":
                        basename = Path(local_filename).name
                        mapping[basename] = item
                    # Also map by ID
                    if item.get("id"):
                        mapping[item["id"]] = item
        except Exception as e:
            print(f"Warning: Failed to load sources metadata from {self.metadata_file}: {e}")
        return mapping

    def clean_page_text(self, text: str) -> str:
        """Clean extracted page text, fix hyphens, and normalize whitespace."""
        if not text:
            return ""

        # Remove null characters and non-printable control chars except tabs/newlines
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

        # Fix hyphenated line breaks (e.g. "compo-\nnent" -> "component")
        text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)

        # Normalize multiple spaces and tabs within a line
        text = re.sub(r'[ \t]+', ' ', text)

        # Collapse more than two consecutive newlines to two
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def load_pdf(self, pdf_path: Path, doc_info: Optional[Dict[str, Any]] = None) -> List[PageContent]:
        """Extract pages from a single PDF file with full metadata."""
        if not PYPDF_AVAILABLE:
            raise ImportError("pypdf is required to extract PDF text. Install it with `pip install pypdf`.")

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        basename = pdf_path.name
        if not doc_info:
            doc_info = self.sources_metadata.get(basename, {})

        doc_id = doc_info.get("id", pdf_path.stem)
        doc_title = doc_info.get("title", pdf_path.stem.replace("_", " "))
        publisher = doc_info.get("publisher", "Unknown Publisher")
        document_type = doc_info.get("document_type", "Aerospace Document")
        relevance = doc_info.get("relevance_to_fmea_gpt", "General guidance")

        pages: List[PageContent] = []
        try:
            reader = PdfReader(str(pdf_path))
            total_pages = len(reader.pages)

            for page_idx, page in enumerate(reader.pages):
                page_num = page_idx + 1
                try:
                    raw_text = page.extract_text() or ""
                except Exception as e:
                    print(f"Warning: Failed to extract page {page_num} of {basename}: {e}")
                    raw_text = ""

                cleaned = self.clean_page_text(raw_text)
                if cleaned:
                    pages.append(PageContent(
                        doc_id=doc_id,
                        source_file=basename,
                        doc_title=doc_title,
                        publisher=publisher,
                        document_type=document_type,
                        page_number=page_num,
                        total_pages=total_pages,
                        text=cleaned,
                        relevance_category=relevance,
                        metadata={
                            "publication_date": doc_info.get("publication_version_date", "Unknown"),
                            "url": doc_info.get("url", "")
                        }
                    ))
        except Exception as e:
            print(f"Error loading PDF {pdf_path}: {e}")

        return pages

    def load_all_documents(self) -> List[PageContent]:
        """Load and extract pages from all downloaded PDF documents in raw_dir."""
        all_pages: List[PageContent] = []
        pdf_files = sorted(list(self.raw_dir.glob("*.pdf")))
        print(f"Found {len(pdf_files)} PDF files in {self.raw_dir}")

        for pdf_path in pdf_files:
            pages = self.load_pdf(pdf_path)
            print(f"  Loaded {len(pages)} non-empty pages from {pdf_path.name}")
            all_pages.extend(pages)

        return all_pages
