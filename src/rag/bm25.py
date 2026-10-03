"""Lightweight local BM25 Okapi retrieval engine for FMEA-GPT Phase 5D.

Zero external heavy dependencies. Designed specifically for technical aerospace documents:
- Preserves regulatory section designations (e.g. '33.75', '1629A', 'CS-E', '8729.1A')
- Preserves technical acronyms (FOD, TMF, HCF, LCF, CIL, SFP, EGT, FADEC, NDT)
- Preserves hyphenated metallurgical compounds ('high-pressure', 'fir-tree', 'stress-rupture')
- Implements standard Robertson-Zaragoza BM25 Okapi scoring with length normalization
"""
import math
import re
from typing import List, Dict, Any, Tuple, Optional


def tokenize_aerospace_text(text: str) -> List[str]:
    """Tokenize technical aerospace text into normalized lexical terms.
    
    Preserves numbers with decimals (e.g., 33.75, 4.4.3), hyphenated compounds, and alphanumeric codes.
    """
    if not text:
        return []
    
    # Lowercase
    t = text.lower()
    
    # Replace non-standard punctuation but preserve hyphens and decimals within words
    tokens = re.findall(r'[a-z0-9]+(?:[-.][a-z0-9]+)*', t)
    
    # Filter very short non-informative tokens (single chars that aren't numbers/letters of interest)
    clean_tokens = []
    for tok in tokens:
        # Strip trailing dots or hyphens
        tok = tok.strip(".-")
        if len(tok) >= 2 or tok.isdigit():
            clean_tokens.append(tok)
            
    return clean_tokens


class BM25Okapi:
    """Okapi BM25 implementation for discrete text passages."""

    def __init__(
        self,
        corpus: List[Dict[str, Any]],
        k1: float = 1.5,
        b: float = 0.75
    ):
        """Initialize BM25 index over a corpus of documents/chunks.
        
        Args:
            corpus: List of dicts, each with at least 'chunk_id' and 'text'.
            k1: Term frequency saturation parameter (default: 1.5).
            b: Document length normalization parameter (default: 0.75).
        """
        self.k1 = k1
        self.b = b
        self.corpus = corpus
        self.corpus_size = len(corpus)
        
        self.doc_tokens: List[List[str]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.df: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        
        self._build_index()

    def _build_index(self) -> None:
        """Tokenize corpus and compute document frequencies & IDF."""
        total_len = 0
        for doc in self.corpus:
            text = doc.get("text", "")
            tokens = tokenize_aerospace_text(text)
            self.doc_tokens.append(tokens)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_len += doc_len
            
            # Document frequency
            unique_tokens = set(tokens)
            for tok in unique_tokens:
                self.df[tok] = self.df.get(tok, 0) + 1

        self.avg_doc_len = total_len / self.corpus_size if self.corpus_size > 0 else 1.0

        # Compute Robertson-Spärck Jones IDF
        for tok, freq in self.df.items():
            # Standard Lucene/BM25 Okapi IDF formula with smoothing
            self.idf[tok] = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def get_scores(self, query: str) -> List[float]:
        """Compute BM25 scores for a query across all documents."""
        q_tokens = tokenize_aerospace_text(query)
        scores = [0.0] * self.corpus_size
        if not q_tokens or self.corpus_size == 0:
            return scores

        for q_tok in q_tokens:
            if q_tok not in self.idf:
                continue
            idf_val = self.idf[q_tok]
            
            for doc_idx, doc_tokens in enumerate(self.doc_tokens):
                # Count term frequency in this document
                tf = doc_tokens.count(q_tok)
                if tf == 0:
                    continue
                
                doc_len = self.doc_lengths[doc_idx]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                scores[doc_idx] += idf_val * (numerator / denominator)

        return scores

    def search(self, query: str, top_k: int = 10) -> List[Tuple[Dict[str, Any], float, int]]:
        """Search corpus and return ranked results.
        
        Returns:
            List of (document_dict, bm25_score, rank_1_indexed)
        """
        scores = self.get_scores(query)
        indexed_scores = [(idx, s) for idx, s in enumerate(scores) if s > 0.0]
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for rank, (doc_idx, score) in enumerate(indexed_scores[:top_k], start=1):
            results.append((self.corpus[doc_idx], score, rank))
        return results
