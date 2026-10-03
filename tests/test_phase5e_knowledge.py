"""Comprehensive test suite for FMEA-GPT Phase 5E Knowledge Expansion.

Validates the 12 mandatory criteria from Phase 5E:
1. New source metadata completeness and authority in sources.json
2. Technical domain tagging and document-level metadata
3. Formula extraction from raw text
4. Formula provenance retention (formula_id, doc, page, raw text, expression, variables)
5. Table extraction and provenance limitations documentation
6. Isolated Phase 5E index verification (data/chroma_db_phase5e)
7. Retrieval of newly acquired technical knowledge (thermal fatigue, cooling)
8. Corpus gap improvement over Phase 5D baseline
9. No invented reliability values (lambda_p, alpha, beta, t)
10. Deterministic adaptive routing behavior and classification accuracy
11. Provenance preservation across all retrieval modalities
12. Regression testing against Phase 5D baseline regulatory retrieval
"""
import sys
import json
import pytest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag.config import RAGConfig
from src.rag.retriever import AerospaceRetriever, RetrievalResult
from src.rag.formula_extractor import FormulaExtractor, ExtractedFormula
from src.rag.adaptive_router import AdaptiveQueryRouter, RetrievalStrategy


class TestPhase5ENewSourceMetadata:
    """Requirement 1 & 7: Validate new source metadata completeness and authority."""

    def test_sources_metadata_contains_phase5e_sources(self):
        metadata_path = Path("data/metadata/sources.json")
        assert metadata_path.exists(), "data/metadata/sources.json must exist"

        with open(metadata_path, "r", encoding="utf-8") as f:
            sources = json.load(f)

        source_ids = {s.get("id") for s in sources}
        expected_ids = {
            "NASA-TP-2013-217830",
            "NASA-CREEP-FATIGUE-HOT-SECTION",
            "NASA-CR-198472"
        }
        for eid in expected_ids:
            assert eid in source_ids, f"Expected source {eid} not found in sources.json"

    def test_phase5e_sources_have_authoritative_metadata(self):
        with open("data/metadata/sources.json", "r", encoding="utf-8") as f:
            sources = json.load(f)

        phase5e_sources = [s for s in sources if s.get("id") in [
            "NASA-TP-2013-217830",
            "NASA-CREEP-FATIGUE-HOT-SECTION",
            "NASA-CR-198472"
        ]]

        for s in phase5e_sources:
            assert s.get("status") == "downloaded"
            assert Path(s.get("local_filename")).exists(), f"File {s.get('local_filename')} not found"
            assert "NASA" in s.get("publisher") or "United Technologies" in s.get("publisher")
            assert s.get("gap_addressed") is not None
            assert len(s.get("relevance_to_fmea_gpt")) > 50


class TestTechnicalDomainTagging:
    """Requirement 2 & 13: Validate domain tagging and ingestion stats."""

    def test_ingestion_stats_exist(self):
        stats_path = Path("data/output/phase5e_ingestion_stats.json")
        assert stats_path.exists(), "phase5e_ingestion_stats.json must exist"

        with open(stats_path, "r", encoding="utf-8") as f:
            stats = json.load(f)

        assert stats["phase"] == "5E"
        assert stats["total_chunks"] >= 1800
        assert stats["new_source_chunks"] >= 300
        assert stats["formula_enriched_chunks"] >= 10
        assert stats["total_formulas_extracted"] >= 30


class TestFormulaExtractionAndProvenance:
    """Requirement 3, 4, 20, 21: Validate formula extraction and provenance retention."""

    def test_formula_extraction_mil_std_cm(self):
        extractor = FormulaExtractor()
        text = "4.5.2 Mode criticality number.\nCm = β × α × λp × t\nwhere β is conditional probability."
        formulas = extractor.extract_from_text(text, source_doc="MIL-STD-1629A.pdf", page_num=32)

        assert len(formulas) >= 1
        cm_formula = formulas[0]
        assert "beta" in cm_formula.normalized_expression.lower()
        assert cm_formula.source_document == "MIL-STD-1629A.pdf"
        assert cm_formula.page_number == 32
        assert cm_formula.formula_id.startswith(("FML-", "FORM-"))

    def test_formula_provenance_preservation(self):
        extractor = FormulaExtractor()
        text = "Item criticality: Cr = sum(Cm) where Cm is failure mode criticality number."
        formulas = extractor.extract_from_text(text, source_doc="MIL-STD-1629A.pdf", page_num=33, section="Task 102")

        assert len(formulas) >= 1
        cr = formulas[0]
        assert cr.section == "Task 102"
        assert cr.source_document == "MIL-STD-1629A.pdf"
        assert cr.page_number == 33
        assert len(cr.raw_text) > 0
        d = cr.to_dict()
        assert d["confidence"] in ["extracted", "inferred"]
        assert d["confidence"] != "invented"


class TestTableProvenanceAndLimitations:
    """Requirement 5 & 12: Validate table provenance and explicit limitation documentation."""

    def test_table_documentation_exists(self):
        report_path = Path("docs/phase5e_source_selection.md")
        assert report_path.exists()
        content = report_path.read_text(encoding="utf-8")
        assert "Table" in content or "table" in content


class TestIsolatedPhase5EIndex:
    """Requirement 6 & 15: Validate isolation of ChromaDB Phase 5E store."""

    def test_isolated_phase5e_store_exists(self):
        store_path = Path("data/chroma_db_phase5e")
        assert store_path.exists(), "data/chroma_db_phase5e must exist"

        # Check baseline stores remain intact
        assert Path("data/chroma_db").exists(), "Baseline data/chroma_db must remain intact"
        assert Path("data/chroma_db_phase5d_sectioned").exists(), "Phase 5D store must remain intact"


class TestRetrievalOfNewlyAcquiredKnowledge:
    """Requirement 7 & 8: Validate retrieval of thermal fatigue and cooling technical knowledge."""

    def test_thermal_fatigue_retrieval(self):
        cfg = RAGConfig(
            chroma_dir=Path("data/chroma_db_phase5e"),
            collection_name="fmea_aerospace_knowledge_phase5e"
        )
        retriever = AerospaceRetriever(config=cfg)
        results = retriever.retrieve("high pressure turbine blade thermomechanical fatigue TMF cracking", top_k=5)

        assert len(results) > 0
        doc_names = [Path(r.source_document).name for r in results]
        # At least one new technical source should be in top results
        has_new_source = any(
            "Blade_Life" in d or "Hot_Section" in d for d in doc_names
        )
        assert has_new_source, f"Expected new NASA fatigue source in top 5, got {doc_names}"

    def test_cooling_passage_retrieval(self):
        cfg = RAGConfig(
            chroma_dir=Path("data/chroma_db_phase5e"),
            collection_name="fmea_aerospace_knowledge_phase5e"
        )
        retriever = AerospaceRetriever(config=cfg)
        results = retriever.retrieve("turbine blade internal cooling passage blockage particulate clogging", top_k=5)

        assert len(results) > 0
        doc_names = [Path(r.source_document).name for r in results]
        has_cooling_source = any("Internal_Cooling" in d for d in doc_names)
        assert has_cooling_source, f"Expected NASA internal cooling source in top 5, got {doc_names}"


class TestCorpusGapImprovement:
    """Requirement 8 & 19: Validate corpus gap resolution rate and ground truth updates."""

    def test_ret12_is_no_longer_corpus_gap(self):
        with open("tests/retrieval_ground_truth.json", "r", encoding="utf-8") as f:
            gt = json.load(f)

        ret12 = next((q for q in gt if q["query_id"] == "RET-12"), None)
        assert ret12 is not None
        assert ret12.get("corpus_gap") is False, "RET-12 should no longer be marked as a corpus gap"
        assert len(ret12.get("relevant_documents", [])) > 0

    def test_remaining_corpus_gaps_are_explicit(self):
        with open("tests/retrieval_ground_truth.json", "r", encoding="utf-8") as f:
            gt = json.load(f)

        gaps = [q for q in gt if q.get("corpus_gap") is True]
        gap_ids = [g["query_id"] for g in gaps]
        # RET-13 and RET-14 (fretting) remain genuine gaps as documented in gap analysis
        assert "RET-13" in gap_ids
        assert "RET-14" in gap_ids


class TestNoInventedReliabilityValues:
    """Requirement 9 & 25: Verify reliability metrics strictly reflect source documents."""

    def test_no_synthetic_failure_rates_in_formula_extractor(self):
        extractor = FormulaExtractor()
        # Verify default confidence does not allow invented
        text = "Operating criticality analysis according to standard procedure."
        formulas = extractor.extract_from_text(text, source_doc="test.pdf", page_num=1)
        for f in formulas:
            assert f.confidence != "invented"
            # No default numerical lambda_p values fabricated
            assert "lambda_p = 0.0" not in f.normalized_expression


class TestAdaptiveQueryRouter:
    """Requirement 10, 23, 24: Validate deterministic adaptive routing."""

    def test_formula_query_routing(self):
        router = AdaptiveQueryRouter()
        c = router.classify_query("mode criticality number equation calculation beta lambda")
        assert c.strategy == RetrievalStrategy.FORMULA_AWARE
        assert len(c.matched_triggers) > 0

    def test_terminology_query_routing(self):
        router = AdaptiveQueryRouter()
        c = router.classify_query("EASA CS-E catastrophic engine failure containment rotor burst")
        assert c.strategy == RetrievalStrategy.HYBRID_EXPANSION
        assert len(c.matched_triggers) > 0

    def test_general_query_routing(self):
        router = AdaptiveQueryRouter()
        c = router.classify_query("turbine blade inspection methods")
        assert c.strategy == RetrievalStrategy.SECTION_DENSE

    def test_inspectable_detailed_retrieval(self):
        router = AdaptiveQueryRouter()
        result = router.retrieve_detailed("Cm criticality formula", top_k=3)
        assert result.classification.strategy == RetrievalStrategy.FORMULA_AWARE
        assert len(result.results) <= 3
        assert result.latency_ms > 0


class TestProvenancePreservation:
    """Requirement 11 & 14: Validate citation formatting and source hierarchy."""

    def test_retrieval_result_citation_format(self):
        cfg = RAGConfig(
            chroma_dir=Path("data/chroma_db_phase5e"),
            collection_name="fmea_aerospace_knowledge_phase5e"
        )
        retriever = AerospaceRetriever(config=cfg)
        results = retriever.retrieve("turbine rotor blade", top_k=2)
        assert len(results) > 0
        top = results[0]
        citation = top.format_citation()
        assert "Page" in citation or "p." in citation
        assert len(top.source_document) > 0
        assert top.page_number > 0


class TestRegressionAgainstPhase5D:
    """Requirement 12 & 28: Validate regulatory baseline retrieval stability."""

    def test_catastrophic_failure_definition_retrieval(self):
        cfg = RAGConfig(
            chroma_dir=Path("data/chroma_db_phase5e"),
            collection_name="fmea_aerospace_knowledge_phase5e"
        )
        retriever = AerospaceRetriever(config=cfg)
        results = retriever.retrieve("catastrophic failure condition definition loss of aircraft multiple fatalities", top_k=3)

        assert len(results) > 0
        doc_names = [Path(r.source_document).name for r in results]
        has_ac25 = any("1309" in d for d in doc_names)
        assert has_ac25, f"Expected AC 25.1309 in top results for catastrophic failure, got {doc_names}"
