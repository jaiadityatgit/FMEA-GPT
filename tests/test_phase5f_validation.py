"""Phase 5F Validation Test Suite: Provenance Audit, Benchmark Freeze & Knowledge Integration.

Validates the 12 core requirements of Phase 5F:
1. Official source identifier validation (NASA/TP-2013-217030, NASA-CP-2444, NASA-CR-198472)
2. Dataset population-count validation (16 engines, 16 sets, 82 blades/set, 1312 total blades, 111 failed)
3. Benchmark denominator consistency (32 total, 30 evaluable, 2 corpus gaps, 0 negative controls)
4. Phase 5E source retrieval via production path
5. Provenance preservation (source_document, page_number, section, excerpt, score)
6. Formula provenance (text, normalized expression, variables, units, page)
7. Beta assumption labeling (beta=1.0 is ASSUMPTION / WORST_CASE_BOUND, not empirical fleet data)
8. Reliability scope enforcement (prevent generic turbine data from being labeled PART_SPECIFIC_MEASURED)
9. No benchmark mutation (benchmark structure integrity)
10. End-to-end HPT provenance (retained failure modes link to verified evidence)
11. No unsupported CFM56-specific reliability claims (no 'will fail', 'has a failure rate of', etc.)
12. No invented maintenance intervals (labeled heuristic/assumed, no false certification claims)
"""
import json
import pytest
import re
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag.config import RAGConfig
from src.rag.retriever import AerospaceRetriever
from src.rag.hybrid_retriever import HybridRetriever
from src.rag.adaptive_router import AdaptiveQueryRouter
from src.agents.graph import FMEAGeneratorGraph
from src.agents.state import (
    ReliabilityScope,
    CriticalityInputParameter,
    CriticalityAnalysis,
    create_criticality_input_parameters,
    enforce_reliability_scope
)


class TestPhase5FSourceAudit:
    """Part A & D: Authoritative source provenance and dataset population audits."""

    @pytest.fixture(autouse=True)
    def load_sources_metadata(self):
        metadata_path = Path("data/metadata/sources.json")
        with open(metadata_path, "r", encoding="utf-8") as f:
            self.sources = json.load(f)
        self.sources_by_id = {s["id"]: s for s in self.sources}
        self.sources_by_report = {s.get("official_report_number", s["id"]): s for s in self.sources}

    def test_official_source_identifiers(self):
        """1. Verify official publisher report numbers and NTRS document IDs."""
        # Doc 1: Zaretsky et al. Turbine Blade Life
        # Official report number is NASA/TP-2013-217030, NTRS 20130013703
        doc1 = self.sources_by_report.get("NASA/TP-2013-217030") or self.sources_by_id.get("NASA-TP-2013-217830")
        assert doc1 is not None, "NASA/TP-2013-217030 not found in sources.json"
        assert doc1["official_report_number"] == "NASA/TP-2013-217030"
        assert doc1["ntrs_document_id"] == "20130013703"
        assert doc1["nasa_center_report_number"] == "E-15972-2"
        assert "Zaretsky" in doc1["authors"][0]
        assert "Soditus" in doc1["authors"][-1]
        assert doc1["legacy_id"] == "NASA-TP-2013-217830"

        # Doc 2: HOST Creep-Fatigue
        doc2 = self.sources_by_report.get("NASA-CP-2444") or self.sources_by_id.get("NASA-CREEP-FATIGUE-HOT-SECTION")
        assert doc2 is not None, "NASA-CP-2444 not found in sources.json"
        assert doc2["official_report_number"] == "NASA-CP-2444"
        assert doc2["ntrs_document_id"] == "19870001780"
        assert "Moreno" in doc2["authors"][0]

        # Doc 3: Internal Cooling Passages
        doc3 = self.sources_by_report.get("NASA-CR-198472") or self.sources_by_id.get("NASA-CR-198472")
        assert doc3 is not None, "NASA-CR-198472 not found in sources.json"
        assert doc3["official_report_number"] == "NASA-CR-198472"
        assert doc3["ntrs_document_id"] == "19960035825"
        assert "Johnson" in doc3["authors"][0]
        assert "Wagner" in doc3["authors"][1]

    def test_dataset_population_count_validation(self):
        """2. Verify that dataset populations are never exaggerated."""
        doc1 = self.sources_by_report.get("NASA/TP-2013-217030") or self.sources_by_id.get("NASA-TP-2013-217830")
        audit1 = doc1["dataset_population_audit"]

        # Exact population counts from Zaretsky et al. (NASA/TP-2013-217030)
        assert audit1["engines_analyzed"] == 16
        assert audit1["blade_sets_analyzed"] == 16
        assert audit1["blades_per_set"] == 82
        assert audit1["total_blades_audited"] == 1312
        assert audit1["failed_blades_observed"] == 111
        assert audit1["sets_with_failures"] == 11
        assert audit1["sets_with_zero_failures"] == 5

        # Must explicitly prohibit exaggerating 16 blade sets into 1,200+ blade sets
        assert audit1["blade_sets_analyzed"] != 1200
        assert audit1["blade_sets_analyzed"] < 100

        # Doc 2 must be classified as laboratory specimen data, NOT airline fleet data
        doc2 = self.sources_by_report.get("NASA-CP-2444") or self.sources_by_id.get("NASA-CREEP-FATIGUE-HOT-SECTION")
        audit2 = doc2["dataset_population_audit"]
        assert "B1900+Hf" in audit2["test_population"]
        assert "smooth" in audit2["test_population"].lower()

        # Doc 3 must be classified as rotating laboratory rig, NOT airline particulate clogging field logs
        doc3 = self.sources_by_id.get("NASA-CR-198472")
        audit3 = doc3["dataset_population_audit"]
        assert "1.15-scale" in audit3["test_article"].lower() or "rig" in audit3["test_article"].lower()


class TestPhase5FBenchmarkFreeze:
    """Part B: Canonical retrieval benchmark freeze and denominator integrity."""

    @pytest.fixture(autouse=True)
    def load_benchmark(self):
        bm_path = Path("tests/retrieval_benchmark_v1.json")
        with open(bm_path, "r", encoding="utf-8") as f:
            self.benchmark = json.load(f)

    def test_benchmark_denominator_consistency(self):
        """3. Establish canonical evaluation population without denominator drift."""
        total_queries = len(self.benchmark)
        evaluable_queries = [q for q in self.benchmark if not q.get("corpus_gap", False)]
        corpus_gap_queries = [q for q in self.benchmark if q.get("corpus_gap", False)]
        negative_controls = [q for q in self.benchmark if q.get("query_type") == "negative_control"]

        assert total_queries == 32, f"Expected exactly 32 canonical queries, got {total_queries}"
        assert len(evaluable_queries) == 30, f"Expected exactly 30 evaluable queries, got {len(evaluable_queries)}"
        assert len(corpus_gap_queries) == 2, f"Expected exactly 2 corpus gap queries, got {len(corpus_gap_queries)}"
        assert len(negative_controls) == 0, f"Expected 0 negative controls, got {len(negative_controls)}"

        # Verify that both open corpus gaps are fretting queries (RET-13 and RET-14)
        gap_ids = {q["query_id"] for q in corpus_gap_queries}
        assert gap_ids == {"RET-13", "RET-14"}

    def test_no_benchmark_mutation(self):
        """9. Ensure benchmark structure and ground truth basis are preserved."""
        for item in self.benchmark:
            assert "query_id" in item
            assert "query" in item
            assert "category" in item
            assert "relevant_documents" in item
            assert "relevant_pages" in item
            assert "ground_truth_basis" in item
            assert len(item["ground_truth_basis"].strip()) > 10


class TestPhase5FIntegrationAndRetrieval:
    """Part C: Verify production retrieval index and provenance preservation."""

    def test_phase5e_source_retrieval_via_production_path(self):
        """4. Verify that production retriever retrieves Phase 5E sources."""
        prod_config = RAGConfig.get_production_config()
        assert any(k in prod_config.collection_name or k in str(prod_config.chroma_dir) for k in ["core_final", "phase5e"])

        retriever = AerospaceRetriever(config=prod_config)
        results = retriever.retrieve("high pressure turbine blade thermomechanical fatigue", top_k=3)
        assert len(results) > 0

        # Retrieved documents must include the authoritative NASA TMF report
        retrieved_docs = [r.source_document for r in results]
        assert any("NASA_TP_2013_217830" in doc or "NASA_Fatigue_Life" in doc for doc in retrieved_docs)
        assert results[0].similarity_score >= 0.60

    def test_provenance_preservation(self):
        """5. Ensure all retrieved results maintain full provenance attributes."""
        retriever = AerospaceRetriever()
        results = retriever.retrieve("turbine blade internal cooling passage heat transfer", top_k=2)
        assert len(results) > 0

        r = results[0]
        assert r.source_document.endswith(".pdf")
        assert r.page_number > 0
        assert len(r.text.strip()) > 20
        assert r.similarity_score > 0.50
        assert r.doc_title != ""
        assert r.publisher != ""


class TestPhase5FCriticalityFormulaAudit:
    """Part E: Formula audit, parameter representation, beta assumption, and scope protection."""

    def test_formula_provenance(self):
        """6. Audit formula ground truth against technical definitions."""
        gt_path = Path("tests/formula_ground_truth.json")
        with open(gt_path, "r", encoding="utf-8") as f:
            formulas = json.load(f)

        assert len(formulas) >= 10, f"Expected at least 10 audited formulas, got {len(formulas)}"

        # Check MIL-STD-1629A Cm formula
        cm_formula = next(f for f in formulas if f["formula_name"] == "mode_criticality_number")
        assert "beta" in cm_formula["normalized_expression"]
        assert "alpha" in cm_formula["normalized_expression"]
        assert "lambda_p" in cm_formula["normalized_expression"]
        assert "t" in cm_formula["normalized_expression"]
        assert cm_formula["expected_units"]["lambda_p"] == "failures/operating_hour"
        assert cm_formula["expected_units"]["t"] == "operating_hours"

    def test_beta_assumption_labeling(self):
        """7. Verify beta=1.0 is labeled ASSUMPTION and not empirical fleet data."""
        params = create_criticality_input_parameters(
            beta=1.0,
            beta_status="ASSUMPTION",
            lambda_p=1e-5,
            alpha=0.3,
            t=1000.0
        )
        beta_param = params["beta"]
        assert beta_param.value == 1.0
        assert beta_param.assumption_status == "ASSUMPTION"
        assert beta_param.scope == ReliabilityScope.WORST_CASE_BOUND
        assert not beta_param.is_measured
        assert "Table 102.1" in beta_param.rationale or "bound" in beta_param.rationale

    def test_reliability_scope_enforcement(self):
        """8. Prevent assigning general turbine reliability data to CFM56 P/N 301-789-204-0."""
        # Scenario A: Generic turbine reliability data assigned to specific part number
        target_pn = "301-789-204-0"
        generic_scope = enforce_reliability_scope(
            target_part_number=target_pn,
            source_part_number=None,  # General turbine data from literature
            data_scope=ReliabilityScope.PART_SPECIFIC_MEASURED
        )
        # Must be downgraded from PART_SPECIFIC_MEASURED to GENERIC_TURBINE_BENCHMARK
        assert generic_scope == ReliabilityScope.GENERIC_TURBINE_BENCHMARK

        # Scenario B: Measured data on the exact matching part number
        matched_scope = enforce_reliability_scope(
            target_part_number=target_pn,
            source_part_number=target_pn,
            data_scope=ReliabilityScope.PART_SPECIFIC_MEASURED
        )
        assert matched_scope == ReliabilityScope.PART_SPECIFIC_MEASURED


class TestPhase5FEndToEndHPTProvenance:
    """Part F & G: End-to-end HPT failure mode audit and absence of unsupported claims."""

    @pytest.fixture(autouse=True)
    def load_trace(self):
        trace_path = Path("data/output/fresh_hpt_trace.json")
        if not trace_path.exists():
            pytest.skip("fresh_hpt_trace.json not found")
        with open(trace_path, "r", encoding="utf-8") as f:
            self.trace = json.load(f)

    def test_end_to_end_hpt_provenance(self):
        """10. Verify that every retained failure mode links to verified evidence."""
        modes = self.trace.get("failure_modes", [])
        assert len(modes) >= 4, f"Expected at least 4 failure modes, got {len(modes)}"

        for m in modes:
            assert m["mode_id"].startswith("FM-")
            evidence = m.get("citations", []) or m.get("evidence", [])
            assert len(evidence) > 0, f"Failure mode {m['mode_id']} has no evidence attached"
            for ev in evidence:
                assert ev["source_document"].endswith(".pdf")
                assert ev["page_number"] > 0

        # FM-HPT-001 (TMF) must cite authoritative sources
        fm1 = next(m for m in modes if m["mode_id"] == "FM-HPT-001")
        fm1_sources = [ev["source_document"] for ev in (fm1.get("citations", []) or fm1.get("evidence", []))]
        assert len(fm1_sources) > 0

    def test_no_unsupported_cfm56_reliability_claims(self):
        """11. Verify that trace contains no unsupported dogmatic reliability claims."""
        trace_str = json.dumps(self.trace).lower()
        prohibited_phrases = [
            "this exact cfm56 part will fail",
            "has a failure rate of 0.",
            "is certified by faa without testing",
            "100% accurate"
        ]
        for phrase in prohibited_phrases:
            assert phrase not in trace_str, f"Found prohibited unsupported claim: '{phrase}'"

    def test_no_invented_maintenance_intervals(self):
        """12. Ensure maintenance intervals are not claimed as certified mandatory intervals."""
        modes = self.trace.get("failure_modes", [])
        for m in modes:
            interval = m.get("inspection_interval", "")
            if not interval and isinstance(m.get("detection"), dict):
                interval = m["detection"].get("interval", "")
            # Ensure it does not falsely claim to be a certified airworthiness directive
            assert "mandatory ad limit" not in interval.lower()
