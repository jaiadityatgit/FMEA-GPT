"""Hybrid dense + lexical retrieval engine for FMEA-GPT Phase 5D.

Combines:
1. Dense Semantic Retrieval (all-MiniLM-L6-v2 ONNX via ChromaDB)
2. BM25 Lexical Retrieval (Okapi BM25 on section-aware chunks)
3. Reciprocal Rank Fusion (RRF) with configurable rank constant k=60
4. Optional Controlled Technical Terminology Expansion
5. Optional Lightweight Local Reranking
Preserves complete provenance: source_document, page_number, section, dense_score, bm25_score, fusion_score.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from .config import RAGConfig
from .retriever import RetrievalResult, AerospaceRetriever
from .vector_store import ChromaVectorStore
from .bm25 import BM25Okapi
from .terminology_expansion import expand_query_terms
from .reranker import LightweightLocalReranker


class HybridRetriever:
    """Production hybrid retriever fusing dense semantic and BM25 lexical search."""

    def __init__(
        self,
        config: Optional[RAGConfig] = None,
        vector_store: Optional[ChromaVectorStore] = None,
        chroma_dir: Optional[Path] = None,
        collection_name: Optional[str] = None,
        rrf_k: int = 60,
        weight_dense: float = 1.0,
        weight_bm25: float = 1.0,
        use_query_expansion: bool = False,
        use_reranker: bool = False,
        reranker: Optional[LightweightLocalReranker] = None
    ):
        self.config = config or RAGConfig.get_production_config()
        if chroma_dir:
            self.config.chroma_dir = Path(chroma_dir)
        if collection_name:
            self.config.collection_name = collection_name

        self.vector_store = vector_store or ChromaVectorStore(self.config)
        self.dense_retriever = AerospaceRetriever(vector_store=self.vector_store, config=self.config)

        self.rrf_k = rrf_k
        self.weight_dense = weight_dense
        self.weight_bm25 = weight_bm25
        self.use_query_expansion = use_query_expansion
        self.use_reranker = use_reranker
        self.reranker = reranker or (LightweightLocalReranker() if use_reranker else None)

        # Initialize BM25 index over vector store documents
        self.bm25_index: Optional[BM25Okapi] = None
        self.chunk_lookup: Dict[str, Dict[str, Any]] = {}
        self._init_bm25()

    def _init_bm25(self) -> None:
        """Load chunks from ChromaDB collection and initialize BM25Okapi index."""
        try:
            col = self.vector_store.collection
            data = col.get(include=["documents", "metadatas"])
            corpus = []
            
            ids = data.get("ids", [])
            docs = data.get("documents", [])
            metas = data.get("metadatas", [])
            
            for cid, text, meta in zip(ids, docs, metas):
                doc_dict = {
                    "chunk_id": cid,
                    "text": text,
                    "metadata": meta or {}
                }
                corpus.append(doc_dict)
                self.chunk_lookup[cid] = doc_dict

            self.bm25_index = BM25Okapi(corpus=corpus)
        except Exception as e:
            print(f"Warning: Failed to initialize BM25 index: {e}")
            self.bm25_index = None

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        doc_id: Optional[str] = None,
        publisher: Optional[str] = None
    ) -> List[RetrievalResult]:
        """Execute hybrid search with dense + BM25 fusion and optional reranking."""
        k = top_k or self.config.default_top_k
        query = query.strip()
        if not query:
            return []

        # 1. Optional Query Expansion
        search_query = query
        if self.use_query_expansion:
            search_query = expand_query_terms(query)

        # Candidate pool size for fusion
        candidate_pool_size = max(20, k * 4)

        # 2. Dense Semantic Search
        dense_results = self.dense_retriever.retrieve(
            query=search_query,
            top_k=candidate_pool_size,
            doc_id=doc_id,
            publisher=publisher
        )

        # Map dense ranks
        dense_rank_map: Dict[str, Tuple[int, RetrievalResult]] = {}
        for rank, res in enumerate(dense_results, start=1):
            dense_rank_map[res.chunk_id] = (rank, res)

        # 3. BM25 Lexical Search
        bm25_rank_map: Dict[str, Tuple[int, Dict[str, Any], float]] = {}
        if self.bm25_index:
            bm25_results = self.bm25_index.search(search_query, top_k=candidate_pool_size)
            for rank, (doc_dict, score, _) in enumerate(bm25_results, start=1):
                bm25_rank_map[doc_dict["chunk_id"]] = (rank, doc_dict, score)

        # 4. Reciprocal Rank Fusion (RRF)
        all_chunk_ids = set(dense_rank_map.keys()) | set(bm25_rank_map.keys())
        fused_scores: List[Tuple[str, float, Optional[float], Optional[float]]] = []

        for cid in all_chunk_ids:
            score = 0.0
            dense_score = None
            bm25_score = None

            if cid in dense_rank_map:
                dense_rank, d_res = dense_rank_map[cid]
                score += self.weight_dense / (self.rrf_k + dense_rank)
                dense_score = d_res.similarity_score

            if cid in bm25_rank_map:
                bm25_rank, _, b_score = bm25_rank_map[cid]
                score += self.weight_bm25 / (self.rrf_k + bm25_rank)
                bm25_score = b_score

            fused_scores.append((cid, score, dense_score, bm25_score))

        # Sort by RRF score descending
        fused_scores.sort(key=lambda x: x[1], reverse=True)

        # 5. Build candidate RetrievalResult objects
        fused_candidates: List[RetrievalResult] = []
        for cid, rrf_score, d_score, b_score in fused_scores[:candidate_pool_size]:
            # Retrieve or build RetrievalResult
            if cid in dense_rank_map:
                res = dense_rank_map[cid][1]
            else:
                doc_dict = self.chunk_lookup.get(cid, {})
                meta = doc_dict.get("metadata", {})
                res = RetrievalResult(
                    chunk_id=cid,
                    text=doc_dict.get("text", ""),
                    source_document=meta.get("source_file", "unknown.pdf"),
                    doc_title=meta.get("doc_title", "Unknown"),
                    publisher=meta.get("publisher", "Unknown"),
                    document_type=meta.get("document_type", "Standard"),
                    page_number=int(meta.get("page_number", 1)),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    distance=0.5,
                    similarity_score=0.5,
                    metadata=meta
                )

            # Attach scores & section info
            sec_id = str(res.metadata.get("section_id", ""))
            sec_title = str(res.metadata.get("section_title", ""))
            res.section = f"{sec_id} {sec_title}".strip() if sec_id != "General" else ""
            res.dense_score = d_score
            res.bm25_score = b_score
            res.fusion_score = rrf_score
            
            # Map RRF score into normalized similarity score for downstream consumer consistency
            res.similarity_score = min(1.0, rrf_score * (self.rrf_k / 2.0))
            res.distance = max(0.0, 1.0 - res.similarity_score)
            fused_candidates.append(res)

        # 6. Optional Local Reranker
        if self.use_reranker and self.reranker:
            return self.reranker.rerank(query=query, candidates=fused_candidates[:max(k * 2, 10)], top_k=k)

        return fused_candidates[:k]
