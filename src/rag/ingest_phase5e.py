"""Phase 5E ingestion: extends the Phase 5D corpus with new technical sources and formula enrichment.

Adds 3 new NASA technical reports addressing verified corpus gaps:
- NASA/TP-2013-217830: Turbine blade life from field data (thermal fatigue, TMF)
- NASA Creep-Fatigue Hot Section: Creep-fatigue interaction life prediction
- NASA/CR-198472: Internal cooling passages heat transfer

Also enriches MIL-STD-1629A chunks containing detected formulas with
structured formula metadata for improved criticality retrieval.
"""
import json
import time
import statistics
from pathlib import Path
from typing import List, Dict, Any

from .config import RAGConfig
from .document_loader import DocumentLoader
from .section_chunker import SectionAwareChunker
from .vector_store import ChromaVectorStore
from .chunker import TextChunk
from .formula_extractor import extract_formulas_from_text


# Phase 5D baseline corpus
PHASE5D_CORPUS_DOCS = [
    "EASA_CS-E_Amnd5_EasyAccessRules.pdf",
    "FAA_AC_25.1309-1A.pdf",
    "FAA_AC_25.1309-1B.pdf",
    "FAA_AC_33.75-1A.pdf",
    "MIL-STD-1629A.pdf",
    "NASA-STD-8729.1A.pdf",
    "NASA_ASRS_Maintenance_Incident_Reports.pdf",
    "NASA_C-MAPSS_Damage_Propagation_Modeling.pdf"
]

# Phase 5E new sources (gap-filling)
PHASE5E_NEW_DOCS = [
    "NASA_TP_2013_217830_Turbine_Blade_Life.pdf",
    "NASA_Fatigue_Life_Prediction_Hot_Section.pdf",
    "NASA_Internal_Cooling_Passages_Heat_Transfer.pdf",
]

# Documents where formula extraction should be applied
FORMULA_ENRICHMENT_DOCS = [
    "MIL-STD-1629A.pdf",
    "NASA-STD-8729.1A.pdf",
]


def enrich_chunk_with_formulas(chunk: TextChunk) -> TextChunk:
    """Detect formulas in a chunk and append structured formula text for improved retrieval.
    
    This does NOT modify the chunk's original text — it appends a separate
    formula block at the end. The original provenance is preserved.
    """
    formulas = extract_formulas_from_text(
        text=chunk.text,
        source_document=chunk.source_file,
        page_number=chunk.page_number,
        section=chunk.metadata.get("section_id", "")
    )
    
    if not formulas:
        return chunk
    
    # Append formula enrichment block
    formula_blocks = []
    for f in formulas:
        formula_blocks.append(f.to_indexable_text())
    
    enrichment = "\n\n---\n[FORMULA ENRICHMENT]\n" + "\n\n".join(formula_blocks)
    
    enriched_text = chunk.text + enrichment
    enriched_metadata = dict(chunk.metadata)
    enriched_metadata["has_formulas"] = True
    enriched_metadata["formula_count"] = len(formulas)
    enriched_metadata["formula_names"] = ",".join(f.formula_name for f in formulas if f.formula_name)
    
    return TextChunk(
        chunk_id=chunk.chunk_id,
        doc_id=chunk.doc_id,
        source_file=chunk.source_file,
        doc_title=chunk.doc_title,
        publisher=chunk.publisher,
        document_type=chunk.document_type,
        page_number=chunk.page_number,
        chunk_index=chunk.chunk_index,
        text=enriched_text,
        metadata=enriched_metadata
    )


def run_phase5e_ingestion(
    output_chroma_dir: Path = Path("data/chroma_db_phase5e"),
    collection_name: str = "fmea_aerospace_knowledge_phase5e",
    batch_size: int = 64
) -> Dict[str, Any]:
    """Run Phase 5E ingestion: expanded corpus + formula enrichment."""
    start_time = time.time()
    raw_dir = Path("data/raw")
    metadata_file = Path("data/metadata/sources.json")
    output_chroma_dir = Path(output_chroma_dir)
    output_chroma_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("      FMEA-GPT PHASE 5E KNOWLEDGE EXPANSION INGESTION")
    print("=" * 70)
    print(f"Raw data directory : {raw_dir}")
    print(f"Target Chroma dir  : {output_chroma_dir}")
    print(f"Collection name    : {collection_name}")
    print("=" * 70)

    # 1. Load all documents (Phase 5D baseline + Phase 5E new)
    all_corpus_docs = PHASE5D_CORPUS_DOCS + PHASE5E_NEW_DOCS
    print(f"\n[Step 1] Loading document pages ({len(PHASE5D_CORPUS_DOCS)} baseline + {len(PHASE5E_NEW_DOCS)} new)...")
    loader = DocumentLoader(raw_dir, metadata_file)
    all_pages = []
    doc_page_counts = {}
    
    for doc_name in all_corpus_docs:
        doc_path = raw_dir / doc_name
        if doc_path.exists():
            pages = loader.load_pdf(doc_path)
            is_new = doc_name in PHASE5E_NEW_DOCS
            marker = " [NEW 5E]" if is_new else ""
            print(f"  Loaded {len(pages)} pages from {doc_name}{marker}")
            all_pages.extend(pages)
            doc_page_counts[doc_name] = len(pages)
        else:
            print(f"  Warning: Document not found: {doc_name}")

    # 2. Chunk using SectionAwareChunker
    print(f"\n[Step 2] Chunking {len(all_pages)} pages with SectionAwareChunker...")
    chunker = SectionAwareChunker(
        target_chunk_size=1000,
        max_chunk_size=1400,
        min_chunk_size=150,
        chunk_overlap=150
    )
    all_chunks: List[TextChunk] = chunker.chunk_all_pages(all_pages)
    print(f"  Generated {len(all_chunks)} section-aware chunks.")

    # 3. Formula enrichment on applicable documents
    print(f"\n[Step 3] Applying formula extraction to {len(FORMULA_ENRICHMENT_DOCS)} documents...")
    formula_enriched_count = 0
    total_formulas_found = 0
    enriched_chunks = []
    
    for chunk in all_chunks:
        if chunk.source_file in FORMULA_ENRICHMENT_DOCS:
            enriched = enrich_chunk_with_formulas(chunk)
            if enriched.metadata.get("has_formulas"):
                formula_enriched_count += 1
                total_formulas_found += enriched.metadata.get("formula_count", 0)
            enriched_chunks.append(enriched)
        else:
            enriched_chunks.append(chunk)
    
    print(f"  Chunks with formulas detected: {formula_enriched_count}")
    print(f"  Total formulas extracted: {total_formulas_found}")

    # 4. Compute statistics
    chunk_lengths = [len(c.text) for c in enriched_chunks]
    avg_chunk_size = statistics.mean(chunk_lengths) if chunk_lengths else 0
    median_chunk_size = statistics.median(chunk_lengths) if chunk_lengths else 0
    
    # Count chunks from new vs baseline documents
    new_doc_chunks = [c for c in enriched_chunks if c.source_file in PHASE5E_NEW_DOCS]
    baseline_chunks = [c for c in enriched_chunks if c.source_file not in PHASE5E_NEW_DOCS]
    
    stats = {
        "phase": "5E",
        "baseline_docs": len(PHASE5D_CORPUS_DOCS),
        "new_docs": len(PHASE5E_NEW_DOCS),
        "total_docs": len(all_corpus_docs),
        "total_pages_processed": len(all_pages),
        "total_chunks": len(enriched_chunks),
        "baseline_chunks": len(baseline_chunks),
        "new_source_chunks": len(new_doc_chunks),
        "average_chunk_size": round(avg_chunk_size, 1),
        "median_chunk_size": round(median_chunk_size, 1),
        "min_chunk_size": min(chunk_lengths) if chunk_lengths else 0,
        "max_chunk_size": max(chunk_lengths) if chunk_lengths else 0,
        "formula_enriched_chunks": formula_enriched_count,
        "total_formulas_extracted": total_formulas_found,
        "doc_page_counts": doc_page_counts,
        "storage_path": str(output_chroma_dir)
    }

    print("\n--- PHASE 5E INGESTION STATISTICS ---")
    print(f"Baseline Chunks     : {stats['baseline_chunks']}")
    print(f"New Source Chunks    : {stats['new_source_chunks']}")
    print(f"Total Chunks        : {stats['total_chunks']}")
    print(f"Average Chunk Size  : {stats['average_chunk_size']} chars")
    print(f"Formula Enriched    : {stats['formula_enriched_chunks']} chunks")

    # 5. Index into ChromaDB
    print(f"\n[Step 4] Indexing {len(enriched_chunks)} chunks into ChromaDB...")
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions

    client = chromadb.PersistentClient(
        path=str(output_chroma_dir),
        settings=Settings(anonymized_telemetry=False)
    )
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    
    # Delete existing collection if present (clean rebuild)
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass
    
    collection = client.create_collection(
        name=collection_name,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )

    total_chunks = len(enriched_chunks)
    for i in range(0, total_chunks, batch_size):
        batch = enriched_chunks[i : i + batch_size]
        ids = [c.chunk_id for c in batch]
        documents = [c.text for c in batch]
        metadatas = []
        for c in batch:
            m = {
                "doc_id": c.doc_id,
                "source_file": c.source_file,
                "doc_title": c.doc_title,
                "publisher": c.publisher,
                "document_type": c.document_type,
                "page_number": int(c.page_number),
                "chunk_index": int(c.chunk_index),
                "section_id": str(c.metadata.get("section_id", "General")),
                "section_title": str(c.metadata.get("section_title", "General")),
                "section_hierarchy": str(c.metadata.get("section_hierarchy", "General")),
            }
            # Add formula metadata if present
            if c.metadata.get("has_formulas"):
                m["has_formulas"] = True
                m["formula_count"] = int(c.metadata.get("formula_count", 0))
                m["formula_names"] = str(c.metadata.get("formula_names", ""))
            metadatas.append(m)

        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        if (i // batch_size + 1) % 5 == 0 or (i + batch_size) >= total_chunks:
            print(f"  Indexed batch {i // batch_size + 1}: {min(i + batch_size, total_chunks)}/{total_chunks} chunks")

    stats["indexing_time_sec"] = round(time.time() - start_time, 2)
    stats["total_indexed_records"] = collection.count()
    print(f"\nIndexing complete in {stats['indexing_time_sec']}s. Verified records: {stats['total_indexed_records']}.")

    # Save statistics
    stats_dir = Path("data/output")
    stats_dir.mkdir(parents=True, exist_ok=True)
    with open(stats_dir / "phase5e_ingestion_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(f"Statistics saved to {stats_dir / 'phase5e_ingestion_stats.json'}")

    return stats


if __name__ == "__main__":
    run_phase5e_ingestion()
