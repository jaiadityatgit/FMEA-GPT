"""Comprehensive unit and integration tests for FMEA-GPT Phase 2 agentic generation engine."""
import json
import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.state import (
    ComponentInfo,
    FailureModeEntry,
    ValidationReport,
    FMEAReport
)
from src.agents.providers.local_synthesizer import LocalAerospaceSynthesizer
from src.agents.graph import FMEAGeneratorGraph
from src.agents.exporters.fmea_table import format_mil_std_1629a_markdown
from src.agents.exporters.digital_twin import export_digital_twin_json
from src.agents.exporters.cil_exporter import format_critical_items_list_markdown


class TestLocalAerospaceSynthesizer(unittest.TestCase):
    """Test the offline aerospace domain reasoning synthesizer."""

    def setUp(self):
        self.synthesizer = LocalAerospaceSynthesizer()

    def test_component_classification_turbine_blade(self):
        comp = self.synthesizer.generate_structured(
            prompt="CFM56 turbofan engine high pressure turbine rotor blade",
            response_model=ComponentInfo
        )
        self.assertIn("Turbine", comp.subsystem)
        self.assertIn("14 CFR § 33.75", comp.regulatory_class)
        self.assertGreater(len(comp.operating_environment), 20)

    def test_failure_modes_generation_and_rpn(self):
        comp = ComponentInfo(
            component_name="CFM56 HPT Stage 1 Blade",
            subsystem="High Pressure Turbine (HPT) Module"
        )
        modes = self.synthesizer.generate_structured(
            prompt="Generate FMEA for HPT Blade",
            response_model=list[FailureModeEntry],  # type: ignore
            context={"component": comp}
        )
        self.assertGreaterEqual(len(modes), 4)

        for m in modes:
            self.assertTrue(m.mode_id.startswith("FM-"))
            self.assertGreaterEqual(m.severity, 1)
            self.assertLessEqual(m.severity, 10)
            self.assertGreaterEqual(m.occurrence, 1)
            self.assertLessEqual(m.occurrence, 10)
            self.assertGreaterEqual(m.detection, 1)
            self.assertLessEqual(m.detection, 10)
            # Verify RPN calculation
            self.assertEqual(m.rpn, m.severity * m.occurrence * m.detection)
            # Verify required fields
            self.assertGreater(len(m.root_cause), 5)
            self.assertGreater(len(m.local_effect), 5)
            self.assertGreater(len(m.end_effect), 5)
            self.assertGreater(len(m.recommended_action), 5)

    def test_validation_report_compliance(self):
        comp = ComponentInfo(component_name="CFM56 Blade")
        modes = self.synthesizer.generate_structured(
            prompt="HPT",
            response_model=list[FailureModeEntry],  # type: ignore
            context={"component": comp}
        )
        report: ValidationReport = self.synthesizer.generate_structured(
            prompt="validate",
            response_model=ValidationReport,
            context={"component": comp, "failure_modes": modes}
        )
        self.assertTrue(report.is_compliant)
        self.assertGreater(report.total_modes_evaluated, 0)
        self.assertGreater(report.max_rpn, 0)


class TestFMEAGeneratorGraph(unittest.TestCase):
    """Integration test verifying end-to-end LangGraph execution."""

    def test_end_to_end_graph_execution(self):
        generator = FMEAGeneratorGraph()
        report = generator.run(
            component_input="CFM56 High Pressure Turbine Stage 1 Rotor Blade",
            target_part_number="301-789-204-0"
        )
        self.assertIsInstance(report, FMEAReport)
        self.assertEqual(report.component.part_number, "301-789-204-0")
        self.assertGreaterEqual(len(report.failure_modes), 4)
        self.assertTrue(report.validation.is_compliant)

        # Check that citations are linked from RAG knowledge base
        has_citations = any(len(fm.citations) > 0 for fm in report.failure_modes)
        self.assertTrue(has_citations)


class TestFMEAExporters(unittest.TestCase):
    """Test output formatting across Markdown, Digital Twin JSON, and CIL."""

    @classmethod
    def setUpClass(cls):
        generator = FMEAGeneratorGraph()
        cls.report = generator.run(
            component_input="CFM56-7B High Pressure Turbine Blade",
            target_part_number="301-789-204-0"
        )

    def test_mil_std_1629a_markdown_format(self):
        md = format_mil_std_1629a_markdown(self.report)
        self.assertIn("FAILURE MODE AND EFFECTS ANALYSIS (FMEA) WORKSHEET", md)
        self.assertIn("MIL-STD-1629A", md)
        self.assertIn("| Item / ID | Failure Mode |", md)
        self.assertIn("Regulatory Compliance & Provenance Citations", md)
        self.assertIn("FM-HPT-001", md)

    def test_digital_twin_json_format(self):
        dt_str = export_digital_twin_json(self.report)
        data = json.loads(dt_str)
        self.assertEqual(data["digital_twin_schema_version"], "1.0.0")
        self.assertIn("degradation_models", data)
        self.assertGreaterEqual(len(data["degradation_models"]), 4)

        entry = data["degradation_models"][0]
        self.assertIn("fault_code", entry)
        self.assertIn("risk_metrics", entry)
        self.assertIn("telemetry_indicators", entry)

    def test_cil_markdown_format(self):
        cil_md = format_critical_items_list_markdown(self.report)
        self.assertIn("CRITICAL ITEMS LIST (CIL)", cil_md)
        self.assertIn("NASA-STD-8729.1A", cil_md)
        self.assertIn("SINGLE POINT FAILURE (SPF)", cil_md)


if __name__ == "__main__":
    unittest.main()
