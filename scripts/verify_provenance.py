"""Test provenance of newly integrated Phase 5E sources across mandatory queries."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.rag.config import RAGConfig
from src.rag.retriever import AerospaceRetriever

queries = [
    "high pressure turbine blade thermomechanical fatigue",
    "CFM56 turbine blade life thermal mechanical fatigue",
    "turbine blade internal cooling passage heat transfer",
    "cooling passage flow starvation",
    "turbine blade oxidation erosion"
]

cfg = RAGConfig.get_production_config() if hasattr(RAGConfig, "get_production_config") else RAGConfig(
    chroma_dir=Path("data/chroma_db_phase5e"),
    collection_name="fmea_aerospace_knowledge_phase5e"
)

retriever = AerospaceRetriever(config=cfg)

print("=" * 80)
print(f"PROVENANCE VERIFICATION ON PRODUCTION STORE ({cfg.chroma_dir.name}):")
print("=" * 80)

for q in queries:
    print(f"\nQUERY: '{q}'")
    results = retriever.retrieve(q, top_k=3)
    for rank, r in enumerate(results, 1):
        print(f"  Rank {rank}: {r.source_document} | Page {r.page_number} | Sim: {r.similarity_score*100:.1f}%")
        print(f"    Title: {r.doc_title}")
        print(f"    Section: {r.section or r.metadata.get('section_id', 'N/A')}")
        print(f"    Excerpt: {r.text[:120].strip().replace(chr(10), ' ')}...")
