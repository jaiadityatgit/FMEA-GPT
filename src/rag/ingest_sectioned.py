"""Script to ingest documents into the experimental section-aware ChromaDB store for Phase 5D."""
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


INDEXED_CORPUS_DOCS = [
    "EASA_CS-E_Amnd5_EasyAccessRules.pdf",
    "FAA_AC_25.1309-1A.pdf",
    "FAA_AC_25.1309-1B.pdf",
    "FAA_AC_33.75-1A.pdf",
    "MIL-STD-1629A.pdf",
    "NASA-STD-8729.1A.pdf",
    "NASA_ASRS_Maintenance_Incident_Reports.pdf",
    "NASA_C-MAPSS_Damage_Propagation_Modeling.pdf"
]


def run_sectioned_ingestion(
    output_chroma_dir: Path = Path("data/chroma_db_phase5d_sectioned"),
    collection_name: str = "fmea_aerospace_knowledge_sectioned",
    batch_size: int = 64
) -> Dict[str, Any]:
    """Run section-aware ingestion into a separate experimental ChromaDB collection."""
    start_time = time.time()
    raw_dir = Path("data/raw")
    metadata_file = Path("data/metadata/sources.json")
    output_chroma_dir = Path(output_chroma_dir)
    output_chroma_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("      FMEA-GPT PHASE 5D SECTION-AWARE INGESTION")
    print("=" * 70)
    print(f"Raw data directory : {raw_dir}")
    print(f"Target Chroma dir  : {output_chroma_dir}")
    print(f"Collection name    : {collection_name}")
    print("=" * 70)

    # 1. Load Documents (strictly 1:1 with baseline corpus)
    print("\n[Step 1] Loading document pages for existing 8 corpus documents...")
    loader = DocumentLoader(raw_dir, metadata_file)
    all_pages = []
    for doc_name in INDEXED_CORPUS_DOCS:
        doc_path = raw_dir / doc_name
        if doc_path.exists():
            pages = loader.load_pdf(doc_path)
            print(f"  Loaded {len(pages)} pages from {doc_name}")
            all_pages.extend(pages)
        else:
            print(f"  Warning: Expected corpus document not found: {doc_name}")

    # 2. Chunk using SectionAwareChunker
    print("\n[Step 2] Chunking with SectionAwareChunker...")
    chunker = SectionAwareChunker(
        target_chunk_size=1000,
        max_chunk_size=1400,
        min_chunk_size=150,
        chunk_overlap=150
    )
    section_chunks: List[TextChunk] = chunker.chunk_all_pages(all_pages)
    print(f"Generated {len(section_chunks)} section-aware chunks.")

    # 3. Compute Structural Statistics
    chunk_lengths = [len(c.text) for c in section_chunks]
    avg_chunk_size = statistics.mean(chunk_lengths) if chunk_lengths else 0
    median_chunk_size = statistics.median(chunk_lengths) if chunk_lengths else 0
    
    # Section statistics
    section_chunks_with_sec = [c for c in section_chunks if c.metadata.get("section_id") != "General"]
    pct_with_section = len(section_chunks_with_sec) / len(section_chunks) * 100 if section_chunks else 0
    
    # Section depths
    depths = []
    for c in section_chunks:
        hierarchy = c.metadata.get("section_hierarchy", "")
        if hierarchy and hierarchy != "General":
            depths.append(len(hierarchy.split(" > ")))
        else:
            depths.append(1)
    avg_section_depth = statistics.mean(depths) if depths else 1.0

    stats = {
        "old_chunk_count": 2446,
        "new_chunk_count": len(section_chunks),
        "total_pages_processed": len(all_pages),
        "average_chunk_size": round(avg_chunk_size, 1),
        "median_chunk_size": round(median_chunk_size, 1),
        "min_chunk_size": min(chunk_lengths) if chunk_lengths else 0,
        "max_chunk_size": max(chunk_lengths) if chunk_lengths else 0,
        "chunks_with_explicit_section": len(section_chunks_with_sec),
        "percentage_with_section": round(pct_with_section, 1),
        "average_section_depth": round(avg_section_depth, 2),
        "storage_path": str(output_chroma_dir)
    }

    print("\n--- CHUNKING STATISTICS ---")
    print(f"Old Baseline Chunks    : {stats['old_chunk_count']}")
    print(f"New Section-Aware Chunks: {stats['new_chunk_count']}")
    print(f"Average Chunk Size     : {stats['average_chunk_size']} chars")
    print(f"Median Chunk Size      : {stats['median_chunk_size']} chars")
    print(f"Chunks with Section ID : {stats['chunks_with_explicit_section']} ({stats['percentage_with_section']}%)")
    print(f"Average Section Depth  : {stats['average_section_depth']}")

    # 4. Index into experimental ChromaDB
    print("\n[Step 3] Indexing into experimental ChromaDB...")
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions

    client = chromadb.PersistentClient(
        path=str(output_chroma_dir),
        settings=Settings(anonymized_telemetry=False)
    )
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )

    total_chunks = len(section_chunks)
    for i in range(0, total_chunks, batch_size):
        batch = section_chunks[i : i + batch_size]
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
            metadatas.append(m)

        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        if (i // batch_size + 1) % 5 == 0 or (i + batch_size) >= total_chunks:
            print(f"  Indexed batch {i // batch_size + 1}: {min(i + batch_size, total_chunks)}/{total_chunks} chunks")

    stats["indexing_time_sec"] = round(time.time() - start_time, 2)
    stats["total_indexed_records"] = collection.count()
    print(f"\nIndexing complete in {stats['indexing_time_sec']}s. Verified records: {stats['total_indexed_records']}.")

    # Save statistics
    scratch_dir = Path("scratch")
    scratch_dir.mkdir(exist_ok=True)
    with open(scratch_dir / "section_chunking_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    return stats


if __name__ == "__main__":
    run_sectioned_ingestion()
