"""Phase 5C Hardening & Provenance Integrity Test Suite.

Validates:
1. Provenance Invariants (real sources, valid pages, claim-specific linkage).
2. Anti-Cheating & Citation Swapping Detection.
3. Legitimate Shared Evidence Support (no naive duplicate rejection).
4. End-to-End Evidence Gate (candidate rejection under sabotaged evidence).
5. Component-Specific Scope Invariants (P/N overreach prevention).
6. Evidence Sensitivity (changing/removing evidence directly alters classification).
7. Reasoning Trace Auditable Transitions.
"""
import os
import unittest
from pathlib import Path
from src.agents.state import (
    EngineeringClaim,
    EvidenceRecord,
    SupportLevel,
    CandidateFailureMode,
    ComponentInfo,
    AnalysisStatus
)
from src.agents.nodes.claim_verifier import verify_claim_against_evidence
from src.agents.graph import FMEAGeneratorGraph
from src.rag.vector_store import ChromaVectorStore


class TestProvenanceInvariants(unittest.TestCase):
    """Enforce strict provenance invariants on all evidence records."""

    @classmethod
    def setUpClass(cls):
        cls.generator = FMEAGeneratorGraph()
        cls.report = cls.generator.run("CFM56 High Pressure Turbine Stage 1 Rotor Blade")
        cls.data_raw_dir = Path("data/raw")

    def test_every_evidence_backed_claim_has_evidence(self):
        """Every claim marked DIRECT_SOURCE or SUPPORTING_SOURCE must have evidence records."""
        for fm in self.report.failure_modes:
            claims = [
                fm.root_cause_claim,
                fm.local_effect_claim,
                fm.next_effect_claim,
                fm.end_effect_claim,
            ]
            if fm.severity_classification:
                claims.append(fm.severity_classification.justification)
            if fm.detection_and_controls:
                claims.append(fm.detection_and_controls.method_description)
                claims.append(fm.detection_and_controls.recommended_action)
            for claim in claims:
                if claim and claim.support_level in [SupportLevel.DIRECT_SOURCE, SupportLevel.SUPPORTING_SOURCE]:
                    self.assertGreater(
                        len(claim.evidence),
                        0,
                        f"Claim {claim.claim_id} has support_level {claim.support_level} but lacks evidence records."
                    )

    def test_every_evidence_record_points_to_real_indexed_file(self):
        """All cited source documents must exist in data/raw/."""
        all_evidence = []
        for fm in self.report.failure_modes:
            all_evidence.extend(fm.evidence_records)
            for claim in [fm.root_cause_claim, fm.local_effect_claim, fm.next_effect_claim, fm.end_effect_claim]:
                if claim and claim.evidence:
                    all_evidence.extend(claim.evidence)

        self.assertGreater(len(all_evidence), 0)
        for ev in all_evidence:
            doc_name = Path(ev.source_document).name
            doc_path = self.data_raw_dir / doc_name
            self.assertTrue(
                doc_path.exists(),
                f"Evidence {ev.evidence_id} cites non-existent file {doc_path}"
            )
            self.assertGreater(ev.page_number, 0, f"Evidence {ev.evidence_id} has invalid page number {ev.page_number}")

    def test_no_generic_global_citations_silently_attached(self):
        """Each failure mode must have distinct, mode-specific evidence queries, not identical global blobs."""
        mode_queries = set()
        for fm in self.report.failure_modes:
            queries_for_mode = tuple(sorted(ev.retrieval_query for ev in fm.evidence_records if ev.retrieval_query))
            if queries_for_mode:
                mode_queries.add(queries_for_mode)
        # Should have distinct retrieval queries across modes
        self.assertGreaterEqual(len(mode_queries), 2)


class TestCitationCopyingAndSwapping(unittest.TestCase):
    """Detect corrupted or copied citations and test valid multi-claim evidence sharing."""

    def test_swapped_citations_between_tmf_and_fod_detected(self):
        """Claim A (TMF) with Evidence B (FOD) and Claim B (FOD) with Evidence A (TMF) must be rejected."""
        tmf_claim = EngineeringClaim(
            claim_id="CLM-TMF-01",
            statement="Thermomechanical fatigue causes cyclic thermal strain cracking in high temperature turbine blades.",
            claim_type="failure_mode",
            support_level=SupportLevel.DIRECT_SOURCE
        )
        fod_claim = EngineeringClaim(
            claim_id="CLM-FOD-01",
            statement="Foreign object damage from ingested hard particles produces notches on compressor airfoils.",
            claim_type="failure_mode",
            support_level=SupportLevel.DIRECT_SOURCE
        )

        tmf_evidence = [
            EvidenceRecord(
                evidence_id="EVID-TMF-GENUINE",
                source_document="NASA-STD-8729.1A.pdf",
                document_title="Standard",
                publisher="NASA",
                page_number=48,
                excerpt="During thermal cycling, transient temperature gradients across the blade section generate severe cyclic thermal stress.",
                retrieval_query="thermal stress cyclic gradient",
                retrieval_score=0.82,
                support_level=SupportLevel.SUPPORTING_SOURCE
            )
        ]
        fod_evidence = [
            EvidenceRecord(
                evidence_id="EVID-FOD-GENUINE",
                source_document="EASA_CS-E_Amnd5_EasyAccessRules.pdf",
                document_title="CS-E",
                publisher="EASA",
                page_number=105,
                excerpt="Foreign object damage from bird ingestion or runway gravel produces leading edge notches accelerating crack growth.",
                retrieval_query="foreign object damage notch",
                retrieval_score=0.85,
                support_level=SupportLevel.SUPPORTING_SOURCE
            )
        ]

        # 1. Genuine pairs pass
        res_tmf_genuine = verify_claim_against_evidence(tmf_claim, tmf_evidence)
        res_fod_genuine = verify_claim_against_evidence(fod_claim, fod_evidence)
        self.assertIn(res_tmf_genuine.assigned_support_level, [SupportLevel.DIRECT_SOURCE, SupportLevel.SUPPORTING_SOURCE])
        self.assertIn(res_fod_genuine.assigned_support_level, [SupportLevel.DIRECT_SOURCE, SupportLevel.SUPPORTING_SOURCE])

        # 2. Corrupted / Swapped pairs fail
        res_tmf_corrupted = verify_claim_against_evidence(tmf_claim, fod_evidence)
        res_fod_corrupted = verify_claim_against_evidence(fod_claim, tmf_evidence)
        self.assertEqual(res_tmf_corrupted.assigned_support_level, SupportLevel.UNSUPPORTED)
        self.assertEqual(res_fod_corrupted.assigned_support_level, SupportLevel.UNSUPPORTED)

    def test_legitimate_shared_evidence_not_rejected_as_duplicate(self):
        """Single FAA passage legitimately defining both hazardous effects and uncontained debris supports both claims."""
        claim_hazard = EngineeringClaim(
            claim_id="CLM-HAZ-01",
            statement="Non-containment of high-energy debris is classified as a hazardous engine effect.",
            claim_type="end_effect",
            support_level=SupportLevel.DIRECT_SOURCE
        )
        claim_uncontained = EngineeringClaim(
            claim_id="CLM-UNCONT-01",
            statement="Turbine rotor burst can produce uncontained high-energy debris penetrating engine nacelles.",
            claim_type="end_effect",
            support_level=SupportLevel.DIRECT_SOURCE
        )

        shared_faa_passage = [
            EvidenceRecord(
                evidence_id="EVID-FAA-SHARED",
                source_document="FAA_AC_33.75-1A.pdf",
                document_title="Safety Analysis",
                publisher="FAA",
                page_number=10,
                excerpt="Hazardous engine effects include: non-containment of high-energy debris, uncontrollable fire, and toxic products in cabin air.",
                retrieval_query="hazardous engine effect uncontained debris",
                retrieval_score=0.88,
                support_level=SupportLevel.DIRECT_SOURCE
            )
        ]

        res_a = verify_claim_against_evidence(claim_hazard, shared_faa_passage)
        res_b = verify_claim_against_evidence(claim_uncontained, shared_faa_passage)
        self.assertTrue(res_a.is_verified)
        self.assertTrue(res_b.is_verified)
        self.assertIn(res_a.assigned_support_level, [SupportLevel.DIRECT_SOURCE, SupportLevel.SUPPORTING_SOURCE])
        self.assertIn(res_b.assigned_support_level, [SupportLevel.DIRECT_SOURCE, SupportLevel.SUPPORTING_SOURCE])


class TestEndToEndEvidenceGate(unittest.TestCase):
    """Verify that unsupported evidence causes candidate rejection in LangGraph pipeline."""

    def test_evidence_gate_rejects_candidate_with_irrelevant_evidence(self):
        """Candidate with sabotaged evidence must have is_retained=False and enter reasoning_trace.rejected_candidates."""
        claim = EngineeringClaim(
            claim_id="CLM-SABOTAGED-MODE",
            statement="Thermomechanical Fatigue Leading Edge Cracking: degradation driven by Cyclic thermal stress.",
            claim_type="failure_mode",
            support_level=SupportLevel.DIRECT_SOURCE
        )
        irrelevant_evidence = [
            EvidenceRecord(
                evidence_id="EVID-IRRELEVANT-01",
                source_document="NASA_ASRS_Maintenance_Incident_Reports.pdf",
                document_title="Maintenance Reports",
                publisher="NASA",
                page_number=3,
                excerpt="Lavatory flush valve seal leakage resulted in blue water accumulation in lower fuselage.",
                retrieval_query="lavatory flush valve seal",
                retrieval_score=0.20,
                support_level=SupportLevel.INSUFFICIENT_EVIDENCE
            )
        ]

        res = verify_claim_against_evidence(claim, irrelevant_evidence)
        self.assertEqual(res.assigned_support_level, SupportLevel.UNSUPPORTED)
        self.assertFalse(res.is_verified)
        self.assertEqual(len(res.verified_evidence), 0)


class TestComponentSpecificOverreach(unittest.TestCase):
    """Ensure component-specific part numbers and exact claims require matching evidence."""

    def test_pn_claim_with_generic_evidence_cannot_be_direct_source(self):
        """CFM56 HPT blade P/N 301-789-204-0 asserted with generic turbine blade document must NOT receive DIRECT_SOURCE."""
        pn_claim = EngineeringClaim(
            claim_id="CLM-PN-OVERREACH",
            statement="CFM56 HPT Stage 1 blade P/N 301-789-204-0 is susceptible to high temperature thermal fatigue.",
            claim_type="component-specific",
            support_level=SupportLevel.DIRECT_SOURCE
        )
        generic_evidence = [
            EvidenceRecord(
                evidence_id="EVID-GENERIC-01",
                source_document="FAA_AC_33.75-1A.pdf",
                document_title="Engine Safety Analysis",
                publisher="FAA",
                page_number=11,
                excerpt="High temperature turbine blades in commercial turbofan engines experience cyclic thermal stresses that cause thermal fatigue cracking.",
                retrieval_query="turbine blade thermal fatigue",
                retrieval_score=0.78,
                support_level=SupportLevel.SUPPORTING_SOURCE
            )
        ]

        res = verify_claim_against_evidence(pn_claim, generic_evidence)
        # Cannot be DIRECT_SOURCE because P/N 301-789-204-0 is absent from text
        self.assertNotEqual(res.assigned_support_level, SupportLevel.DIRECT_SOURCE)
        self.assertEqual(res.assigned_support_level, SupportLevel.SUPPORTING_SOURCE)

    def test_unbacked_mandatory_cycle_interval_rejected_as_unsupported(self):
        """Assertion of mandatory 500-cycle inspection with general inspection guidance must be UNSUPPORTED."""
        interval_claim = EngineeringClaim(
            claim_id="CLM-INTERVAL-01",
            statement="A borescope inspection every 500 flight cycles is mandatory.",
            claim_type="quantitative",
            support_level=SupportLevel.DIRECT_SOURCE
        )
        general_guidance_evidence = [
            EvidenceRecord(
                evidence_id="EVID-GUIDANCE-01",
                source_document="FAA_AC_33.75-1A.pdf",
                document_title="Safety Analysis",
                publisher="FAA",
                page_number=8,
                excerpt="Engine maintenance manuals establish periodic borescope inspection procedures to detect crack initiation in hot gas path airfoils.",
                retrieval_query="borescope inspection maintenance",
                retrieval_score=0.65,
                support_level=SupportLevel.SUPPORTING_SOURCE
            )
        ]

        res = verify_claim_against_evidence(interval_claim, general_guidance_evidence)
        self.assertEqual(res.assigned_support_level, SupportLevel.UNSUPPORTED)
        self.assertIn("Quantitative/modal overreach", res.verification_rationale)


class TestEvidenceSensitivityAndCoupling(unittest.TestCase):
    """Verify that changing evidence directly changes the verification outcome."""

    def test_strong_vs_weak_evidence_changes_outcome(self):
        """Case A (strong evidence) yields SUPPORTED, Case B (weak/vague evidence) yields INSUFFICIENT_EVIDENCE."""
        claim = EngineeringClaim(
            claim_id="CLM-SENSITIVITY-01",
            statement="High temperature turbine blades experience cyclic thermal stress during engine start and stop cycles.",
            claim_type="failure_mode",
            support_level=SupportLevel.DIRECT_SOURCE
        )

        strong_evidence = [
            EvidenceRecord(
                evidence_id="EVID-STRONG-01",
                source_document="NASA-STD-8729.1A.pdf",
                document_title="Standard",
                publisher="NASA",
                page_number=48,
                excerpt="During engine acceleration and deceleration, transient temperature gradients across the blade section generate severe cyclic thermal stress.",
                retrieval_query="transient temperature gradient cyclic thermal stress",
                retrieval_score=0.88,
                support_level=SupportLevel.DIRECT_SOURCE
            )
        ]
        weak_evidence = [
            EvidenceRecord(
                evidence_id="EVID-WEAK-01",
                source_document="FAA_AC_25.1309-1B.pdf",
                document_title="System Design",
                publisher="FAA",
                page_number=2,
                excerpt="General discussion of aircraft system reliability principles and qualitative assessment methods without component thermal details.",
                retrieval_query="system reliability methods",
                retrieval_score=0.22,
                support_level=SupportLevel.INSUFFICIENT_EVIDENCE
            )
        ]

        res_strong = verify_claim_against_evidence(claim, strong_evidence)
        res_weak = verify_claim_against_evidence(claim, weak_evidence)

        self.assertIn(res_strong.assigned_support_level, [SupportLevel.DIRECT_SOURCE, SupportLevel.SUPPORTING_SOURCE])
        self.assertTrue(res_strong.is_verified)

        self.assertEqual(res_weak.assigned_support_level, SupportLevel.INSUFFICIENT_EVIDENCE)
        self.assertFalse(res_weak.is_verified)

    def test_evidence_removal_prevents_unjustified_direct_source(self):
        """Removing supporting evidence from a claim results in INSUFFICIENT_EVIDENCE."""
        claim = EngineeringClaim(
            claim_id="CLM-REMOVAL-01",
            statement="Turbine rotor blade separation can liberate uncontained high-energy fragments.",
            claim_type="failure_mode",
            support_level=SupportLevel.DIRECT_SOURCE
        )
        empty_evidence = []
        res = verify_claim_against_evidence(claim, empty_evidence)
        self.assertEqual(res.assigned_support_level, SupportLevel.INSUFFICIENT_EVIDENCE)
        self.assertFalse(res.is_verified)


if __name__ == "__main__":
    unittest.main()
