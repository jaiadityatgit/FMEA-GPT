"""Section-aware aerospace document chunker for FMEA-GPT Phase 5D.

Preserves hierarchical document structures:
Document -> Chapter / Task -> Section -> Subsection -> Technical Block.
Stitches cross-page paragraphs, avoids document-title header dilution,
and enriches chunks with section metadata.
"""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from .document_loader import PageContent
from .chunker import TextChunk


# Regular expressions for detecting aerospace standards section headings
HEADING_PATTERNS = [
    # 1. Military Task headings (MIL-STD-1629A: "TASK 101 FAILURE MODE AND EFFECTS ANALYSIS")
    (r'^(TASK\s+\d{3}[A-Z]?)\s+[-:.]?\s*(.+)$', "task"),
    
    # 2. European Certification Specifications (CS-E / CS-25: "CS-E 510 Safety Analysis", "CS-E 800 Bird Strike")
    (r'^(CS-[A-Z]+\s+\d+(?:\([a-z0-9]+\))?)\s+[-:.]?\s*(.+)$', "cs_spec"),
    
    # 3. EASA Acceptable Means of Compliance (AMC E 510 Safety Analysis)
    (r'^(AMC\s+[A-Z]+\s+\d+(?:\([a-z0-9]+\))?)\s+[-:.]?\s*(.+)$', "amc_spec"),
    
    # 4. Standard Decimal Sections (e.g., "4.4.3 Severity classification", "1.1 Scope", "3.1.19 Single failure point")
    (r'^(\d+\.\d+(?:\.\d+)*)\s+([A-Z][A-Za-z0-9\s,\-\(\)\/\'\"]{2,80})$', "decimal_section"),
    
    # 5. Major Numbered Sections (e.g., "7. SAFETY ANALYSIS CRITERIA.", "1. SCOPE", "4. GENERAL REQUIREMENTS")
    (r'^(\d+\.)\s+([A-Z0-9\s,\-\(\)\/]{3,80})\.?$', "major_section"),
    
    # 6. FAA Alphanumeric Subsections (e.g., "7a. Hazardous Engine Effects.", "8b. Minor Engine Effects.")
    (r'^(\d+[a-z]\.)\s+([A-Z][A-Za-z0-9\s,\-\(\)\/]{2,80})\.?$', "alpha_section"),
    
    # 7. Regulatory code sections (e.g., "§ 33.75 Safety analysis", "14 CFR 33.75")
    (r'^(§\s*\d+\.\d+|14\s+CFR\s+§?\s*\d+\.\d+)\s+[-:.]?\s*(.+)$', "cfr_section"),
    
    # 8. Appendices (e.g., "APPENDIX A - FMEA WORKSHEETS", "APPENDIX B")
    (r'^(APPENDIX\s+[A-Z0-9]+)\s*[-:.]?\s*(.*)$', "appendix"),
]


@dataclass
class SectionContext:
    """Active hierarchical section tracking."""
    task_or_chapter: str = ""
    section_id: str = ""
    section_title: str = ""
    section_type: str = ""
    
    @property
    def display_prefix(self) -> str:
        """Compact semantic prefix for embedding without verbose document title dilution."""
        if self.section_id and self.section_title:
            return f"[Section {self.section_id}: {self.section_title}]\n"
        elif self.task_or_chapter:
            return f"[{self.task_or_chapter}]\n"
        return ""
    
    @property
    def hierarchy_str(self) -> str:
        parts = [p for p in [self.task_or_chapter, f"{self.section_id} {self.section_title}".strip()] if p]
        return " > ".join(parts) if parts else "General"


class SectionAwareChunker:
    """Hierarchical, section-aware chunker for technical aerospace standards."""

    def __init__(
        self,
        target_chunk_size: int = 1000,
        max_chunk_size: int = 1400,
        min_chunk_size: int = 150,
        chunk_overlap: int = 150
    ):
        self.target_chunk_size = target_chunk_size
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.chunk_overlap = chunk_overlap

    def detect_heading(self, line: str) -> Optional[Tuple[str, str, str]]:
        """Identify if a line is a structural aerospace section heading.
        
        Returns:
            Tuple of (section_id, section_title, heading_type) or None.
        """
        line_clean = line.strip()
        if not line_clean or len(line_clean) > 120:
            return None
        
        # Avoid false positives on table headers or sentences ending in full stop with many words
        if line_clean.endswith(".") and len(line_clean.split()) > 12:
            return None

        for pattern, h_type in HEADING_PATTERNS:
            m = re.match(pattern, line_clean, re.IGNORECASE)
            if m:
                sec_id = m.group(1).strip()
                sec_title = m.group(2).strip().rstrip(".")
                return sec_id, sec_title, h_type
        return None

    def _split_into_semantic_blocks(self, text: str) -> List[Tuple[str, Optional[Tuple[str, str, str]]]]:
        """Split text into semantic blocks while tagging inline headings."""
        lines = text.split("\n")
        blocks: List[Tuple[str, Optional[Tuple[str, str, str]]]] = []
        current_lines: List[str] = []
        current_heading: Optional[Tuple[str, str, str]] = None

        for line in lines:
            line_str = line.strip()
            heading = self.detect_heading(line_str)
            if heading:
                # Flush previous paragraph block
                if current_lines:
                    block_text = "\n".join(current_lines).strip()
                    if block_text:
                        blocks.append((block_text, current_heading))
                    current_lines = []
                current_heading = heading
                # Include the heading line as start of new block
                current_lines.append(line_str)
            else:
                if not line_str:
                    # Empty line indicates paragraph boundary
                    if current_lines:
                        block_text = "\n".join(current_lines).strip()
                        if block_text:
                            blocks.append((block_text, current_heading))
                        current_lines = []
                else:
                    current_lines.append(line_str)

        if current_lines:
            block_text = "\n".join(current_lines).strip()
            if block_text:
                blocks.append((block_text, current_heading))

        return blocks

    def chunk_document_pages(self, pages: List[PageContent]) -> List[TextChunk]:
        """Chunk all pages of a single document with cross-page paragraph continuity."""
        if not pages:
            return []

        chunks: List[TextChunk] = []
        context = SectionContext()
        chunk_idx = 0

        # Sort pages by page number
        sorted_pages = sorted(pages, key=lambda p: p.page_number)
        doc_id = sorted_pages[0].doc_id
        source_file = sorted_pages[0].source_file
        doc_title = sorted_pages[0].doc_title
        publisher = sorted_pages[0].publisher
        doc_type = sorted_pages[0].document_type

        # Iterate through pages, maintaining section context across boundaries
        for i, page in enumerate(sorted_pages):
            page_text = page.text.strip()
            if not page_text:
                continue

            blocks = self._split_into_semantic_blocks(page_text)
            current_chunk_parts: List[str] = []
            current_char_count = 0
            page_chunk_start_page = page.page_number

            for block_text, heading in blocks:
                if heading:
                    sec_id, sec_title, h_type = heading
                    if h_type in ["task", "major_section", "appendix"]:
                        context.task_or_chapter = f"{sec_id} {sec_title}".strip()
                        context.section_id = sec_id
                        context.section_title = sec_title
                    else:
                        context.section_id = sec_id
                        context.section_title = sec_title
                    context.section_type = h_type

                block_len = len(block_text)

                # Check if adding block exceeds target and we have accumulated enough text
                if current_char_count + block_len > self.target_chunk_size and current_chunk_parts:
                    chunk_body = "\n\n".join(current_chunk_parts).strip()
                    if len(chunk_body) >= self.min_chunk_size:
                        prefix = context.display_prefix
                        chunk_text = prefix + chunk_body
                        chunks.append(TextChunk(
                            chunk_id=f"{doc_id}_p{page_chunk_start_page}_s{chunk_idx}",
                            doc_id=doc_id,
                            source_file=source_file,
                            doc_title=doc_title,
                            publisher=publisher,
                            document_type=doc_type,
                            page_number=page_chunk_start_page,
                            chunk_index=chunk_idx,
                            text=chunk_text,
                            metadata={
                                "section_id": context.section_id or "General",
                                "section_title": context.section_title or "General",
                                "section_hierarchy": context.hierarchy_str,
                                "char_count": len(chunk_text),
                                "relevance_category": page.relevance_category,
                                "is_section_aware": True
                            }
                        ))
                        chunk_idx += 1

                    # Retain overlap from end of current chunk
                    overlap_parts = []
                    accum = 0
                    for part in reversed(current_chunk_parts):
                        accum += len(part)
                        overlap_parts.insert(0, part)
                        if accum >= self.chunk_overlap:
                            break
                    current_chunk_parts = overlap_parts
                    current_char_count = sum(len(p) for p in current_chunk_parts)
                    page_chunk_start_page = page.page_number

                # If single block is huge (larger than max_chunk_size), split by sentence
                if block_len > self.max_chunk_size:
                    sentences = re.split(r'(?<=[.!?])\s+', block_text)
                    for sent in sentences:
                        s_clean = sent.strip()
                        if not s_clean:
                            continue
                        if current_char_count + len(s_clean) > self.target_chunk_size and current_chunk_parts:
                            chunk_body = " ".join(current_chunk_parts).strip()
                            if len(chunk_body) >= self.min_chunk_size:
                                prefix = context.display_prefix
                                chunk_text = prefix + chunk_body
                                chunks.append(TextChunk(
                                    chunk_id=f"{doc_id}_p{page_chunk_start_page}_s{chunk_idx}",
                                    doc_id=doc_id,
                                    source_file=source_file,
                                    doc_title=doc_title,
                                    publisher=publisher,
                                    document_type=doc_type,
                                    page_number=page_chunk_start_page,
                                    chunk_index=chunk_idx,
                                    text=chunk_text,
                                    metadata={
                                        "section_id": context.section_id or "General",
                                        "section_title": context.section_title or "General",
                                        "section_hierarchy": context.hierarchy_str,
                                        "char_count": len(chunk_text),
                                        "relevance_category": page.relevance_category,
                                        "is_section_aware": True
                                    }
                                ))
                                chunk_idx += 1
                            current_chunk_parts = []
                            current_char_count = 0
                        current_chunk_parts.append(s_clean)
                        current_char_count += len(s_clean)
                    continue

                current_chunk_parts.append(block_text)
                current_char_count += block_len + 2

            # Flush page chunks if accumulated
            if current_chunk_parts:
                chunk_body = "\n\n".join(current_chunk_parts).strip()
                if len(chunk_body) >= self.min_chunk_size:
                    prefix = context.display_prefix
                    chunk_text = prefix + chunk_body
                    chunks.append(TextChunk(
                        chunk_id=f"{doc_id}_p{page_chunk_start_page}_s{chunk_idx}",
                        doc_id=doc_id,
                        source_file=source_file,
                        doc_title=doc_title,
                        publisher=publisher,
                        document_type=doc_type,
                        page_number=page_chunk_start_page,
                        chunk_index=chunk_idx,
                        text=chunk_text,
                        metadata={
                            "section_id": context.section_id or "General",
                            "section_title": context.section_title or "General",
                            "section_hierarchy": context.hierarchy_str,
                            "char_count": len(chunk_text),
                            "relevance_category": page.relevance_category,
                            "is_section_aware": True
                        }
                    ))
                    chunk_idx += 1

        return chunks

    def chunk_all_pages(self, pages: List[PageContent]) -> List[TextChunk]:
        """Group pages by document and process with section awareness."""
        from collections import defaultdict
        docs_pages = defaultdict(list)
        for page in pages:
            docs_pages[page.doc_id].append(page)

        all_chunks: List[TextChunk] = []
        for doc_id, doc_page_list in docs_pages.items():
            chunks = self.chunk_document_pages(doc_page_list)
            all_chunks.extend(chunks)

        return all_chunks
