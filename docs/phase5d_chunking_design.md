# FMEA-GPT Phase 5D — Section-Aware Chunking Design

**Document ID:** DOC-PHASE5D-CHUNKING-001  
**Repository:** `C:\fmeagpt`  
**Date:** October 2026  
**Status:** Approved Engineering Design Specification  

---

## 1. Problem Statement & Audit Findings

The Phase 4 forensic audit and Phase 5C retrieval benchmarks identified that **71.4% (10 of 14) of retrieval failures and weak queries** were caused by chunk boundary offsets, document title dilution, and missing section context.

### Forensic Analysis of the Baseline Chunker (`AerospaceChunker` in `chunker.py`)
1. **Header Dilution in Embedding Space:**
   Every chunk prepended a verbose provenance header:
   ```text
   [NASA Reliability and Maintainability (R&M) Standard for Spaceflight and Support Systems | Page 48]
   ```
   At 90–125 characters, this repetitive string consumed ~30 tokens (12–15%) of the 256 WordPiece token limit of `all-MiniLM-L6-v2`. This pulled dense vectors toward generic document-level concepts rather than specific technical definitions.
2. **Loss of Hierarchical Section Context:**
   When a document transitions from front matter to technical specifications (e.g., `CS-E 800 Bird Strike` or `MIL-STD-1629A § 4.4.3 Severity Classification`), subsequent paragraphs lose the section header if chunked independently. A paragraph discussing "ingestion of 1.15 kg flocking birds" lacked the tag `CS-E 800`, preventing BM25 and semantic matches on "FOD" or "bird ingestion standard".
3. **Hard Page-Boundary Splitting:**
   The baseline chunker processed pages strictly in isolation (`chunk_page(page)`). Sentences or paragraphs that wrapped across physical PDF page boundaries were severed into disconnected fragments.
4. **List & Requirement Severing:**
   Numbered requirements (e.g., `(a)`, `(b)`, `(1)`, `(2)`) and definitions were arbitrarily split at 900 characters rather than respecting semantic block boundaries.

---

## 2. Section-Aware Chunking Strategy

To resolve these failure modes, Phase 5D introduces **Hierarchical Structural Chunking**:

```text
Document (e.g., FAA AC 33.75-1A)
  └── Chapter / Major Task (e.g., TASK 101 or § 7 SAFETY ANALYSIS CRITERIA)
        └── Section / Paragraph (e.g., 7.a Hazardous Engine Effects)
              └── Numbered Requirement / Definition / Technical Block
```

### Core Invariants of the Section-Aware Chunker
1. **Never sever a sentence:** Split boundaries occur strictly on paragraph ends (`\n\n`), list item boundaries, or sentence terminals (`[.!?]`).
2. **Never sever a numbered requirement list:** When a parent clause introduces sub-items (e.g., *"Hazardous Engine Effects include the following: (1) ... (2) ... (3) ..."*), keep the introductory clause and its sub-items in the same chunk up to the maximum soft limit (1,200 chars).
3. **Section Header Attribution:** When a section heading is detected (e.g., `§ 4.4.3`, `CS-E 510`, `TASK 102`), retain the section number and title in chunk metadata AND prepend a compact semantic prefix (e.g., `Section 4.4.3: Severity Classification`) to the technical text.
4. **Separation of Embedding Text from Display Metadata:**
   - **Embedding Text:** `[Section: CS-E 800 Bird Ingestion] The engine must be designed to withstand the ingestion of...` (compact, high-density technical terms).
   - **Display / Provenance Metadata:** Full document title, publisher, page number, chunk index, section ID, and file path stored in ChromaDB metadata fields, NOT prepended as boilerplate embedding text.
5. **Cross-Page Paragraph Stitching:**
   If a paragraph ends without terminal punctuation at the bottom of Page $N$, stitch the continuation from the top of Page $N+1$ before segmenting.

---

## 3. Section Hierarchy Detection Patterns

Aerospace regulatory standards and military handbooks follow distinct heading conventions:

| Standard / Authority | Primary Heading Regex Pattern | Example Detected Header | Section Hierarchy Level |
| :--- | :--- | :--- | :---: |
| **MIL-STD-1629A** | `^(TASK\s+\d{3}[A-Z]?)\s+(.+)$` | `TASK 101 FAILURE MODE AND EFFECTS ANALYSIS` | Level 1 (Task) |
| **MIL-STD-1629A** | `^(\d+\.\d+(?:\.\d+)*)\s+([A-Z][A-Za-z0-9\s,\-\(\)]+)$` | `4.4.3 Severity classification` | Level 2 (Section) |
| **FAA Advisory Circulars** | `^(\d+\.)\s+([A-Z\s]{3,})\.?$` | `7. SAFETY ANALYSIS CRITERIA.` | Level 1 (Major Section) |
| **FAA Advisory Circulars** | `^(\d+[a-z]\.)\s+([A-Z][A-Za-z\s]+)\.?$` | `7a. Hazardous Engine Effects.` | Level 2 (Subsection) |
| **EASA CS-E / CS-25** | `^(CS-[A-Z]+\s+\d+)\s+([A-Za-z0-9\s\-\(\)]+)$` | `CS-E 510 Safety Analysis` | Level 1 (Code Specification) |
| **EASA AMC** | `^(AMC\s+[A-Z]+\s+\d+(?:\s+AMC\s+\d+)?)\s+([A-Za-z0-9\s\-\(\)]+)$` | `AMC E 510 Safety Analysis` | Level 2 (Acceptable Means of Compliance) |
| **NASA Standards** | `^(\d+\.\d+)\s+([A-Z][A-Za-z0-9\s,\-\(\)]+)$` | `4.4 Critical Items List` | Level 2 (Section) |
| **NASA Appendices** | `^(APPENDIX\s+[A-Z])\s+([A-Za-z0-9\s\-\(\)]+)$` | `APPENDIX A FMEA Worksheets` | Level 1 (Appendix) |

---

## 4. Metadata Schema Extensions

Each `TextChunk` produced by the section-aware chunker retains the following enriched metadata:

```python
{
    "chunk_id": "MIL-STD-1629A_p9_s4.4.3_c0",
    "doc_id": "MIL-STD-1629A",
    "source_file": "MIL-STD-1629A.pdf",
    "doc_title": "Procedures for Performing a Failure Mode, Effects and Criticality Analysis",
    "publisher": "U.S. Department of Defense (DoD)",
    "document_type": "Military Standard",
    "page_number": 9,
    "section_id": "4.4.3",
    "section_title": "Severity classification",
    "section_hierarchy": "GENERAL REQUIREMENTS > 4.4 Severity > 4.4.3 Severity classification",
    "chunk_index": 0,
    "char_count": 842,
    "text": "Section 4.4.3: Severity classification. Severity categories are assigned to provide a measure of the worst potential consequence resulting from design deficiency...",
    "metadata": {
        "is_table": False,
        "is_definition": True,
        "has_cross_page_continuation": False
    }
}
```

---

## 5. Chunk Sizing Parameters

* **Target Chunk Size:** 1,000 characters (~200–220 words / ~180 tokens).
* **Maximum Chunk Size (Soft Limit):** 1,400 characters (allows complete requirements/definitions without slicing).
* **Minimum Chunk Size:** 150 characters (avoids orphan headers or page numbers).
* **Semantic Overlap:** 150 characters (preserves transition between logical paragraphs).
* **Embedding Prefix:** `[Section: {section_id} {section_title}]\n` (only 30–50 chars, embedding high-signal technical keywords rather than verbose document titles).

---

## 6. Implementation Plan & Database Isolation

1. **Experimental Store:** All section-aware chunks will be ingested into a separate ChromaDB directory:
   `data/chroma_db_phase5d_sectioned/`
2. **Preservation of Baseline:** The existing `data/chroma_db/` (2,446 baseline chunks) will remain strictly untouched to ensure baseline comparisons are completely reproducible.
3. **Ingestion Script Execution:** A dedicated ingestion run using the section-aware chunker will measure chunk count, size distribution, section depth, and page-boundary continuity.
