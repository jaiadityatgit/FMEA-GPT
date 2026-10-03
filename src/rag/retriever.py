"""Semantic retrieval engine for FMEA-GPT aerospace RAG."""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .config import RAGConfig
from .vector_store import ChromaVectorStore


@dataclass
class RetrievalResult:
    """Represents a single retrieved passage with source provenance and relevance score."""
    chunk_id: str
    text: str
    source_document: str
    doc_title: str
    publisher: str
    document_type: str
    page_number: int
    chunk_index: int
    distance: float
    similarity_score: float
    section: Optional[str] = ""
    dense_score: Optional[float] = None
    bm25_score: Optional[float] = None
    fusion_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "source_document": self.source_document,
            "doc_title": self.doc_title,
            "publisher": self.publisher,
            "document_type": self.document_type,
            "page_number": self.page_number,
            "chunk_index": self.chunk_index,
            "section": self.section or self.metadata.get("section_id", ""),
            "distance": round(self.distance, 4),
            "similarity_score": round(self.similarity_score, 4),
            "similarity_percentage": f"{self.similarity_score * 100:.1f}%",
            "dense_score": round(self.dense_score, 4) if self.dense_score is not None else None,
            "bm25_score": round(self.bm25_score, 4) if self.bm25_score is not None else None,
            "fusion_score": round(self.fusion_score, 4) if self.fusion_score is not None else None,
            "metadata": self.metadata
        }

    def format_citation(self) -> str:
        """Returns a formatted human-readable citation string."""
        return f"{self.doc_title} ({self.publisher}) - File: {self.source_document}, Page {self.page_number} [Similarity: {self.similarity_score*100:.1f}%]"


class AerospaceRetriever:
    """Performs semantic retrieval against the local ChromaDB vector store."""

    def __init__(self, vector_store: Optional[ChromaVectorStore] = None, config: Optional[RAGConfig] = None):
        if config is None:
            config = RAGConfig.get_production_config()
        self.config = config
        self.vector_store = vector_store or ChromaVectorStore(self.config)

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        doc_id: Optional[str] = None,
        publisher: Optional[str] = None
    ) -> List[RetrievalResult]:
        """Execute semantic search and return ranked passages with citations."""
        k = top_k or self.config.default_top_k
        query = query.strip()
        if not query:
            return []

        # Construct optional metadata filter
        where_filter = None
        if doc_id and publisher:
            where_filter = {"$and": [{"doc_id": doc_id}, {"publisher": publisher}]}
        elif doc_id:
            where_filter = {"doc_id": doc_id}
        elif publisher:
            where_filter = {"publisher": publisher}

        raw_results = self.vector_store.query(
            query_text=query,
            top_k=k,
            where=where_filter
        )

        retrieval_results: List[RetrievalResult] = []
        
        ids = raw_results.get("ids", [[]])[0]
        documents = raw_results.get("documents", [[]])[0]
        metadatas = raw_results.get("metadatas", [[]])[0]
        distances = raw_results.get("distances", [[]])[0]

        for i in range(len(ids)):
            dist = float(distances[i]) if i < len(distances) else 1.0
            # For cosine distance: distance is in [0, 2], where 0 is identical.
            # Similarity score = 1 - distance (clamped to [0, 1])
            similarity = max(0.0, min(1.0, 1.0 - dist))
            
            meta = metadatas[i] if i < len(metadatas) else {}
            chunk_text = documents[i] if i < len(documents) else ""

            sec_id = str(meta.get("section_id", ""))
            sec_title = str(meta.get("section_title", ""))
            sec_str = f"{sec_id} {sec_title}".strip() if sec_id and sec_id != "General" else ""

            retrieval_results.append(RetrievalResult(
                chunk_id=ids[i],
                text=chunk_text,
                source_document=meta.get("source_file", "unknown"),
                doc_title=meta.get("doc_title", "Unknown Title"),
                publisher=meta.get("publisher", "Unknown Publisher"),
                document_type=meta.get("document_type", "Aerospace Document"),
                page_number=int(meta.get("page_number", 0)),
                chunk_index=int(meta.get("chunk_index", 0)),
                distance=dist,
                similarity_score=similarity,
                section=sec_str,
                dense_score=similarity,
                metadata=meta
            ))

        return retrieval_results
