"""Unit tests for Phase 5A Engineering Data Model & Criticality Methodology Redesign."""
import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.state import (
    SupportLevel,
    AnalysisStatus,
    SeverityCategory,
    ProbabilityLevel,
    CriticalityMethodology,
    DetectionCategory,
    EvidenceRecord,
    EngineeringAssumption,
    EngineeringClaim,
    SeverityClassification,
    CriticalityAnalysis,
    DetectionAndControls,
    CILAssessment,
    LegacyRPN,
    ComponentInfo,
    FailureModeEntry,
    ValidationReport,
    FMEAReport
)
from src.agents.providers.local_synthesizer import LocalAerospaceSynthesizer


class TestPhase5ASchemaDesign(unittest.TestCase):
    """Test suite verifying Phase 5A engineering schema capabilities."""

    def test_1_unknown_severity_representation(self):
        """Verify the model supports UNKNOWN severity when evidence is missing."""
        claim = EngineeringClaim(
            claim_id="CLM-SEV-UNK",
            statement="Consequence on system level cannot be determined from available airframe data.",
            support_level=SupportLevel.INSUFFICIENT_EVIDENCE
        )
        sev = SeverityClassification(
            category=SeverityCategory.UNKNOWN,
            definition="Severity unclassified due to lack of end-effect loss statements.",
            justification=claim,
            classification_confidence="UNVERIFIED"
        )
        self.assertEqual(sev.category, SeverityCategory.UNKNOWN)
        self.assertEqual(sev.justification.support_level, SupportLevel.INSUFFICIENT_EVIDENCE)
        self.assertEqual(sev.classification_confidence, "UNVERIFIED")

    def test_2_unknown_criticality_representation(self):
        """Verify the model supports UNKNOWN criticality when failure rates are unavailable."""
        claim = EngineeringClaim(
            claim_id="CLM-CRIT-UNK",
            statement="Operating time and part failure rates (lambda_p) are not present in corpus.",
            support_level=SupportLevel.INSUFFICIENT_EVIDENCE
        )
        crit = CriticalityAnalysis(
            methodology=CriticalityMethodology.UNKNOWN,
            qualitative_level=ProbabilityLevel.UNKNOWN,
            rationale=claim,
            data_source_description="No reliability prediction available"
        )
        self.assertEqual(crit.methodology, CriticalityMethodology.UNKNOWN)
        self.assertEqual(crit.qualitative_level, ProbabilityLevel.UNKNOWN)
        self.assertIsNone(crit.failure_mode_criticality_cm)

    def test_3_evidence_backed_claim(self):
        """Verify an evidence-backed claim correctly validates direct documentary proof."""
        evid = EvidenceRecord(
            evidence_id="EVID-AC3375-P11",
            source_document="FAA_AC_33.75-1A.pdf",
            document_title="Guidance Material for 14 CFR 33.75, Safety Analysis",
            publisher="FAA",
            page_number=11,
            section="§ 7.b",
            excerpt="Release of multiple blades will likely exceed containment ring capability.",
            support_level=SupportLevel.DIRECT_SOURCE
        )
        claim = EngineeringClaim(
            claim_id="CLM-HAZARD-001",
            statement="Uncontained blade release constitutes a Hazardous Engine Effect.",
            claim_type="end_effect",
            support_level=SupportLevel.DIRECT_SOURCE,
            evidence=[evid]
        )
        self.assertTrue(claim.is_evidence_backed)
        self.assertEqual(claim.support_level, SupportLevel.DIRECT_SOURCE)
        self.assertEqual(len(claim.evidence), 1)
        self.assertEqual(claim.evidence[0].page_number, 11)

    def test_4_unsupported_claim(self):
        """Verify that unsupported claims are explicitly labeled without false confidence."""
        claim = EngineeringClaim(
            claim_id="CLM-UNSUPPORTED-01",
            statement="Warp plasma injection causes exotic lattice decay.",
            claim_type="failure_mode",
            support_level=SupportLevel.UNSUPPORTED,
            evidence=[],
            verification_notes="Fictitious subsystem; zero documentary evidence exists."
        )
        self.assertFalse(claim.is_evidence_backed)
        self.assertEqual(claim.support_level, SupportLevel.UNSUPPORTED)
        self.assertEqual(len(claim.evidence), 0)

    def test_5_inferred_claim(self):
        """Verify engineering inferences derived from domain physics are distinctly categorized."""
        claim = EngineeringClaim(
            claim_id="CLM-INF-TMF",
            statement="Thermal strain concentrated at cooling orifices promotes micro-crack initiation.",
            claim_type="root_cause",
            support_level=SupportLevel.ENGINEERING_INFERENCE,
            verification_notes="Derived from finite element thermal gradient analysis."
        )
        self.assertEqual(claim.support_level, SupportLevel.ENGINEERING_INFERENCE)
        self.assertFalse(claim.is_evidence_backed)  # Inferred, not direct quote

    def test_6_assumption_requiring_verification(self):
        """Verify explicit modeling of engineering assumptions and required verifications."""
        asm = EngineeringAssumption(
            assumption_id="ASM-001",
            statement="Containment ring structure retains all single blade shedding events.",
            engineering_rationale="Blade containment test per 14 CFR § 33.19 passed at certification.",
            risk_impact="Catastrophic airframe penetration if uncontained.",
            verification_required=True
        )
        self.assertTrue(asm.verification_required)
        self.assertIn("containment", asm.statement.lower())

    def test_7_multiple_evidence_records(self):
        """Verify that a claim can aggregate multiple independent evidence records."""
        evid_1 = EvidenceRecord(
            evidence_id="EVID-1",
            source_document="MIL-STD-1629A.pdf",
            document_title="Procedures for FMECA",
            publisher="DoD",
            page_number=16,
            excerpt="Category I - Catastrophic",
            support_level=SupportLevel.DIRECT_SOURCE
        )
        evid_2 = EvidenceRecord(
            evidence_id="EVID-2",
            source_document="FAA_AC_33.75-1A.pdf",
            document_title="Safety Analysis",
            publisher="FAA",
            page_number=4,
            excerpt="Engine Critical Part designation",
            support_level=SupportLevel.SUPPORTING_SOURCE
        )
        claim = EngineeringClaim(
            claim_id="CLM-MULT-EVID",
            statement="Component failure hazard classification.",
            support_level=SupportLevel.DIRECT_SOURCE,
            evidence=[evid_1, evid_2]
        )
        self.assertEqual(len(claim.evidence), 2)
        self.assertTrue(claim.is_evidence_backed)

    def test_8_claim_specific_citations(self):
        """Verify that individual fields on a failure mode reference different evidence records."""
        evid_cause = EvidenceRecord(
            evidence_id="EVID-CAUSE",
            source_document="EASA_CS-E_Amnd5_EasyAccessRules.pdf",
            document_title="CS-E 510 Safety Analysis",
            publisher="EASA",
            page_number=93,
            excerpt="Cyclic stress and temperature fatigue life analysis.",
            support_level=SupportLevel.SUPPORTING_SOURCE
        )
        evid_action = EvidenceRecord(
            evidence_id="EVID-ACTION",
            source_document="FAA_AC_33.75-1A.pdf",
            document_title="AC 33.75-1A",
            publisher="FAA",
            page_number=8,
            excerpt="Maintenance manual periodic inspection limits.",
            support_level=SupportLevel.SUPPORTING_SOURCE
        )

        cause_claim = EngineeringClaim(
            claim_id="C-1",
            statement="Thermal gradient fatigue stress",
            evidence=[evid_cause]
        )
        action_claim = EngineeringClaim(
            claim_id="A-1",
            statement="Borescope optical check every 500 cycles",
            evidence=[evid_action]
        )

        fm = FailureModeEntry(
            mode_id="FM-SPECIFIC-01",
            failure_mode="Airfoil thermal cracking",
            root_cause="Thermal gradients",
            local_effect="Cracking",
            next_higher_effect="EGT rise",
            end_effect="Thrust loss",
            root_cause_claim=cause_claim,
            detection_and_controls=DetectionAndControls(
                primary_detection_means="Optical Borescope",
                method_description=EngineeringClaim(claim_id="D-1", statement="Borescope"),
                recommended_action=action_claim
            )
        )

        # Confirm cause evidence is NOT the same as action evidence (claim-level separation)
        self.assertEqual(fm.root_cause_claim.evidence[0].source_document, "EASA_CS-E_Amnd5_EasyAccessRules.pdf")
        self.assertEqual(fm.detection_and_controls.recommended_action.evidence[0].source_document, "FAA_AC_33.75-1A.pdf")

    def test_9_separation_of_severity_and_criticality(self):
        """Verify Severity and Criticality are represented as distinct, independent models."""
        sev = SeverityClassification(
            category=SeverityCategory.CATEGORY_I,
            definition="Category I - Catastrophic",
            justification=EngineeringClaim(claim_id="J1", statement="Uncontained blade failure")
        )
        
        # Quantitative Criticality Calculation per Task 102 § 3.2.1.6: Cm = beta * alpha * lambda_p * t
        # beta = 1.0, alpha = 0.25, lambda_p = 10 failures / 10^6 hours = 1e-5, t = 1000 hours
        beta = 1.0
        alpha = 0.25
        lambda_p = 1e-5
        t = 1000.0
        cm_expected = beta * alpha * lambda_p * t  # 0.0025

        crit = CriticalityAnalysis(
            methodology=CriticalityMethodology.QUANTITATIVE_CALCULATION,
            beta_conditional_probability=beta,
            alpha_failure_mode_ratio=alpha,
            part_failure_rate_lambda_p=lambda_p,
            operating_time_t=t,
            failure_mode_criticality_cm=cm_expected,
            rationale=EngineeringClaim(claim_id="R1", statement="Calculated via Task 102 formula")
        )

        self.assertEqual(sev.category, SeverityCategory.CATEGORY_I)
        self.assertEqual(crit.methodology, CriticalityMethodology.QUANTITATIVE_CALCULATION)
        self.assertAlmostEqual(crit.failure_mode_criticality_cm, 0.0025)

    def test_10_legacy_rpn_isolation(self):
        """Verify legacy automotive RPN is isolated with explicit disclaimers."""
        rpn = LegacyRPN(
            severity_score=8,
            occurrence_score=4,
            detection_score=4,
            rpn_value=128
        )
        self.assertEqual(rpn.rpn_value, 128)
        self.assertFalse(rpn.is_mil_std_1629a_standard)
        self.assertEqual(rpn.methodology, "legacy_automotive_unverified")
        self.assertIn("NOT part of MIL-STD-1629A", rpn.disclaimer)


if __name__ == "__main__":
    unittest.main()
