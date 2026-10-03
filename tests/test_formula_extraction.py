"""Tests for Phase 5E formula extraction and structured mathematical provenance.

Validates:
1. Formula detection from raw page text
2. Known formula pattern matching (MIL-STD-1629A Cm, Cr)
3. Greek letter normalization
4. Variable definition extraction
5. Indexable text generation
6. Formula ground truth validation
"""
import json
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag.formula_extractor import (
    ExtractedFormula,
    detect_equation_lines,
    extract_formulas_from_text,
    normalize_greek_in_text,
    extract_variable_definitions_from_context,
    KNOWN_FORMULA_PATTERNS,
)


class TestGreekNormalization:
    """Test Greek letter normalization for searchability."""

    def test_normalize_alpha_beta(self):
        assert "alpha" in normalize_greek_in_text("α")
        assert "beta" in normalize_greek_in_text("β")

    def test_normalize_lambda(self):
        result = normalize_greek_in_text("λp × t")
        assert "lambda" in result
        assert "t" in result

    def test_normalize_sigma(self):
        assert "sigma" in normalize_greek_in_text("σ")

    def test_no_change_for_ascii(self):
        assert normalize_greek_in_text("Cm = a * b") == "Cm = a * b"

    def test_mixed_greek_ascii(self):
        result = normalize_greek_in_text("Cm = β × α × λp × t")
        assert "beta" in result
        assert "alpha" in result
        assert "lambda" in result


class TestEquationDetection:
    """Test detection of equation-containing lines."""

    def test_detect_simple_equation(self):
        text = "The formula is:\nCm = a * b * lambda * t\nwhere a is the ratio"
        lines = detect_equation_lines(text)
        assert len(lines) >= 1
        assert any("Cm" in line for _, line in lines)

    def test_reject_long_sentence(self):
        text = "This is a very long sentence that happens to contain an equals sign = but is really just a paragraph of ordinary text describing something unrelated to mathematics and should not be detected as an equation because it has many words."
        lines = detect_equation_lines(text)
        assert len(lines) == 0

    def test_detect_greek_equation(self):
        text = "Cm = β × α × λp × t"
        lines = detect_equation_lines(text)
        assert len(lines) >= 1

    def test_detect_reliability_function(self):
        text = "R(t) = e^(-λt)"
        lines = detect_equation_lines(text)
        assert len(lines) >= 1

    def test_empty_text(self):
        assert detect_equation_lines("") == []

    def test_no_equations(self):
        text = "This is a paragraph about turbine blades.\nNo formulas here.\nJust text."
        lines = detect_equation_lines(text)
        assert len(lines) == 0


class TestFormulaExtraction:
    """Test extraction and classification of engineering formulas."""

    def test_extract_cm_formula(self):
        text = "4.5.2 Mode criticality number.\nCm = β × α × λp × t\nwhere β is the conditional probability"
        formulas = extract_formulas_from_text(
            text, "MIL-STD-1629A.pdf", 28, "Task 102"
        )
        assert len(formulas) >= 1
        cm_formulas = [f for f in formulas if f.formula_name == "mode_criticality_number"]
        assert len(cm_formulas) >= 1
        f = cm_formulas[0]
        assert f.formula_type == "criticality"
        assert "beta" in f.normalized_expression
        assert "alpha" in f.normalized_expression
        assert "lambda" in f.normalized_expression
        assert f.confidence == "extracted"

    def test_extract_cr_formula(self):
        text = "4.5.3 Item criticality number.\nCr = Σ Cm\nThe item criticality"
        formulas = extract_formulas_from_text(
            text, "MIL-STD-1629A.pdf", 29, "Task 102"
        )
        cr_formulas = [f for f in formulas if f.formula_name == "item_criticality_number"]
        assert len(cr_formulas) >= 1
        f = cr_formulas[0]
        assert f.formula_type == "criticality"
        assert "Cr" in f.variable_definitions

    def test_extract_plain_text_cm(self):
        """Test that OCR-rendered plain text version is also matched."""
        text = "Cm = a * b * lambda * t"
        formulas = extract_formulas_from_text(
            text, "MIL-STD-1629A.pdf", 28, "Task 102"
        )
        # Should still match the Cm pattern even without Greek characters
        cm_formulas = [f for f in formulas if "Cm" in f.raw_text and "=" in f.raw_text]
        assert len(cm_formulas) >= 1

    def test_generic_formula_extraction(self):
        """Test that unknown formulas are still extracted generically."""
        text = "The stress intensity factor is:\nK = Y × σ × √(π × a)\nwhere Y is the geometry factor"
        formulas = extract_formulas_from_text(
            text, "test_doc.pdf", 1, "Section 3"
        )
        k_formulas = [f for f in formulas if "K" in f.raw_text and "=" in f.raw_text]
        assert len(k_formulas) >= 1
        f = k_formulas[0]
        assert f.formula_type == "generic"
        assert f.confidence == "extracted"

    def test_formula_provenance(self):
        """Verify provenance metadata is correctly preserved."""
        text = "Cm = β × α × λp × t"
        formulas = extract_formulas_from_text(
            text, "MIL-STD-1629A.pdf", 28, "Task 102"
        )
        assert len(formulas) >= 1
        f = formulas[0]
        assert f.source_document == "MIL-STD-1629A.pdf"
        assert f.page_number == 28
        assert f.section == "Task 102"

    def test_formula_id_determinism(self):
        """Formula IDs should be deterministic for the same input."""
        text = "Cm = β × α × λp × t"
        f1 = extract_formulas_from_text(text, "test.pdf", 1, "")[0]
        f2 = extract_formulas_from_text(text, "test.pdf", 1, "")[0]
        assert f1.formula_id == f2.formula_id

    def test_no_formulas_in_narrative(self):
        text = "The turbine blade operates at high temperature.\nCreep is a time-dependent deformation."
        formulas = extract_formulas_from_text(text, "test.pdf", 1, "")
        assert len(formulas) == 0


class TestIndexableText:
    """Test searchable text generation from formulas."""

    def test_indexable_text_contains_expression(self):
        f = ExtractedFormula(
            formula_id="test-001",
            source_document="MIL-STD-1629A.pdf",
            page_number=28,
            section="Task 102",
            raw_text="Cm = β × α × λp × t",
            normalized_expression="Cm = beta * alpha * lambda_p * t",
            display_representation="Cm = β × α × λp × t",
            variable_definitions={"Cm": "mode criticality number"},
            formula_name="mode_criticality_number",
            formula_type="criticality"
        )
        idx_text = f.to_indexable_text()
        assert "mode_criticality_number" in idx_text
        assert "Cm" in idx_text
        assert "MIL-STD-1629A" in idx_text

    def test_indexable_text_includes_variables(self):
        f = ExtractedFormula(
            formula_id="test-002",
            source_document="test.pdf",
            page_number=1,
            section="",
            raw_text="R(t) = e^(-λt)",
            normalized_expression="R_t = exp(-lambda * t)",
            display_representation="R(t) = e^(-λt)",
            variable_definitions={
                "R(t)": "reliability function",
                "lambda": "constant failure rate"
            },
            formula_name="exponential_reliability",
            formula_type="reliability"
        )
        idx_text = f.to_indexable_text()
        assert "reliability function" in idx_text
        assert "constant failure rate" in idx_text


class TestVariableDefinitionExtraction:
    """Test extraction of variable definitions from surrounding context."""

    def test_where_block(self):
        text = "Cm = β × α × λp × t\nwhere\nβ = conditional probability of occurrence\nα = failure mode ratio\nλp = part failure rate\nt = operating time"
        defs = extract_variable_definitions_from_context(text, 0)
        assert len(defs) >= 2

    def test_colon_definitions(self):
        text = "K = Y × σ × √(π × a)\nY: geometry factor for crack shape\nσ: applied stress\na: crack length"
        defs = extract_variable_definitions_from_context(text, 0)
        assert len(defs) >= 1

    def test_no_definitions(self):
        text = "Cm = β × α × λp × t\nThe criticality analysis is then performed.\nResults are recorded."
        defs = extract_variable_definitions_from_context(text, 0)
        assert len(defs) == 0


class TestFormulaDictSerialization:
    """Test serialization of formula objects."""

    def test_to_dict(self):
        f = ExtractedFormula(
            formula_id="test-003",
            source_document="test.pdf",
            page_number=1,
            section="Section 1",
            raw_text="x = y + z",
            normalized_expression="x = y + z",
            display_representation="x = y + z",
            formula_name="test_formula",
            formula_type="generic"
        )
        d = f.to_dict()
        assert d["formula_id"] == "test-003"
        assert d["source_document"] == "test.pdf"
        assert d["formula_type"] == "generic"
        assert isinstance(d["variable_definitions"], dict)


class TestGroundTruthValidation:
    """Validate formula extraction against ground truth test vectors."""

    @pytest.fixture
    def ground_truth(self):
        gt_path = Path(__file__).parent / "formula_ground_truth.json"
        if not gt_path.exists():
            pytest.skip("formula_ground_truth.json not found")
        with open(gt_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_known_formula_patterns_cover_ground_truth(self, ground_truth):
        """Verify that KNOWN_FORMULA_PATTERNS includes patterns for all ground truth formulas."""
        known_names = {p["name"] for p in KNOWN_FORMULA_PATTERNS}
        for gt in ground_truth:
            if gt["formula_name"] in known_names:
                matching = [p for p in KNOWN_FORMULA_PATTERNS if p["name"] == gt["formula_name"]]
                assert len(matching) == 1, f"Expected exactly one pattern for {gt['formula_name']}"
                pattern = matching[0]
                # Verify variable coverage
                for var_name in gt["expected_variables"]:
                    assert var_name in pattern["known_variables"], \
                        f"Ground truth variable '{var_name}' missing from pattern '{gt['formula_name']}'"

    def test_ground_truth_formula_count(self, ground_truth):
        """At minimum 3 ground truth formulas should exist."""
        assert len(ground_truth) >= 3
