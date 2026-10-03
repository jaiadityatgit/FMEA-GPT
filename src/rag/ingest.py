"""Document ingestion and indexing execution script for FMEA-GPT RAG."""
import argparse
import time
from pathlib import Path
from .config import RAGConfig
from .document_loader import DocumentLoader
from .chunker import AerospaceChunker
from .vector_store import ChromaVectorStore


def run_ingestion(
    reset: bool = False,
    doc_filter: list = None,
    batch_size: int = 64
) -> None:
    """Run the complete ingestion pipeline: load PDFs -> chunk -> embed -> index into ChromaDB."""
    start_time = time.time()
    config = RAGConfig()
    config.ensure_directories()

    print("=" * 70)
    print("      FMEA-GPT AEROSPACE RAG INGESTION PIPELINE")
    print("=" * 70)
    print(f"Raw data directory : {config.raw_dir}")
    print(f"Chroma storage     : {config.chroma_dir}")
    print(f"Collection name    : {config.collection_name}")
    print(f"Embedding model    : {config.embedding_model_name}")
    print(f"Chunk size/overlap : {config.chunk_size} / {config.chunk_overlap}")
    print("=" * 70)

    # 1. Initialize Vector Store
    vector_store = ChromaVectorStore(config)
    if reset:
        print("\n[Step 0] Resetting existing ChromaDB collection...")
        vector_store.reset()

    # 2. Load Documents
    print("\n[Step 1] Loading and extracting document pages...")
    loader = DocumentLoader(config.raw_dir, config.metadata_file)
    
    if doc_filter:
        pdf_paths = [config.raw_dir / name for name in doc_filter]
        all_pages = []
        for p in pdf_paths:
            if p.exists():
                all_pages.extend(loader.load_pdf(p))
            else:
                print(f"Warning: Specified file not found: {p}")
    else:
        all_pages = loader.load_all_documents()

    if not all_pages:
        print("No pages extracted. Ensure PDFs are present in data/raw/.")
        return

    print(f"\nExtracted total of {len(all_pages)} pages across documents.")

    # 3. Chunk Pages
    print("\n[Step 2] Chunking pages into semantic aerospace passages...")
    chunker = AerospaceChunker(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        min_chunk_size=config.min_chunk_size
    )
    all_chunks = chunker.chunk_all_pages(all_pages)
    print(f"Generated {len(all_chunks)} semantic chunks.")

    # 4. Index Chunks into ChromaDB
    print("\n[Step 3] Generating embeddings and indexing into ChromaDB...")
    indexed_count = vector_store.add_chunks(all_chunks, batch_size=batch_size)

    elapsed = time.time() - start_time
    stats = vector_store.get_stats()

    print("\n" + "=" * 70)
    print("            INGESTION COMPLETE SUMMARY")
    print("=" * 70)
    print(f"Total pages processed : {len(all_pages)}")
    print(f"Total chunks created   : {len(all_chunks)}")
    print(f"Total records in DB   : {stats['document_count']}")
    print(f"Total time elapsed    : {elapsed:.2f} seconds")
    print(f"Database location     : {stats['storage_path']}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Ingest aerospace documents into FMEA-GPT ChromaDB.")
    parser.add_argument("--reset", action="store_true", help="Clear existing collection before indexing.")
    parser.add_argument("--docs", nargs="+", help="Specific PDF filenames to ingest (e.g., MIL-STD-1629A.pdf).")
    parser.add_argument("--batch-size", type=int, default=64, help="Embedding batch size.")
    args = parser.parse_args()

    run_ingestion(reset=args.reset, doc_filter=args.docs, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
