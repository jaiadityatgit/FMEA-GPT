"""Lightweight local reranker module for FMEA-GPT Phase 5D.

Operates locally and deterministically on top-N candidate passages from hybrid retrieval:
- Evaluates lexical and semantic consensus
- Rewards exact regulatory requirement and section title matches
- Applies query term density and coverage bonuses
- Re-scores and re-ranks top-N candidates to produce final top-K
"""
import re
from typing import List, Dict, Any, Tuple, Optional
from .retriever import RetrievalResult


class LightweightLocalReranker:
    """Fast, local CPU reranker for re-scoring top-N candidate passages."""

    def __init__(
        self,
        weight_dense: float = 0.40,
        weight_bm25: float = 0.35,
        weight_phrase: float = 0.15,
        weight_section: float = 0.10
    ):
        self.weight_dense = weight_dense
        self.weight_bm25 = weight_bm25
        self.weight_phrase = weight_phrase
        self.weight_section = weight_section

    def _extract_phrases(self, query: str) -> List[str]:
        """Extract multi-word key technical n-grams (2-3 words) from query."""
        words = re.findall(r'[A-Za-z0-9]+(?:[-.][A-Za-z0-9]+)*', query)
        phrases = []
        # Add 2-word phrases
        for i in range(len(words) - 1):
            p2 = f"{words[i]} {words[i+1]}".lower()
            if len(p2) > 5:
                phrases.append(p2)
        # Add 3-word phrases
        for i in range(len(words) - 2):
            p3 = f"{words[i]} {words[i+1]} {words[i+2]}".lower()
            if len(p3) > 8:
                phrases.append(p3)
        return phrases

    def _compute_phrase_score(self, query: str, text: str) -> float:
        """Compute exact multi-word phrase matching score in text."""
        phrases = self._extract_phrases(query)
        if not phrases:
            return 0.0
        text_lower = text.lower()
        matched = sum(1 for p in phrases if p in text_lower)
        return min(1.0, matched / len(phrases))

    def _compute_section_score(self, query: str, metadata: Dict[str, Any]) -> float:
        """Check if section ID or title in metadata matches query intent."""
        sec_id = str(metadata.get("section_id", "")).lower()
        sec_title = str(metadata.get("section_title", "")).lower()
        q_lower = query.lower()
        
        score = 0.0
        if sec_id and sec_id != "general" and sec_id in q_lower:
            score += 0.6
        if sec_title and sec_title != "general":
            sec_words = [w for w in sec_title.split() if len(w) > 3]
            matched_words = [w for w in sec_words if w in q_lower]
            if matched_words:
                score += 0.4 * (len(matched_words) / len(sec_words))
        return min(1.0, score)

    def rerank(
        self,
        query: str,
        candidates: List[RetrievalResult],
        top_k: int = 5
    ) -> List[RetrievalResult]:
        """Re-rank candidate passages using hybrid feature re-scoring.
        
        Args:
            query: The search query.
            candidates: List of RetrievalResult objects from dense or hybrid retrieval.
            top_k: Number of final results to return.
            
        Returns:
            Re-ranked list of RetrievalResult objects with updated similarity_score and metadata.
        """
        if not candidates:
            return []

        # Find max BM25 score for normalization
        max_bm25 = max((getattr(c, "bm25_score", 0.0) or 0.0) for c in candidates)
        if max_bm25 <= 0.0:
            max_bm25 = 1.0

        scored_candidates: List[Tuple[RetrievalResult, float]] = []

        for c in candidates:
            dense_norm = c.similarity_score  # already in [0, 1]
            raw_bm25 = getattr(c, "bm25_score", 0.0) or 0.0
            bm25_norm = min(1.0, raw_bm25 / max_bm25) if max_bm25 > 0 else 0.0
            phrase_score = self._compute_phrase_score(query, c.text)
            section_score = self._compute_section_score(query, c.metadata)

            rerank_score = (
                self.weight_dense * dense_norm +
                self.weight_bm25 * bm25_norm +
                self.weight_phrase * phrase_score +
                self.weight_section * section_score
            )

            # Record reranker diagnostics in metadata
            c.metadata["rerank_score"] = round(rerank_score, 4)
            c.metadata["phrase_score"] = round(phrase_score, 3)
            c.metadata["section_score"] = round(section_score, 3)
            scored_candidates.append((c, rerank_score))

        # Sort descending by re-rank score
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        reranked_results: List[RetrievalResult] = []
        for rank, (cand, score) in enumerate(scored_candidates[:top_k]):
            cand.similarity_score = round(score, 4)
            cand.distance = round(1.0 - score, 4)
            cand.metadata["final_rank"] = rank + 1
            reranked_results.append(cand)

        return reranked_results
