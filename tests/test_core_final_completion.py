"""Regression and validation tests for FMEA-GPT Final Core Engineering Completion.

Verifies:
1. Two newly acquired sources have verified provenance metadata in sources.json.
2. Production retriever accesses the core_final store and retrieves from both new sources.
3. Engineering taxonomy is externalized to subsystem_taxonomy.json; no ATA strings hardcoded.
4. Component classification respects input naming and does not force CFM56 branding on other engines.
5. End-to-end FMEA generates evidence-grounded failure modes with full provenance.
6. Inspection intervals are not invented cycle limits; criticality probability is unquantified (UNKNOWN).
"""
import json
from pathlib import Path
import pytest

from src.rag.config import RAGConfig
from src.rag.retriever import AerospaceRetriever
from src.agents.taxonomy import get_taxonomy, classify_component_from_taxonomy
from src.agents.state import ProbabilityLevel, AnalysisStatus
from src.agents.graph import FMEAGeneratorGraph


class TestCoreFinalProvenanceAndIntegrity:
    """Part A: Verify sources.json metadata for new sources."""

    @pytest.fixture(autouse=True)
    def setup_sources(self):
        sources_path = Path("data/metadata/sources.json")
        with open(sources_path, "r", encoding="utf-8") as f:
            self.sources = json.load(f)
        self.by_id = {s["id"]: s for s in self.sources}

    def test_new_source_provenance_metadata(self):
        """1. Verify Arakere fretting paper and CR-189111 TBC report metadata."""
        # 1. Fretting source
        fretting = self.by_id.get("NASA-MSFC-ARAKERE-2000-FRETTING")
        assert fretting is not None, "Arakere fretting paper not found in sources.json"
        assert fretting["official_report_number"] == "ASME-Trib-61"
        assert fretting["ntrs_document_id"] == "20000033269"
        assert fretting["evidence_category"] == "NUMERICAL_ANALYSIS"
        assert "fretting" in fretting["technical_domain"].lower()
        assert fretting["publication_year"] == 2000
        assert "PUBLIC" in fretting["public_availability"]
        assert any("Arakere" in a for a in fretting["authors"])
        assert any("Swanson" in a for a in fretting["authors"])
        assert "SSME" in fretting["dataset_population_audit"]["test_article"]

        # 2. TBC source
        tbc = self.by_id.get("NASA-CR-189111")
        assert tbc is not None, "CR-189111 TBC report not found in sources.json"
        assert tbc["official_report_number"] == "NASA-CR-189111"
        assert tbc["ntrs_document_id"] == "19930003401"
        assert tbc["evidence_category"] == "LABORATORY_EXPERIMENT"
        assert "coating" in tbc["technical_domain"].lower()
        assert tbc["publication_year"] == 1991
        assert "PUBLIC" in tbc["public_availability"]
        assert any("Meier" in a for a in tbc["authors"])
        assert "EB-PVD" in tbc["dataset_population_audit"]["test_article"]

    def test_taxonomy_externalization_integrity(self):
        """2. Verify subsystem_taxonomy.json structure and status vocabulary."""
        tax = get_taxonomy()
        assert tax["schema_version"] == "1.0"
        vocab = tax["status_vocabulary"]
        for required_status in ["SOURCE_DERIVED", "REFERENCE_TAXONOMY", "UNVERIFIED_ENGINEERING_KNOWLEDGE", "NOT_ESTABLISHED_IN_CORPUS"]:
            assert required_status in vocab

        # ATA chapters present as reference taxonomy
        ata = tax["ata_chapters"]
        assert ata["_status"] == "REFERENCE_TAXONOMY"
        assert "72" in ata and "Turbine" in ata["72"]["title"]
        assert "73" in ata
        assert "27" in ata
        assert "38" in ata

        # Default part number is uncataloged / unspecified
        assert tax["default_part_number"]["value"] == "UNSPECIFIED"

    def test_component_classification_preserves_custom_naming(self):
        """3. Classification must not force CFM56 branding on non-CFM56 turbomachinery."""
        custom_input = "PW4000 High Pressure Turbine 2nd Stage Rotor Blade"
        comp = classify_component_from_taxonomy(custom_input)
        assert comp.component_name == custom_input
        assert "High Pressure Turbine" in comp.subsystem
        assert "Engine Critical Part" in comp.regulatory_class
        assert comp.part_number == "UNSPECIFIED"

    def test_production_retriever_accesses_core_final(self):
        """4. Production retriever queries return hits from both new technical sources."""
        cfg = RAGConfig.get_production_config()
        assert "core_final" in cfg.collection_name or "core_final" in str(cfg.chroma_dir)
        retriever = AerospaceRetriever(config=cfg)

        # Fretting query
        fret_results = retriever.retrieve("turbine blade dovetail fretting fatigue micro-slip", top_k=3)
        assert any("Arakere" in r.source_document for r in fret_results)

        # TBC query
        tbc_results = retriever.retrieve("thermal barrier coating spallation EB-PVD", top_k=3)
        assert any("CR_189111" in r.source_document for r in tbc_results)

    def test_end_to_end_hpt_epistemic_properties(self):
        """5. End-to-end HPT generation adheres to epistemic rules (no invented intervals, UNKNOWN prob)."""
        cfg = RAGConfig.get_production_config()
        graph = FMEAGeneratorGraph(config=cfg)
        report = graph.run("CFM56 High Pressure Turbine Stage 1 Rotor Blade", part_number="301-789-204-0")

        assert report.component.analysis_status == AnalysisStatus.SUPPORTED
        assert len(report.failure_modes) >= 4

        for fm in report.failure_modes:
            # Inspection interval must NOT claim certified mandatory cycles
            assert "500 flight cycles" not in fm.inspection_interval.lower()
            assert "1,000 flight cycles" not in fm.inspection_interval.lower()
            assert "not established" in fm.inspection_interval.lower()

            # Criticality probability must be UNKNOWN
            crit = fm.criticality_analysis
            assert crit is not None
            assert crit.qualitative_level == ProbabilityLevel.UNKNOWN
            assert "Probability level not established" in crit.matrix_position

            # Legacy RPN must be quarantined
            assert fm.legacy_rpn_audit is not None
            assert fm.legacy_rpn_audit.methodology == "legacy_automotive_unverified"

            # Detection claim must have DOMAIN_HEURISTIC or SUPPORTING_SOURCE support level
            assert fm.detection_and_controls.method_description.support_level in [
                "domain_heuristic", "supporting_source"
            ]
