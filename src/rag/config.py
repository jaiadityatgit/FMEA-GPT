"""Configuration for RAG ingestion and retrieval in FMEA-GPT."""
import os
from pathlib import Path
from dataclasses import dataclass, field

# Base workspace path
BASE_DIR = Path(__file__).resolve().parent.parent.parent

@dataclass
class RAGConfig:
    """Configuration settings for document ingestion, chunking, embedding, and vector storage."""
    base_dir: Path = BASE_DIR
    data_dir: Path = BASE_DIR / "data"
    raw_dir: Path = BASE_DIR / "data" / "raw"
    metadata_file: Path = BASE_DIR / "data" / "metadata" / "sources.json"
    chroma_dir: Path = BASE_DIR / "data" / "chroma_db"
    
    collection_name: str = "fmea_aerospace_knowledge"
    embedding_model_name: str = "all-MiniLM-L6-v2"
    
    # Chunking parameters calibrated for technical aerospace standards
    chunk_size: int = 900
    chunk_overlap: int = 180
    min_chunk_size: int = 100
    
    # Retrieval parameters
    default_top_k: int = 5
    similarity_threshold: float = 0.0

    def __post_init__(self) -> None:
        """Default to production core_final store if available and default paths are used."""
        core_final_dir = self.data_dir / "chroma_db_core_final"
        if core_final_dir.exists() and self.chroma_dir == (self.base_dir / "data" / "chroma_db") and self.collection_name == "fmea_aerospace_knowledge":
            self.chroma_dir = core_final_dir
            self.collection_name = "fmea_aerospace_knowledge_core_final"

    def ensure_directories(self) -> None:
        """Create necessary directories if they do not exist."""
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_production_config(cls) -> "RAGConfig":
        """Get the active production RAG configuration pointing to the validated core-final store.
        
        Preserves isolated previous stores for baseline evaluation and ablation:
        - Baseline: data/chroma_db ('fmea_aerospace_knowledge')
        - Phase 5D: data/chroma_db_phase5d_sectioned ('fmea_aerospace_knowledge_sectioned')
        - Phase 5E: data/chroma_db_phase5e ('fmea_aerospace_knowledge_phase5e')
        - Core Final: data/chroma_db_core_final ('fmea_aerospace_knowledge_core_final')
        """
        cfg = cls()
        core_final_dir = cfg.data_dir / "chroma_db_core_final"
        phase5e_dir = cfg.data_dir / "chroma_db_phase5e"
        phase5d_dir = cfg.data_dir / "chroma_db_phase5d_sectioned"
        if core_final_dir.exists():
            cfg.chroma_dir = core_final_dir
            cfg.collection_name = "fmea_aerospace_knowledge_core_final"
        elif phase5e_dir.exists():
            cfg.chroma_dir = phase5e_dir
            cfg.collection_name = "fmea_aerospace_knowledge_phase5e"
        elif phase5d_dir.exists():
            cfg.chroma_dir = phase5d_dir
            cfg.collection_name = "fmea_aerospace_knowledge_sectioned"
        return cfg
