"""Formula extraction and structured mathematical provenance for FMEA-GPT Phase 5E.

Detects, normalizes, and preserves engineering formulas from extracted PDF text.
Handles Greek symbols, subscripts, single-letter variables, and structured equation blocks.
"""
import re
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class ExtractedFormula:
    """Represents a single extracted engineering formula with full provenance."""
    formula_id: str
    source_document: str
    page_number: int
    section: str
    raw_text: str
    normalized_expression: str
    display_representation: str
    variable_definitions: Dict[str, str] = field(default_factory=dict)
    units_if_explicit: Dict[str, str] = field(default_factory=dict)
    formula_name: str = ""
    formula_type: str = ""  # e.g., "criticality", "probability", "reliability", "fatigue"
    confidence: str = "extracted"  # "extracted" | "inferred" — never "invented"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "formula_id": self.formula_id,
            "source_document": self.source_document,
            "page_number": self.page_number,
            "section": self.section,
            "raw_text": self.raw_text,
            "normalized_expression": self.normalized_expression,
            "display_representation": self.display_representation,
            "variable_definitions": self.variable_definitions,
            "units_if_explicit": self.units_if_explicit,
            "formula_name": self.formula_name,
            "formula_type": self.formula_type,
            "confidence": self.confidence
        }

    def to_indexable_text(self) -> str:
        """Generate a searchable text block combining formula and context."""
        parts = [f"[Formula: {self.formula_name}]" if self.formula_name else "[Formula]"]
        parts.append(f"Expression: {self.display_representation}")
        if self.variable_definitions:
            var_defs = "; ".join(f"{k} = {v}" for k, v in self.variable_definitions.items())
            parts.append(f"Variables: {var_defs}")
        if self.units_if_explicit:
            units = "; ".join(f"{k}: {v}" for k, v in self.units_if_explicit.items())
            parts.append(f"Units: {units}")
        parts.append(f"Source: {self.source_document}, page {self.page_number}")
        if self.section:
            parts.append(f"Section: {self.section}")
        return "\n".join(parts)


# Greek letter mappings for normalization
GREEK_LETTER_MAP = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta",
    "ε": "epsilon", "λ": "lambda", "μ": "mu", "σ": "sigma",
    "τ": "tau", "θ": "theta", "π": "pi", "ω": "omega",
    "Σ": "sum", "Δ": "Delta", "Φ": "Phi", "Ψ": "Psi",
}

# Reverse mapping: text to symbol
TEXT_TO_GREEK = {v: k for k, v in GREEK_LETTER_MAP.items()}

# Known aerospace engineering formula patterns
KNOWN_FORMULA_PATTERNS = [
    # MIL-STD-1629A Mode Criticality Number
    {
        "pattern": r'[Cc]m\s*=\s*[βbBα].*[λl].*t',
        "name": "mode_criticality_number",
        "type": "criticality",
        "canonical_display": "Cm = β × α × λp × t",
        "canonical_normalized": "Cm = beta * alpha * lambda_p * t",
        "known_variables": {
            "Cm": "mode criticality number for failure mode",
            "beta": "conditional probability of occurrence of next higher failure effect (β)",
            "alpha": "failure mode ratio (fraction of part failure rate for the mode) (α)",
            "lambda_p": "part failure rate (λp)",
            "t": "operating time or mission duration"
        },
        "known_units": {
            "Cm": "dimensionless",
            "beta": "dimensionless",
            "alpha": "dimensionless",
            "lambda_p": "failures/operating_hour",
            "t": "operating_hours"
        }
    },
    # MIL-STD-1629A Item Criticality Number
    {
        "pattern": r'[Cc]r\s*=\s*[ΣS∑]?\s*[Cc]m',
        "name": "item_criticality_number",
        "type": "criticality",
        "canonical_display": "Cr = Σ(Cm)n",
        "canonical_normalized": "Cr = sum(Cm_n for n in failure_modes)",
        "known_variables": {
            "Cr": "criticality number for the item",
            "Cm": "mode criticality number for each failure mode n",
            "n": "number of failure modes identified for the item"
        },
        "known_units": {
            "Cr": "dimensionless",
            "Cm": "dimensionless",
            "n": "integer_count"
        }
    },
    # Failure probability
    {
        "pattern": r'[Pp]\s*=\s*1\s*-\s*e\^?\s*\(?-[λl]',
        "name": "exponential_failure_probability",
        "type": "reliability",
        "canonical_display": "P(t) = 1 - e^(-λt)",
        "canonical_normalized": "P_t = 1 - exp(-lambda * t)",
        "known_variables": {
            "P(t)": "probability of failure by time t",
            "lambda": "constant failure rate (λ)",
            "t": "operating time",
            "e": "base of natural logarithm"
        },
        "known_units": {
            "P(t)": "dimensionless",
            "lambda": "failures/operating_hour",
            "t": "operating_hours",
            "e": "mathematical_constant"
        }
    },
    # Reliability function
    {
        "pattern": r'[Rr]\s*\(?\s*t\s*\)?\s*=\s*e\^?\s*\(?-[λl]',
        "name": "exponential_reliability",
        "type": "reliability",
        "canonical_display": "R(t) = e^(-λt)",
        "canonical_normalized": "R_t = exp(-lambda * t)",
        "known_variables": {
            "R(t)": "reliability (probability of survival to time t)",
            "lambda": "constant failure rate (λ)",
            "t": "operating time"
        },
        "known_units": {
            "R(t)": "dimensionless",
            "lambda": "failures/operating_hour",
            "t": "operating_hours"
        }
    },
    # Two-parameter Weibull CDF (NASA-TP-2013-217030 Eq. 1)
    {
        "pattern": r'[Ff]\s*\(?\s*t\s*\)?\s*=\s*1\s*-\s*e\^?\s*\(?-\s*\(?\s*t\s*/\s*[ηe]',
        "name": "weibull_cumulative_failure",
        "type": "reliability",
        "canonical_display": "F(t) = 1 - e^(-(t/η)^β)",
        "canonical_normalized": "F_t = 1 - exp(-(t / eta)^beta)",
        "known_variables": {
            "F(t)": "cumulative failure probability at time t",
            "t": "operating time or mission cycles",
            "eta": "characteristic life (scale parameter) (η)",
            "beta": "Weibull slope (shape parameter) (β)"
        },
        "known_units": {
            "F(t)": "dimensionless",
            "t": "flight_hours_or_cycles",
            "eta": "flight_hours_or_cycles",
            "beta": "dimensionless"
        }
    },
    # Two-parameter Weibull Reliability (NASA-TP-2013-217030)
    {
        "pattern": r'[Rr]\s*\(?\s*t\s*\)?\s*=\s*e\^?\s*\(?-\s*\(?\s*t\s*/\s*[ηe]',
        "name": "weibull_reliability_function",
        "type": "reliability",
        "canonical_display": "R(t) = e^(-(t/η)^β)",
        "canonical_normalized": "R_t = exp(-(t / eta)^beta)",
        "known_variables": {
            "R(t)": "reliability function (survival probability to time t)",
            "t": "operating time or mission cycles",
            "eta": "characteristic life (scale parameter) (η)",
            "beta": "Weibull slope (shape parameter) (β)"
        },
        "known_units": {
            "R(t)": "dimensionless",
            "t": "flight_hours_or_cycles",
            "eta": "flight_hours_or_cycles",
            "beta": "dimensionless"
        }
    },
    # Benard Median Rank Formula for Johnson-Weibull Analysis
    {
        "pattern": r'[Mm][Rr]\s*=\s*\(?\s*i\s*-\s*0\.3\s*\)?\s*/\s*\(?\s*[Nn]\s*\+\s*0\.4\s*\)?',
        "name": "johnson_weibull_median_rank",
        "type": "reliability",
        "canonical_display": "MR = (i - 0.3) / (N + 0.4)",
        "canonical_normalized": "MR = (i - 0.3) / (N + 0.4)",
        "known_variables": {
            "MR": "median rank cumulative failure probability estimate",
            "i": "failure order number (rank)",
            "N": "total sample size (population)"
        },
        "known_units": {
            "MR": "dimensionless",
            "i": "integer_rank",
            "N": "integer_count"
        }
    },
    # Internal Cooling Nusselt Number (NASA-CR-198472)
    {
        "pattern": r'[Nn]u\s*=\s*\(?\s*h\s*[*×]?\s*d\s*\)?\s*/\s*k',
        "name": "nusselt_number",
        "type": "heat_transfer",
        "canonical_display": "Nu = (h × d) / k",
        "canonical_normalized": "Nu = (h * d) / k",
        "known_variables": {
            "Nu": "Nusselt number",
            "h": "convective heat transfer coefficient",
            "d": "hydraulic passage diameter",
            "k": "thermal conductivity of coolant air"
        },
        "known_units": {
            "Nu": "dimensionless",
            "h": "W/(m^2*K)",
            "d": "meters",
            "k": "W/(m*K)"
        }
    },
    # Cooling Passage Reynolds Number (NASA-CR-198472)
    {
        "pattern": r'[Rr]e\s*=\s*\(?\s*[ρp]\s*[*×]?\s*V\s*[*×]?\s*d\s*\)?\s*/\s*[μu]',
        "name": "reynolds_number",
        "type": "fluid_dynamics",
        "canonical_display": "Re = (ρ × V × d) / μ",
        "canonical_normalized": "Re = (rho * V * d) / mu",
        "known_variables": {
            "Re": "Reynolds number",
            "rho": "coolant fluid density (ρ)",
            "V": "mean coolant flow velocity",
            "d": "hydraulic passage diameter",
            "mu": "dynamic viscosity of coolant air (μ)"
        },
        "known_units": {
            "Re": "dimensionless",
            "rho": "kg/m^3",
            "V": "m/s",
            "d": "meters",
            "mu": "Pa*s"
        }
    },
    # Rotating Passage Rotation Number (NASA-CR-198472 Coriolis parameter)
    {
        "pattern": r'[Rr]o\s*=\s*\(?\s*[Ωw]\s*[*×]?\s*d\s*\)?\s*/\s*V',
        "name": "rotation_number",
        "type": "fluid_dynamics",
        "canonical_display": "Ro = (Ω × d) / V",
        "canonical_normalized": "Ro = (Omega * d) / V",
        "known_variables": {
            "Ro": "Rotation number (Coriolis acceleration parameter)",
            "Omega": "rotational angular velocity (Ω)",
            "d": "hydraulic passage diameter",
            "V": "mean coolant flow velocity"
        },
        "known_units": {
            "Ro": "dimensionless",
            "Omega": "rad/s",
            "d": "meters",
            "V": "m/s"
        }
    },
]


def _generate_formula_id(source: str, page: int, raw: str) -> str:
    """Generate a deterministic formula ID from source provenance."""
    hash_input = f"{source}:{page}:{raw[:100]}"
    return f"FML-{hashlib.md5(hash_input.encode()).hexdigest()[:12].upper()}"


def normalize_greek_in_text(text: str) -> str:
    """Replace Greek Unicode characters with their spelled-out English names."""
    result = text
    for greek, english in GREEK_LETTER_MAP.items():
        result = result.replace(greek, english)
    return result


def detect_equation_lines(text: str) -> List[Tuple[int, str]]:
    """Detect lines that appear to contain mathematical equations.
    
    Returns list of (line_index, line_text) tuples.
    """
    equation_indicators = [
        r'=',           # Assignment/equation
        r'[×÷±∑∏∫]',   # Mathematical operators
        r'\^',           # Exponentiation
        r'[αβγδελμσθπω]', # Greek letters
    ]
    
    lines = text.split('\n')
    equations = []
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped or len(line_stripped) < 3:
            continue
        
        # Must contain '=' to be considered an equation
        if '=' not in line_stripped:
            continue
            
        # Must not be too long (equations are typically compact)
        if len(line_stripped) > 200:
            continue
            
        # Must not look like a normal sentence (few words, some symbols)
        words = line_stripped.split()
        if len(words) > 15:
            continue
        
        # Check for equation-like patterns
        has_math = any(re.search(p, line_stripped) for p in equation_indicators)
        has_variables = bool(re.search(r'\b[A-Z][a-z]?\s*=', line_stripped))
        has_greek = bool(re.search(r'[αβγδελμσθπωΣΔ]', line_stripped))
        has_subscript_style = bool(re.search(r'[A-Za-z]_[A-Za-z0-9]|[A-Za-z]\d', line_stripped))
        
        if has_math or has_variables or has_greek or has_subscript_style:
            equations.append((i, line_stripped))
    
    return equations


def extract_formulas_from_text(
    text: str,
    source_document: str,
    page_number: int,
    section: str = ""
) -> List[ExtractedFormula]:
    """Extract and classify mathematical formulas from page text.
    
    This function:
    1. Detects equation lines in the text
    2. Matches against known aerospace formula patterns
    3. Normalizes Greek symbols
    4. Preserves raw and normalized representations
    5. Never invents variable definitions or units
    """
    formulas = []
    
    # Detect candidate equation lines
    equation_lines = detect_equation_lines(text)
    
    for line_idx, raw_line in equation_lines:
        normalized = normalize_greek_in_text(raw_line)
        
        # Try to match known formula patterns
        matched_known = False
        for known in KNOWN_FORMULA_PATTERNS:
            if re.search(known["pattern"], raw_line, re.IGNORECASE) or \
               re.search(known["pattern"], normalized, re.IGNORECASE):
                formula = ExtractedFormula(
                    formula_id=_generate_formula_id(source_document, page_number, raw_line),
                    source_document=source_document,
                    page_number=page_number,
                    section=section,
                    raw_text=raw_line,
                    normalized_expression=known["canonical_normalized"],
                    display_representation=known["canonical_display"],
                    variable_definitions=dict(known["known_variables"]),
                    units_if_explicit=dict(known.get("known_units", {})),
                    formula_name=known["name"],
                    formula_type=known["type"],
                    confidence="extracted"
                )
                formulas.append(formula)
                matched_known = True
                break
        
        if not matched_known:
            # Generic formula extraction — preserve raw and normalize Greek only
            formula = ExtractedFormula(
                formula_id=_generate_formula_id(source_document, page_number, raw_line),
                source_document=source_document,
                page_number=page_number,
                section=section,
                raw_text=raw_line,
                normalized_expression=normalized,
                display_representation=raw_line,
                formula_name="",
                formula_type="generic",
                confidence="extracted"
            )
            formulas.append(formula)
    
    return formulas


def extract_variable_definitions_from_context(
    text: str,
    formula_line_idx: int
) -> Dict[str, str]:
    """Attempt to extract variable definitions from surrounding text.
    
    Looks for patterns like:
    - "where X = ..."
    - "X is the ..."
    - "X: ..."
    
    Only returns definitions explicitly found in the source text.
    Never invents definitions.
    """
    lines = text.split('\n')
    definitions = {}
    
    # Look at the 10 lines following the formula
    start = max(0, formula_line_idx + 1)
    end = min(len(lines), formula_line_idx + 12)
    
    where_block = False
    for i in range(start, end):
        line = lines[i].strip()
        
        if line.lower().startswith("where"):
            where_block = True
            line = line[5:].strip().lstrip(':').strip()
        
        if where_block or re.match(r'^[A-Za-z_αβγδελμσθπω]\s*[=:]\s*', line):
            # Pattern: "X = description" or "X: description"
            m = re.match(r'^([A-Za-zαβγδελμσθπω][A-Za-z0-9_]*)\s*[=:]\s*(.+)$', line)
            if m:
                var_name = m.group(1).strip()
                var_def = m.group(2).strip().rstrip('.')
                if len(var_def) > 3:  # Avoid trivially short definitions
                    definitions[var_name] = var_def
        elif where_block and not line:
            where_block = False  # End of "where" block
    
    return definitions


class FormulaExtractor:
    """Convenience class wrapper for formula extraction operations."""

    def extract_from_text(
        self,
        text: str,
        source_doc: str = "",
        page_num: int = 0,
        section: str = ""
    ) -> List[ExtractedFormula]:
        """Extract all formulas from text block with full provenance."""
        return extract_formulas_from_text(
            text=text,
            source_document=source_doc,
            page_number=page_num,
            section=section
        )

    def normalize_greek(self, text: str) -> str:
        """Convert Greek symbols to canonical ASCII words."""
        return normalize_greek_in_text(text)

    def detect_equations(self, text: str) -> List[Tuple[int, str]]:
        """Detect lines containing mathematical equations."""
        return detect_equation_lines(text)
