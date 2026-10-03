"""Comprehensive unit and adversarial test suite for Phase 5B Evidence-Grounded Reasoning Engine.

Tests:
1. Deterministic Claim Support (Thematic relevance, anti-mismatch detection).
2. Anti-Cheating Tests (Sabotaged/irrelevant evidence produces UNSUPPORTED; swapped evidence rejected).
3. Adversarial Component Handling (Lavatory Flush Valve, F-35 Waveguide, Unknown XYZ-999, Spacecraft Turbine).
4. Evidence-Gap Conditional Routing in LangGraph.
5. Dynamic Failure Mode Enumeration (non-fixed mode counts).
6. Evidence Coverage Report (deterministic claim-level counts).
7. Quantitative Criticality Integrity (no fabricated lambda_p, beta, alpha, t).
8. Retrieval Evaluation across all 11 aerospace categories.
"""
import json
import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.state import (
    EngineeringClaim,
    EvidenceRecord,
    SupportLevel,
    AnalysisStatus,
    ComponentInfo,
    SeverityCategory,
    CriticalityMethodology,
    FMEAReport
)
from src.agents.nodes.claim_verifier import verify_claim_against_evidence
from src.agents.nodes.validator import execute_engineering_validation
from src.agents.nodes.classifier import classify_component_node
from src.agents.providers.local_synthesizer import LocalAerospaceSynthesizer
from src.agents.graph import FMEAGeneratorGraph, check_corpus_coverage
from src.rag.retriever import AerospaceRetriever
from src.rag.config import RAGConfig


class TestDeterministicClaimSupport(unittest.TestCase):
    """Test deterministic evaluation of claims against evidence."""

    def test_tmf_claim_with_bird_strike_evidence_is_unsupported(self):
        """Claim A: TMF cracking with bird ingestion evidence MUST yield UNSUPPORTED."""
        claim = EngineeringClaim(
            claim_id="CLM-TEST-TMF-001",
            statement="Thermomechanical fatigue causes cyclic thermal strain and cracking in the turbine blade.",
            claim_type="failure_mode",
            support_level=SupportLevel.DIRECT_SOURCE
        )
        bird_strike_evidence = [
            EvidenceRecord(
                evidence_id="EVID-SABOTAGED-01",
                source_document="FAA_AC_33.75-1A.pdf",
                document_title="Engine Safety Analysis",
                publisher="FAA",
                page_number=14,
                excerpt="Large flocking bird ingestion criteria require demonstration that the engine will not experience an uncontained failure or catch fire upon bird impact.",
                retrieval_query="bird ingestion impact",
                retrieval_score=0.45,
                support_level=SupportLevel.SUPPORTING_SOURCE
            )
        ]

        result = verify_claim_against_evidence(claim, bird_strike_evidence)
        self.assertEqual(result.assigned_support_level, SupportLevel.UNSUPPORTED)
        self.assertFalse(result.is_verified)
        self.assertEqual(len(result.verified_evidence), 0)

    def test_hazardous_effect_claim_with_faa_ac_is_direct_or_supporting(self):
        """Claim B: Hazardous engine effect with FAA AC 33.75 passage MUST yield DIRECT_SOURCE or SUPPORTING_SOURCE."""
        claim = EngineeringClaim(
            claim_id="CLM-TEST-HAZ-001",
            statement="Major rotating components can produce hazardous engine effects including uncontained debris.",
            claim_type="end_effect",
            support_level=SupportLevel.DIRECT_SOURCE
        )
        faa_evidence = [
            EvidenceRecord(
                evidence_id="EVID-AC3375-GENUINE-01",
                source_document="FAA_AC_33.75-1A.pdf",
                document_title="Guidance Material for 14 CFR 33.75, Safety Analysis",
                publisher="FAA",
                page_number=11,
                excerpt="Hazardous engine effects include uncontained high-energy debris, complete inability to shut down the engine, and toxic products in the cabin.",
                retrieval_query="hazardous engine effect uncontained",
                retrieval_score=0.88,
                support_level=SupportLevel.DIRECT_SOURCE
            )
        ]

        result = verify_claim_against_evidence(claim, faa_evidence)
        self.assertIn(result.assigned_support_level, [SupportLevel.DIRECT_SOURCE, SupportLevel.SUPPORTING_SOURCE])
        self.assertTrue(result.is_verified)
        self.assertGreaterEqual(len(result.verified_evidence), 1)

    def test_swapped_evidence_anti_cheating(self):
        """Anti-Cheating Test: If TMF evidence is replaced with FOD evidence, claim must NOT be DIRECT_SOURCE."""
        tmf_claim = EngineeringClaim(
            claim_id="CLM-TMF-SWAP",
            statement="Thermomechanical fatigue causes microstructural cracking from transient thermal gradients.",
            claim_type="failure_mode",
            support_level=SupportLevel.DIRECT_SOURCE
        )
        fod_evidence = [
            EvidenceRecord(
                evidence_id="EVID-FOD-001",
                source_document="FAA_AC_33.75-1A.pdf",
                document_title="Guidance Material",
                publisher="FAA",
                page_number=22,
                excerpt="Foreign object damage resulting from runway gravel ingestion creates leading edge notches on compressor fan blades.",
                retrieval_query="foreign object damage",
                retrieval_score=0.52,
                support_level=SupportLevel.SUPPORTING_SOURCE
            )
        ]

        result = verify_claim_against_evidence(tmf_claim, fod_evidence)
        # Cannot be verified as direct source
        self.assertNotEqual(result.assigned_support_level, SupportLevel.DIRECT_SOURCE)
        self.assertEqual(result.assigned_support_level, SupportLevel.UNSUPPORTED)

    def test_irrelevant_evidence_never_marked_direct_source(self):
        """Anti-Cheating Test: Highly plausible engineering claim with irrelevant evidence cannot be marked DIRECT_SOURCE."""
        plausible_claim = EngineeringClaim(
            claim_id="CLM-PLAUSIBLE-01",
            statement="High temperature creep causes radial plastic elongation in superalloy turbine blades.",
            claim_type="failure_mode",
            support_level=SupportLevel.DIRECT_SOURCE
        )
        irrelevant_evidence = [
            EvidenceRecord(
                evidence_id="EVID-IRRELEVANT-01",
                source_document="FAA_AC_25.1309-1B.pdf",
                document_title="System Design",
                publisher="FAA",
                page_number=5,
                excerpt="Flight control system electrical wiring separation requirements under transport category rules.",
                retrieval_query="wiring separation",
                retrieval_score=0.35,
                support_level=SupportLevel.INSUFFICIENT_EVIDENCE
            )
        ]

        result = verify_claim_against_evidence(plausible_claim, irrelevant_evidence)
        self.assertNotEqual(result.assigned_support_level, SupportLevel.DIRECT_SOURCE)
        self.assertIn(result.assigned_support_level, [SupportLevel.UNSUPPORTED, SupportLevel.INSUFFICIENT_EVIDENCE])


class TestAdversarialComponents(unittest.TestCase):
    """Stress-test system with out-of-domain, cabin, and fictional components."""

    @classmethod
    def setUpClass(cls):
        cls.generator = FMEAGeneratorGraph()

    def test_lavatory_flush_valve_handling(self):
        """Commercial Aircraft Lavatory Flush Valve must NOT be classified as flight critical."""
        report = self.generator.run("Commercial Aircraft Lavatory Flush Valve")
        self.assertIsInstance(report, FMEAReport)
        # Classification must be non-critical / insufficient evidence
        self.assertEqual(report.component.analysis_status, AnalysisStatus.INSUFFICIENT_EVIDENCE)
        self.assertIn("Cabin", report.component.system)
        self.assertNotIn("Engine Critical Part", report.component.regulatory_class)
        # Graph routed via evidence-gap branch -> 0 manufactured aerospace modes
        self.assertEqual(len(report.failure_modes), 0)
        self.assertFalse(report.evidence_coverage.is_coverage_adequate)

    def test_f35_stealth_waveguide_handling(self):
        """F-35 Plasma Stealth Waveguide Injector (out-of-domain / classified) must yield INSUFFICIENT_EVIDENCE."""
        report = self.generator.run("F-35 Plasma Stealth Waveguide Injector")
        self.assertEqual(report.component.analysis_status, AnalysisStatus.INSUFFICIENT_EVIDENCE)
        self.assertEqual(len(report.failure_modes), 0)
        self.assertFalse(report.evidence_coverage.is_coverage_adequate)
        self.assertEqual(report.evidence_coverage.directly_supported, 0)

    def test_unknown_component_xyz999_handling(self):
        """Unknown Component XYZ-999 must yield INSUFFICIENT_EVIDENCE without hallucinations."""
        report = self.generator.run("Unknown Component XYZ-999")
        self.assertEqual(report.component.analysis_status, AnalysisStatus.INSUFFICIENT_EVIDENCE)
        self.assertEqual(len(report.failure_modes), 0)
        self.assertFalse(report.evidence_coverage.is_coverage_adequate)

    def test_fictional_spacecraft_turbine_handling(self):
        """Spacecraft Turbine Blade From Fictional Engine must yield INSUFFICIENT_EVIDENCE."""
        report = self.generator.run("Spacecraft Turbine Blade From Fictional Engine")
        self.assertEqual(report.component.analysis_status, AnalysisStatus.INSUFFICIENT_EVIDENCE)
        self.assertEqual(len(report.failure_modes), 0)

    def test_cfm56_hpt_blade_supported(self):
        """CFM56 HPT Stage 1 Blade must be fully grounded and supported."""
        report = self.generator.run("CFM56 High Pressure Turbine Stage 1 Rotor Blade")
        self.assertEqual(report.component.analysis_status, AnalysisStatus.SUPPORTED)
        self.assertIn("Engine Critical Part", report.component.regulatory_class)
        self.assertGreaterEqual(len(report.failure_modes), 4)
        self.assertTrue(report.evidence_coverage.is_coverage_adequate)
        self.assertGreater(report.evidence_coverage.total_claims, 10)


class TestDynamicFailureModeEnumeration(unittest.TestCase):
    """Verify that failure mode count varies dynamically and is not fixed at 6."""

    @classmethod
    def setUpClass(cls):
        cls.generator = FMEAGeneratorGraph()

    def test_mode_counts_vary_by_component(self):
        # 1. CFM56 HPT Blade -> 5 modes
        report_blade = self.generator.run("CFM56 High Pressure Turbine Stage 1 Rotor Blade")
        count_blade = len(report_blade.failure_modes)
        self.assertGreaterEqual(count_blade, 4)

        # 2. CFM56 Fuel Metering Valve -> 2 modes
        report_valve = self.generator.run("CFM56 fuel metering valve")
        count_valve = len(report_valve.failure_modes)
        self.assertIn(count_valve, [1, 2, 3])

        # 3. CFM56 Combustion Chamber -> 1-3 modes
        report_actuator = self.generator.run("CFM56 Combustion Chamber")
        count_actuator = len(report_actuator.failure_modes)
        self.assertIn(count_actuator, [1, 2, 3])

        # 4. Unknown Component -> 0 modes
        report_unknown = self.generator.run("Unknown Component XYZ-999")
        count_unknown = len(report_unknown.failure_modes)
        self.assertEqual(count_unknown, 0)

        # Confirm counts are not identical across all components
        self.assertNotEqual(count_blade, count_valve)
        self.assertNotEqual(count_valve, count_unknown)


class TestConditionalRoutingAndTrace(unittest.TestCase):
    """Verify LangGraph conditional routing and audit reasoning trace."""

    @classmethod
    def setUpClass(cls):
        cls.generator = FMEAGeneratorGraph()

    def test_evidence_gap_branch_taken(self):
        report = self.generator.run("Unknown Component XYZ-999")
        self.assertIsNotNone(report.reasoning_trace)
        trace = report.reasoning_trace
        self.assertIn("evidence_gap", trace.execution_route)
        self.assertNotIn("build_fmea", trace.execution_route)

    def test_adequate_branch_taken(self):
        report = self.generator.run("CFM56 High Pressure Turbine Stage 1 Rotor Blade")
        self.assertIsNotNone(report.reasoning_trace)
        trace = report.reasoning_trace
        self.assertIn("extract_evidence", trace.execution_route)
        self.assertIn("generate_candidates", trace.execution_route)
        self.assertIn("targeted_retrieval", trace.execution_route)
        self.assertIn("verify_claims", trace.execution_route)
        self.assertIn("build_fmea", trace.execution_route)
        self.assertIn("validate", trace.execution_route)

    def test_reasoning_trace_preserves_candidates_and_queries(self):
        report = self.generator.run("CFM56 High Pressure Turbine Stage 1 Rotor Blade")
        trace = report.reasoning_trace
        self.assertGreater(len(trace.candidate_modes_discovered), 0)
        self.assertGreater(len(trace.retrieval_queries), 0)
        self.assertGreater(len(trace.accepted_modes), 0)


class TestQuantitativeCriticalityHonesty(unittest.TestCase):
    """Verify quantitative criticality does not invent missing failure rate parameters."""

    @classmethod
    def setUpClass(cls):
        cls.generator = FMEAGeneratorGraph()

    def test_no_fabricated_lambda_or_beta(self):
        report = self.generator.run("CFM56 High Pressure Turbine Stage 1 Rotor Blade")
        for fm in report.failure_modes:
            crit = fm.criticality_analysis
            self.assertIsNotNone(crit)
            # Must be qualitative since corpus does not have fleet operational hours/rates
            self.assertEqual(crit.methodology, CriticalityMethodology.QUALITATIVE_MATRIX)
            # Quantitative fields must remain None
            self.assertIsNone(crit.part_failure_rate_lambda_p)
            self.assertIsNone(crit.operating_time_t)
            self.assertIsNone(crit.failure_mode_criticality_cm)


class TestEvidenceCoverageReport(unittest.TestCase):
    """Verify deterministic claim-level counting in EvidenceCoverageReport."""

    @classmethod
    def setUpClass(cls):
        cls.generator = FMEAGeneratorGraph()

    def test_coverage_counts_integrity(self):
        report = self.generator.run("CFM56 High Pressure Turbine Stage 1 Rotor Blade")
        cov = report.evidence_coverage
        self.assertIsNotNone(cov)
        self.assertGreater(cov.total_claims, 0)
        # Sum of categorized counts must equal total_claims
        calculated_sum = (
            cov.directly_supported +
            cov.supporting_evidence +
            cov.engineering_inference +
            cov.domain_heuristic +
            cov.unsupported +
            cov.insufficient_evidence
        )
        self.assertEqual(cov.total_claims, calculated_sum)
        self.assertTrue(cov.is_coverage_adequate)


class TestRetrievalEvaluationSet(unittest.TestCase):
    """Verify retrieval against evaluation_queries.json covering all 11 aerospace categories."""

    @classmethod
    def setUpClass(cls):
        config = RAGConfig()
        cls.retriever = AerospaceRetriever(config=config)
        eval_path = Path(__file__).resolve().parent / "evaluation_queries.json"
        with open(eval_path, "r", encoding="utf-8") as f:
            cls.eval_queries = json.load(f)

    def test_evaluation_queries_file_completeness(self):
        self.assertGreaterEqual(len(self.eval_queries), 20)
        categories = {q["category"] for q in self.eval_queries}
        required_categories = {
            "thermal fatigue", "creep", "FOD", "blade fracture", "containment",
            "hazardous engine effects", "maintenance", "NDT", "criticality",
            "severity", "single point failure"
        }
        for req in required_categories:
            self.assertIn(req, categories)

    def test_semantic_retrieval_scores_across_categories(self):
        """Execute all evaluation queries and confirm valid similarity_score / distance metrics."""
        for item in self.eval_queries:
            q = item["query"]
            results = self.retriever.retrieve(query=q, top_k=2)
            self.assertGreaterEqual(len(results), 1, f"Failed to retrieve passages for: {q}")
            top = results[0]
            # Verify terminology and score bounds
            self.assertGreater(top.similarity_score, 0.40, f"Low similarity score for {item['query_id']}: {top.similarity_score}")
            self.assertGreater(len(top.text), 30)
            self.assertTrue(top.source_document.endswith(".pdf"))


if __name__ == "__main__":
    unittest.main()
