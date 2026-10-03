"""Core-final ingestion: Phase 5E production corpus + the two verified gap-closure sources.

Reuses the existing Phase 5E pipeline (SectionAwareChunker, formula enrichment, provenance metadata)
without introducing a new retrieval architecture. Writes a NEW store so that every earlier index
remains byte-for-byte reproducible:

    data/chroma_db/                     (Phase 5C baseline)      - untouched
    data/chroma_db_phase5d_sectioned/   (Phase 5D)               - untouched
    data/chroma_db_phase5e/             (Phase 5E)               - untouched
    data/chroma_db_core_final/          (Phase 5E corpus + 2)    - production store

Added sources (verified against NTRS before download, see data/metadata/sources.json):
    - NTRS 20000033269  Arakere & Swanson (2000), Fretting Stresses in Single Crystal Superalloy
      Turbine Blade Attachments  [NUMERICAL_ANALYSIS]
    - NTRS 19930003401  NASA-CR-189111, Meier/Nissley/Sheffler (1991), TBC Life Prediction Model
      Development Phase II (EB-PVD)  [LABORATORY_EXPERIMENT]
"""
import json
import re
import statistics
import time
from pathlib import Path
from typing import Any, Dict, List

from .chunker import TextChunk
from .document_loader import DocumentLoader
from .ingest_phase5e import (
    FORMULA_ENRICHMENT_DOCS,
    PHASE5D_CORPUS_DOCS,
    PHASE5E_NEW_DOCS,
    enrich_chunk_with_formulas,
)
from .section_chunker import SectionAwareChunker

CORE_FINAL_NEW_DOCS = [
    "NASA_MSFC_2000_Arakere_Fretting_Stresses_SC_Blade_Attachments.pdf",
    "NASA_CR_189111_EBPVD_TBC_Life_Prediction.pdf",
]

CORE_FINAL_CHROMA_DIR = Path("data/chroma_db_core_final")
CORE_FINAL_COLLECTION = "fmea_aerospace_knowledge_core_final"

# Provenance fields copied from sources.json onto every chunk (primitive values only).
PROVENANCE_FIELDS = (
    "official_report_number",
    "ntrs_document_id",
    "evidence_category",
    "technical_domain",
)

# Running page header printed on every page of the Arakere preprint (OCR variants: "Nagaraj",
# "IVagaraj", "l_lagaraj", "]%garaj" ...). Left in place it adds the words "Single Crystal Superalloy
# Turbine Blade" to every chunk, so unrelated turbine-blade queries (creep, TMF) were pulled toward
# this paper. Only this boilerplate is removed; body text is untouched.
RUNNING_HEADER_PATTERNS = {
    "NASA_MSFC_2000_Arakere_Fretting_Stresses_SC_Blade_Attachments.pdf": re.compile(
        r"\S{0,12}a?raj\s*K[.,]?\s+Arakere\s+and\s+Gregory\s+Swanson\s+"
        r"Fretting\s+Stresses\s+in\s+Single\s+Crystal\s+Super\S*\s+Turbine\s+Blade\s+Attachments",
        re.IGNORECASE,
    ),
}


def strip_running_header(source_file: str, text: str) -> str:
    pattern = RUNNING_HEADER_PATTERNS.get(source_file)
    if not pattern:
        return text
    return pattern.sub(" ", text).strip()


def _publication_year(info: Dict[str, Any]) -> int:
    if isinstance(info.get("publication_year"), int):
        return info["publication_year"]
    m = re.search(r"(19|20)\d{2}", str(info.get("publication_version_date", "")))
    return int(m.group(0)) if m else 0


def _provenance_for(info: Dict[str, Any]) -> Dict[str, Any]:
    prov = {k: str(info.get(k, "")) for k in PROVENANCE_FIELDS}
    if not prov["official_report_number"]:
        prov["official_report_number"] = str(info.get("id", ""))
    prov["publication_year"] = _publication_year(info)
    audit = info.get("dataset_population_audit") or {}
    prov["applicability_scope"] = str(audit.get("generalization_constraint", ""))[:500]
    return prov


def run_core_final_ingestion(
    output_chroma_dir: Path = CORE_FINAL_CHROMA_DIR,
    collection_name: str = CORE_FINAL_COLLECTION,
    batch_size: int = 64,
) -> Dict[str, Any]:
    start = time.time()
    raw_dir = Path("data/raw")
    metadata_file = Path("data/metadata/sources.json")
    output_chroma_dir = Path(output_chroma_dir)
    output_chroma_dir.mkdir(parents=True, exist_ok=True)

    corpus = PHASE5D_CORPUS_DOCS + PHASE5E_NEW_DOCS + CORE_FINAL_NEW_DOCS
    # Formula enrichment is applied only where the extractor's named patterns were validated
    # (Phase 5E). A trial run on the two new OCR'd reports produced 533 *unnamed* generic matches
    # (any OCR line containing '='), e.g. "Cycle Life for Tref = 93C (200F)" - these are not
    # validated formulas and would pollute chunk text, so the new sources are indexed un-enriched.
    formula_docs = set(FORMULA_ENRICHMENT_DOCS)

    loader = DocumentLoader(raw_dir, metadata_file)
    pages, page_counts = [], {}
    for name in corpus:
        path = raw_dir / name
        if not path.exists():
            raise FileNotFoundError(f"Corpus document missing: {path}")
        doc_pages = loader.load_pdf(path)
        for p in doc_pages:
            p.text = strip_running_header(name, p.text)
        page_counts[name] = len(doc_pages)
        pages.extend(doc_pages)
        print(f"  Loaded {len(doc_pages):4d} pages  {name}{'  [NEW]' if name in CORE_FINAL_NEW_DOCS else ''}")

    chunker = SectionAwareChunker(target_chunk_size=1000, max_chunk_size=1400, min_chunk_size=150, chunk_overlap=150)
    chunks: List[TextChunk] = chunker.chunk_all_pages(pages)

    enriched: List[TextChunk] = []
    formula_chunks, formula_total = 0, 0
    for c in chunks:
        if c.source_file in formula_docs:
            c = enrich_chunk_with_formulas(c)
            if c.metadata.get("has_formulas"):
                formula_chunks += 1
                formula_total += int(c.metadata.get("formula_count", 0))
        enriched.append(c)

    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions

    client = chromadb.PersistentClient(path=str(output_chroma_dir), settings=Settings(anonymized_telemetry=False))
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass
    collection = client.create_collection(
        name=collection_name,
        embedding_function=embedding_functions.DefaultEmbeddingFunction(),
        metadata={"hnsw:space": "cosine"},
    )

    prov_cache: Dict[str, Dict[str, Any]] = {}
    for i in range(0, len(enriched), batch_size):
        batch = enriched[i : i + batch_size]
        metas = []
        for c in batch:
            if c.source_file not in prov_cache:
                prov_cache[c.source_file] = _provenance_for(loader.sources_metadata.get(c.source_file, {}))
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
                **prov_cache[c.source_file],
            }
            if c.metadata.get("has_formulas"):
                m["has_formulas"] = True
                m["formula_count"] = int(c.metadata.get("formula_count", 0))
                m["formula_names"] = str(c.metadata.get("formula_names", ""))
            metas.append(m)
        collection.upsert(ids=[c.chunk_id for c in batch], documents=[c.text for c in batch], metadatas=metas)

    lengths = [len(c.text) for c in enriched]
    stats = {
        "store": str(output_chroma_dir),
        "collection": collection_name,
        "total_docs": len(corpus),
        "new_docs": CORE_FINAL_NEW_DOCS,
        "total_pages": len(pages),
        "total_chunks": len(enriched),
        "new_source_chunks": {d: sum(1 for c in enriched if c.source_file == d) for d in CORE_FINAL_NEW_DOCS},
        "formula_enriched_chunks": formula_chunks,
        "total_formulas_extracted": formula_total,
        "formulas_in_new_sources": sum(
            int(c.metadata.get("formula_count", 0)) for c in enriched if c.source_file in CORE_FINAL_NEW_DOCS
        ),
        "average_chunk_size": round(statistics.mean(lengths), 1),
        "doc_page_counts": page_counts,
        "indexed_records": collection.count(),
        "indexing_time_sec": round(time.time() - start, 1),
    }
    out = Path("data/output/core_final_ingestion_stats.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(json.dumps(stats, indent=2))
    return stats


if __name__ == "__main__":
    run_core_final_ingestion()
