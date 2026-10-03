"""Aerospace technical text chunker for FMEA-GPT RAG pipeline."""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any
from .document_loader import PageContent


@dataclass
class TextChunk:
    """Represents a discrete semantic chunk of an aerospace document with rich metadata."""
    chunk_id: str
    doc_id: str
    source_file: str
    doc_title: str
    publisher: str
    document_type: str
    page_number: int
    chunk_index: int
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "source_file": self.source_file,
            "doc_title": self.doc_title,
            "publisher": self.publisher,
            "document_type": self.document_type,
            "page_number": self.page_number,
            "chunk_index": self.chunk_index,
            "text": self.text,
            "metadata": self.metadata
        }


class AerospaceChunker:
    """Splits technical aerospace pages into overlapping semantic passages."""

    def __init__(self, chunk_size: int = 900, chunk_overlap: int = 180, min_chunk_size: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text along section breaks, numbered lists, or double newlines."""
        # Split on double newlines or numbered section patterns
        paragraphs = re.split(r'\n{2,}', text)
        result = []
        for p in paragraphs:
            p_clean = p.strip()
            if p_clean:
                result.append(p_clean)
        return result

    def chunk_page(self, page: PageContent) -> List[TextChunk]:
        """Chunk a single extracted page while preserving page and source context."""
        text = page.text.strip()
        if not text:
            return []

        # If page text is within chunk size, keep it as a single coherent chunk
        if len(text) <= self.chunk_size:
            header_prefix = f"[{page.doc_title} | Page {page.page_number}]\n"
            full_chunk_text = header_prefix + text
            return [TextChunk(
                chunk_id=f"{page.doc_id}_p{page.page_number}_c0",
                doc_id=page.doc_id,
                source_file=page.source_file,
                doc_title=page.doc_title,
                publisher=page.publisher,
                document_type=page.document_type,
                page_number=page.page_number,
                chunk_index=0,
                text=full_chunk_text,
                metadata={
                    "char_count": len(full_chunk_text),
                    "relevance_category": page.relevance_category
                }
            )]

        # Recursive sliding window over paragraphs
        paragraphs = self._split_into_paragraphs(text)
        chunks: List[TextChunk] = []
        current_chunk_parts: List[str] = []
        current_length = 0
        chunk_idx = 0

        header_prefix = f"[{page.doc_title} | Page {page.page_number}]\n"
        prefix_len = len(header_prefix)

        for para in paragraphs:
            para_len = len(para)
            
            # If paragraph itself is larger than chunk_size, split by sentences
            if para_len > self.chunk_size:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sentence in sentences:
                    s_clean = sentence.strip()
                    if not s_clean:
                        continue
                    if current_length + len(s_clean) + 1 > (self.chunk_size - prefix_len) and current_chunk_parts:
                        chunk_body = " ".join(current_chunk_parts)
                        if len(chunk_body) >= self.min_chunk_size:
                            chunks.append(TextChunk(
                                chunk_id=f"{page.doc_id}_p{page.page_number}_c{chunk_idx}",
                                doc_id=page.doc_id,
                                source_file=page.source_file,
                                doc_title=page.doc_title,
                                publisher=page.publisher,
                                document_type=page.document_type,
                                page_number=page.page_number,
                                chunk_index=chunk_idx,
                                text=header_prefix + chunk_body,
                                metadata={
                                    "char_count": len(header_prefix + chunk_body),
                                    "relevance_category": page.relevance_category
                                }
                            ))
                            chunk_idx += 1
                        
                        # Retain overlap from end of current chunk
                        overlap_target = self.chunk_overlap
                        overlap_parts = []
                        accum = 0
                        for part in reversed(current_chunk_parts):
                            accum += len(part)
                            overlap_parts.insert(0, part)
                            if accum >= overlap_target:
                                break
                        current_chunk_parts = overlap_parts
                        current_length = sum(len(p) for p in current_chunk_parts)

                    current_chunk_parts.append(s_clean)
                    current_length += len(s_clean)
                continue

            # Check if adding paragraph exceeds chunk size
            if current_length + para_len + 2 > (self.chunk_size - prefix_len) and current_chunk_parts:
                chunk_body = "\n\n".join(current_chunk_parts)
                if len(chunk_body) >= self.min_chunk_size:
                    chunks.append(TextChunk(
                        chunk_id=f"{page.doc_id}_p{page.page_number}_c{chunk_idx}",
                        doc_id=page.doc_id,
                        source_file=page.source_file,
                        doc_title=page.doc_title,
                        publisher=page.publisher,
                        document_type=page.document_type,
                        page_number=page.page_number,
                        chunk_index=chunk_idx,
                        text=header_prefix + chunk_body,
                        metadata={
                            "char_count": len(header_prefix + chunk_body),
                            "relevance_category": page.relevance_category
                        }
                    ))
                    chunk_idx += 1

                # Overlap logic
                overlap_target = self.chunk_overlap
                overlap_parts = []
                accum = 0
                for part in reversed(current_chunk_parts):
                    accum += len(part)
                    overlap_parts.insert(0, part)
                    if accum >= overlap_target:
                        break
                current_chunk_parts = overlap_parts
                current_length = sum(len(p) for p in current_chunk_parts)

            current_chunk_parts.append(para)
            current_length += para_len + 2

        # Final remaining chunk
        if current_chunk_parts:
            chunk_body = "\n\n".join(current_chunk_parts)
            if len(chunk_body) >= self.min_chunk_size:
                chunks.append(TextChunk(
                    chunk_id=f"{page.doc_id}_p{page.page_number}_c{chunk_idx}",
                    doc_id=page.doc_id,
                    source_file=page.source_file,
                    doc_title=page.doc_title,
                    publisher=page.publisher,
                    document_type=page.document_type,
                    page_number=page.page_number,
                    chunk_index=chunk_idx,
                    text=header_prefix + chunk_body,
                    metadata={
                        "char_count": len(header_prefix + chunk_body),
                        "relevance_category": page.relevance_category
                    }
                ))

        return chunks

    def chunk_all_pages(self, pages: List[PageContent]) -> List[TextChunk]:
        """Process a list of pages into discrete chunks."""
        all_chunks: List[TextChunk] = []
        for page in pages:
            chunks = self.chunk_page(page)
            all_chunks.extend(chunks)
        return all_chunks
