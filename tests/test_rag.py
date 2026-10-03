"""Comprehensive unit and integration tests for FMEA-GPT RAG pipeline."""
import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag.config import RAGConfig
from src.rag.document_loader import DocumentLoader, PageContent
from src.rag.chunker import AerospaceChunker, TextChunk
from src.rag.retriever import RetrievalResult, AerospaceRetriever
from src.rag.vector_store import ChromaVectorStore


class TestRAGConfig(unittest.TestCase):
    """Test RAG configuration defaults and paths."""

    def test_config_paths(self):
        config = RAGConfig()
        self.assertTrue(config.data_dir.name == "data")
        self.assertTrue(config.raw_dir.name == "raw")
        self.assertIn(config.chroma_dir.name, ["chroma_db", "chroma_db_core_final"])
        self.assertIn(config.collection_name, ["fmea_aerospace_knowledge", "fmea_aerospace_knowledge_core_final"])
        self.assertGreater(config.chunk_size, config.chunk_overlap)
        self.assertEqual(config.chunk_overlap, 180)


class TestDocumentLoader(unittest.TestCase):
    """Test text cleaning and sources metadata loading."""

    def setUp(self):
        self.config = RAGConfig()
        self.loader = DocumentLoader(self.config.raw_dir, self.config.metadata_file)

    def test_clean_page_text_hyphens(self):
        raw = "The high-pressure turbine compo-\nnent failed due to thermal fatigue."
        cleaned = self.loader.clean_page_text(raw)
        self.assertIn("component", cleaned)
        self.assertNotIn("compo-\nnent", cleaned)

    def test_clean_page_text_whitespace(self):
        raw = "MIL-STD-1629A   defines    Task 101.\n\n\n\nTask 102 follows."
        cleaned = self.loader.clean_page_text(raw)
        self.assertIn("Task 101.\n\nTask 102", cleaned)
        self.assertNotIn("    ", cleaned)

    def test_sources_metadata_loaded(self):
        self.assertGreater(len(self.loader.sources_metadata), 0)
        # Check for key standard
        self.assertIn("MIL-STD-1629A.pdf", self.loader.sources_metadata)
        entry = self.loader.sources_metadata["MIL-STD-1629A.pdf"]
        self.assertEqual(entry["id"], "MIL-STD-1629A")
        self.assertIn("DoD", entry["publisher"])


class TestAerospaceChunker(unittest.TestCase):
    """Test chunking logic, header preservation, and overlap."""

    def setUp(self):
        self.chunker = AerospaceChunker(chunk_size=400, chunk_overlap=100, min_chunk_size=50)

    def test_single_small_page(self):
        page = PageContent(
            doc_id="TEST-DOC",
            source_file="test_doc.pdf",
            doc_title="Test Aerospace Specification",
            publisher="FAA",
            document_type="Advisory Circular",
            page_number=1,
            total_pages=5,
            text="This is a short specification clause defining engine safety containment."
        )
        chunks = self.chunker.chunk_page(page)
        self.assertEqual(len(chunks), 1)
        chunk = chunks[0]
        self.assertTrue(chunk.chunk_id.startswith("TEST-DOC_p1_c0"))
        self.assertIn("[Test Aerospace Specification | Page 1]", chunk.text)
        self.assertIn("engine safety containment", chunk.text)

    def test_multi_paragraph_chunking_with_overlap(self):
        long_text = (
            "Section 1.1: High Pressure Turbine Blade Failure Modes.\n\n"
            "Thermal fatigue cracks typically initiate at the leading edge cooling holes "
            "where thermal gradients during takeoff power transients are most severe. "
            "Microstructural degradation leads to creep elongation under centrifugal stress.\n\n"
            "Section 1.2: Maintenance Action Recommendations.\n\n"
            "Borescope inspection of the high-pressure turbine stage 1 blades must be conducted "
            "at intervals not exceeding 500 flight cycles per FAA AC 33.75-1A guidelines. "
            "Blades exhibiting cracks exceeding 0.05 inches must be replaced immediately."
        )
        page = PageContent(
            doc_id="CFM56-MANUAL",
            source_file="cfm56_manual.pdf",
            doc_title="CFM56 Turbine Blade Maintenance",
            publisher="CFM / FAA",
            document_type="Engine Manual",
            page_number=42,
            total_pages=100,
            text=long_text
        )
        chunks = self.chunker.chunk_page(page)
        self.assertGreaterEqual(len(chunks), 2)
        for c in chunks:
            self.assertEqual(c.page_number, 42)
            self.assertIn("[CFM56 Turbine Blade Maintenance | Page 42]", c.text)


class TestRetrievalResult(unittest.TestCase):
    """Test retrieval result formatting and citation generation."""

    def test_citation_formatting(self):
        result = RetrievalResult(
            chunk_id="MIL-STD-1629A_p12_c1",
            text="Severity Category I - Catastrophic: A failure mode which may cause death.",
            source_document="MIL-STD-1629A.pdf",
            doc_title="Procedures for Performing a Failure Mode, Effects and Criticality Analysis",
            publisher="U.S. DoD",
            document_type="Military Standard",
            page_number=12,
            chunk_index=1,
            distance=0.15,
            similarity_score=0.85
        )
        citation = result.format_citation()
        self.assertIn("Page 12", citation)
        self.assertIn("U.S. DoD", citation)
        self.assertIn("85.0%", citation)
        
        d = result.to_dict()
        self.assertEqual(d["page_number"], 12)
        self.assertEqual(d["similarity_score"], 0.85)


class TestVectorStoreAndRetrieverIntegration(unittest.TestCase):
    """Integration test verifying end-to-end embedding, ChromaDB persistence, and semantic retrieval."""

    @classmethod
    def setUpClass(cls):
        cls.config = RAGConfig()
        cls.retriever = AerospaceRetriever(config=cls.config)

    def test_semantic_retrieval_returns_provenance(self):
        query = "MIL-STD-1629A failure mode effects severity categories"
        results = self.retriever.retrieve(query=query, top_k=3)
        self.assertGreaterEqual(len(results), 1)
        
        top = results[0]
        self.assertIsInstance(top, RetrievalResult)
        self.assertTrue(top.source_document.endswith(".pdf"))
        self.assertGreater(top.page_number, 0)
        self.assertGreater(top.similarity_score, 0.0)
        self.assertLessEqual(top.similarity_score, 1.0)
        self.assertGreater(len(top.text), 20)

    def test_publisher_filtering(self):
        query = "engine safety analysis containment"
        results = self.retriever.retrieve(query=query, top_k=3, publisher="Federal Aviation Administration (FAA)")
        for res in results:
            self.assertEqual(res.publisher, "Federal Aviation Administration (FAA)")


if __name__ == "__main__":
    unittest.main()

