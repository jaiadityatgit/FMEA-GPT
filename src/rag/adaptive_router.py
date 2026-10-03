"""Deterministic adaptive query router for FMEA-GPT Phase 5E.

Routes incoming queries to the optimal retrieval strategy:
1. FORMULA / MATHEMATICAL -> Formula-aware retrieval (MIL-STD-1629A equations, reliability calculations)
2. TERMINOLOGY / CROSS-STANDARD -> Hybrid Dense + BM25 with Controlled Terminology Expansion
3. GENERAL TECHNICAL FACT -> Section-Aware Dense Retrieval (default)

Design principles:
- 100% deterministic and inspectable (no black-box LLM router)
- Transparent classification explanations and matched triggers
- Fully backward compatible with the AerospaceRetriever interface
"""
import re
import time
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from .config import RAGConfig
from .retriever import AerospaceRetriever, RetrievalResult
from .hybrid_retriever import HybridRetriever


class RetrievalStrategy(str, Enum):
    SECTION_DENSE = "section_aware_dense"
    HYBRID_EXPANSION = "hybrid_terminology_expansion"
    FORMULA_AWARE = "formula_aware_retrieval"


@dataclass
class QueryClassification:
    """Detailed query classification decision record."""
    query: str
    strategy: RetrievalStrategy
    matched_triggers: List[str]
    rationale: str


@dataclass
class AdaptiveRoutingResult:
    """Complete inspectable retrieval output including routing metadata."""
    query: str
    classification: QueryClassification
    results: List[RetrievalResult]
    latency_ms: float


class AdaptiveQueryRouter:
    """Inspectable, rule-driven adaptive query router for aerospace technical retrieval."""

    # Regex indicators for mathematical & equation queries
    FORMULA_PATTERNS = [
        r"\b(equation|formula|calculate|calculation|calculated)\b",
        r"\b(mode criticality number|item criticality number)\b",
        r"\b[Cc][mr]\b",
        r"\b(lambda|lambda_p|failure rate|hazard rate)\b",
        r"\b(beta|alpha|operating time|mission loss probability)\b",
        r"\b(weibull|summation|formulaic|quantitative matrix)\b",
        r"[βλα]"
    ]

    # Regex indicators for terminology-heavy, cross-standard, and complex interaction queries
    TERMINOLOGY_PATTERNS = [
        r"\b(ata\s*\d+|cs-e|ac\s*25|ac\s*33|mil-std|task\s*10[123]|amc)\b",
        r"\b(cil|sfp|single point failure|critical items list)\b",
        r"\b(catastrophic|hazardous|major|marginal|minor)\b",
        r"\b(containment|rotor burst|uncontained debris)\b",
        r"\b(fretting|dovetail|fir-tree|galling|micro-motion)\b",
        r"\b(tmf|lcf|hcf|creep-fatigue|thermomechanical fatigue)\b",
        r"\b(cooling passage|film cooling|serpentine|heat transfer loss)\b",
        r"\b(spallation|thermal barrier coating|tbc)\b",
        r"\b(boroscope|eddy current|ultrasonic|ndi|c-mapss)\b"
    ]

    def __init__(
        self,
        config: Optional[RAGConfig] = None,
        chroma_dir: Optional[Path] = None,
        collection_name: Optional[str] = None
    ):
        self.config = config or RAGConfig.get_production_config()
        if chroma_dir:
            self.config.chroma_dir = Path(chroma_dir)
        if collection_name:
            self.config.collection_name = collection_name

        # 1. Section-aware Dense Retriever
        self.dense_retriever = AerospaceRetriever(config=self.config)

        # 2. Hybrid Retriever with Terminology Expansion
        self.hybrid_expansion_retriever = HybridRetriever(
            chroma_dir=self.config.chroma_dir,
            collection_name=self.config.collection_name,
            use_query_expansion=True,
            use_reranker=False
        )

        # 3. Hybrid Retriever with BM25 (ideal for formulas and exact notation)
        self.hybrid_bm25_retriever = HybridRetriever(
            chroma_dir=self.config.chroma_dir,
            collection_name=self.config.collection_name,
            use_query_expansion=False,
            use_reranker=False
        )

    def classify_query(self, query: str) -> QueryClassification:
        """Classify query into one of three deterministic routing strategies."""
        query_lower = query.lower()

        # Check Formula Patterns first
        matched_formula = []
        for pat in self.FORMULA_PATTERNS:
            found = re.findall(pat, query_lower, re.IGNORECASE)
            if found:
                matched_formula.extend(found)

        if matched_formula:
            return QueryClassification(
                query=query,
                strategy=RetrievalStrategy.FORMULA_AWARE,
                matched_triggers=list(set(str(f) for f in matched_formula)),
                rationale="Query contains explicit mathematical notation, formula keywords, or reliability calculation parameters."
            )

        # Check Terminology / Cross-Standard Patterns
        matched_terminology = []
        for pat in self.TERMINOLOGY_PATTERNS:
            found = re.findall(pat, query_lower, re.IGNORECASE)
            if found:
                matched_terminology.extend(found)

        if matched_terminology:
            return QueryClassification(
                query=query,
                strategy=RetrievalStrategy.HYBRID_EXPANSION,
                matched_triggers=list(set(str(t) for t in matched_terminology)),
                rationale="Query contains domain acronyms, standard cross-references, or complex interaction mechanisms."
            )

        # Default: Section-Aware Dense
        return QueryClassification(
            query=query,
            strategy=RetrievalStrategy.SECTION_DENSE,
            matched_triggers=[],
            rationale="Short technical query or general engineering mechanism suitable for dense semantic similarity."
        )

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """Execute adaptive retrieval compliant with the AerospaceRetriever interface."""
        classification = self.classify_query(query)

        if classification.strategy == RetrievalStrategy.FORMULA_AWARE:
            # Hybrid BM25 + Dense is superior for exact formula notation & symbols
            results = self.hybrid_bm25_retriever.retrieve(query, top_k=top_k)
        elif classification.strategy == RetrievalStrategy.HYBRID_EXPANSION:
            results = self.hybrid_expansion_retriever.retrieve(query, top_k=top_k)
        else:
            results = self.dense_retriever.retrieve(query, top_k=top_k)

        return results

    def retrieve_detailed(self, query: str, top_k: int = 5) -> AdaptiveRoutingResult:
        """Execute retrieval and return full routing diagnostic metadata."""
        t0 = time.perf_counter()
        classification = self.classify_query(query)
        results = self.retrieve(query, top_k=top_k)
        t1 = time.perf_counter()

        return AdaptiveRoutingResult(
            query=query,
            classification=classification,
            results=results,
            latency_ms=round((t1 - t0) * 1000.0, 2)
        )
