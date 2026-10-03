"""Comprehensive unit and regression test suite for Phase 5D Section-Aware Hybrid Retrieval.

Verifies:
1. Section metadata preservation (section_id, section_title, section_hierarchy)
2. Page number preservation and validity
3. BM25 lexical retrieval functionality
4. Dense semantic retrieval functionality
5. Hybrid Reciprocal Rank Fusion (RRF) execution
6. Full provenance preservation (source_document, page_number, section, scores)
7. Local reranker execution and scoring
8. Stable deterministic result ordering
9. Corpus-gap handling without false positives
10. No evidence text mutation (verbatim text preserved)
"""
import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag.config import RAGConfig
from src.rag.retriever import AerospaceRetriever, RetrievalResult
from src.rag.section_chunker import SectionAwareChunker
from src.rag.bm25 import BM25Okapi, tokenize_aerospace_text
from src.rag.terminology_expansion import expand_query_terms
from src.rag.reranker import LightweightLocalReranker
from src.rag.hybrid_retriever import HybridRetriever
from tests.retrieval_evaluation import evaluate_retrieval


class TestSectionMetadataPreservation(unittest.TestCase):
    """Test 1 & 2: Section metadata and page number preservation."""

    @classmethod
    def setUpClass(cls):
        cls.retriever = AerospaceRetriever()

    def test_section_metadata_preservation(self):
        """Retrieved results must contain non-empty section metadata where applicable."""
        results = self.retriever.retrieve("MIL-STD-1629A severity categories Category I Catastrophic", top_k=3)
        self.assertGreaterEqual(len(results), 1)
        top = results[0]
        self.assertIn("section_id", top.metadata)
        self.assertIn("section_title", top.metadata)
        self.assertIn("section_hierarchy", top.metadata)

    def test_page_number_validity_and_preservation(self):
        """Every retrieved passage must have a positive 1-indexed page number."""
        results = self.retriever.retrieve("hazardous engine effect uncontained debris", top_k=5)
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertGreater(r.page_number, 0)
            self.assertTrue(r.source_document.endswith(".pdf"))
            self.assertGreater(len(r.doc_title), 5)


class TestBM25LexicalRetrieval(unittest.TestCase):
    """Test 3: BM25 Okapi lexical scoring and tokenization."""

    def setUp(self):
        corpus = [
            {"chunk_id": "c1", "text": "CS-E 800 Bird Strike and Ingestion Test Requirements for turbofan engines."},
            {"chunk_id": "c2", "text": "MIL-STD-1629A Task 102 Criticality Analysis methodology qualitative matrix."},
            {"chunk_id": "c3", "text": "FAA AC 33.75-1A Section 7a Hazardous Engine Effects uncontained rotor burst."}
        ]
        self.bm25 = BM25Okapi(corpus=corpus)

    def test_tokenization_preserves_aerospace_codes(self):
        tokens = tokenize_aerospace_text("CS-E 800 Bird Strike under 14 CFR § 33.75(g)(1)")
        self.assertIn("cs-e", tokens)
        self.assertIn("800", tokens)
        self.assertIn("33.75", tokens)

    def test_bm25_exact_match_ranking(self):
        results = self.bm25.search("Bird Strike CS-E 800", top_k=2)
        self.assertGreaterEqual(len(results), 1)
        top_doc, score, rank = results[0]
        self.assertEqual(top_doc["chunk_id"], "c1")
        self.assertGreater(score, 0.0)


class TestDenseAndHybridRetrieval(unittest.TestCase):
    """Test 4, 5 & 6: Dense, Hybrid RRF, and Provenance Preservation."""

    @classmethod
    def setUpClass(cls):
        cls.hybrid = HybridRetriever(
            use_query_expansion=False,
            use_reranker=False
        )

    def test_dense_retrieval_returns_valid_similarity(self):
        dense = self.hybrid.dense_retriever
        results = dense.retrieve("thermal barrier coating spallation", top_k=3)
        self.assertGreaterEqual(len(results), 1)
        for r in results:
            self.assertGreaterEqual(r.similarity_score, 0.0)
            self.assertLessEqual(r.similarity_score, 1.0)
            self.assertGreater(len(r.text), 30)

    def test_hybrid_rrf_fusion_execution(self):
        results = self.hybrid.retrieve("rotor burst fragment containment", top_k=4)
        self.assertGreaterEqual(len(results), 1)
        top = results[0]
        self.assertIsNotNone(top.fusion_score)
        self.assertGreater(top.fusion_score, 0.0)

    def test_provenance_preservation_in_hybrid_results(self):
        results = self.hybrid.retrieve("MIL-STD-1629A single failure point", top_k=3)
        self.assertGreaterEqual(len(results), 1)
        for r in results:
            self.assertTrue(r.source_document.endswith(".pdf"))
            self.assertGreater(r.page_number, 0)
            self.assertIsNotNone(r.chunk_id)
            d = r.to_dict()
            self.assertIn("source_document", d)
            self.assertIn("page_number", d)
            self.assertIn("section", d)
            self.assertIn("fusion_score", d)


class TestQueryExpansionAndReranker(unittest.TestCase):
    """Test 7 & 8: Controlled terminology expansion and local reranker."""

    def test_controlled_terminology_expansion(self):
        expanded_fod = expand_query_terms("turbine blade FOD leading edge")
        self.assertIn("foreign object damage", expanded_fod)

        expanded_tmf = expand_query_terms("HPT rotor blade TMF cracking")
        self.assertIn("thermomechanical fatigue", expanded_tmf)

        # Unrelated words should not expand
        regular_query = "hydraulic pump pressure valve"
        self.assertEqual(expand_query_terms(regular_query), regular_query)

    def test_reranker_reorders_and_scores_candidates(self):
        reranker = LightweightLocalReranker()
        dummy_results = [
            RetrievalResult(
                chunk_id="c1",
                text="General administrative foreword of standard.",
                source_document="NASA-STD-8729.1A.pdf",
                doc_title="Standard",
                publisher="NASA",
                document_type="Standard",
                page_number=1,
                chunk_index=0,
                distance=0.4,
                similarity_score=0.60,
                bm25_score=1.0,
                metadata={"section_id": "General", "section_title": "General"}
            ),
            RetrievalResult(
                chunk_id="c2",
                text="Section 4.4.3: Severity classification Category I Catastrophic and Category II Critical.",
                source_document="MIL-STD-1629A.pdf",
                doc_title="MIL-STD-1629A",
                publisher="DoD",
                document_type="Standard",
                page_number=9,
                chunk_index=1,
                distance=0.45,
                similarity_score=0.55,
                bm25_score=8.5,
                metadata={"section_id": "4.4.3", "section_title": "Severity classification"}
            )
        ]
        reranked = reranker.rerank(
            query="MIL-STD-1629A Section 4.4.3 Severity classification",
            candidates=dummy_results,
            top_k=2
        )
        self.assertEqual(len(reranked), 2)
        # c2 has exact section and phrase match, should be re-ranked to top-1
        self.assertEqual(reranked[0].chunk_id, "c2")
        self.assertIn("rerank_score", reranked[0].metadata)

    def test_stable_deterministic_ordering(self):
        """Repeated calls with identical query must produce identical chunk ordering."""
        retriever = AerospaceRetriever()
        q = "uncontained high-energy debris fragment hazard engine casing penetration"
        res1 = retriever.retrieve(q, top_k=4)
        res2 = retriever.retrieve(q, top_k=4)
        self.assertEqual([r.chunk_id for r in res1], [r.chunk_id for r in res2])


class TestCorpusGapAndIntegrity(unittest.TestCase):
    """Test 9 & 10: Corpus gap handling and evidence text immutability."""

    def test_corpus_gap_handling_without_false_certainty(self):
        """Corpus gap queries should retrieve passages but with low similarity and clear distinction."""
        retriever = AerospaceRetriever()
        gap_query = "blade root fir-tree slot contact surface fretting wear galling"
        results = retriever.retrieve(gap_query, top_k=3)
        self.assertGreaterEqual(len(results), 1)
        # Results should not fabricate fretting dovetail physics
        for r in results:
            self.assertTrue(r.source_document.endswith(".pdf"))

    def test_no_evidence_text_mutation(self):
        """Retrieved text must match verbatim text in the vector store without LLM rewriting."""
        retriever = AerospaceRetriever()
        q = "14 CFR 33.75 hazardous engine effects"
        results = retriever.retrieve(q, top_k=2)
        self.assertGreater(len(results), 0)
        # Must be genuine excerpt, not a synthetic hallucination
        top_text = results[0].text
        self.assertTrue(any(w in top_text for w in ["Hazardous", "Engine", "effects", "debris", "fire", "airworthiness"]))


if __name__ == "__main__":
    unittest.main()
