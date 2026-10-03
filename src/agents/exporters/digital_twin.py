"""Digital Twin JSON export format for aerospace health monitoring systems."""
import json
from typing import Dict, Any
from ..state import FMEAReport


def export_digital_twin_json(report: FMEAReport, indent: int = 2) -> str:
    """Format FMEA into structured Digital Twin schema for predictive maintenance ingestion."""
    comp = report.component
    payload: Dict[str, Any] = {
        "digital_twin_schema_version": "1.0.0",
        "asset_metadata": {
            "component_name": comp.component_name,
            "part_number": comp.part_number,
            "system": comp.system,
            "subsystem": comp.subsystem,
            "regulatory_airworthiness_tier": comp.regulatory_class,
            "operating_limits": {
                "max_operating_temperature_celsius": 1400 if "turbine" in comp.subsystem.lower() else 350,
                "nominal_rpm": 14500 if "rotor" in comp.component_name.lower() or "turbine" in comp.component_name.lower() else 0
            }
        },
        "degradation_models": [],
        "prognostic_rules": {
            "rpn_alert_threshold": 100,
            "single_point_failure_interlock": True
        }
    }

    for fm in report.failure_modes:
        # Map failure mode to telemetry signatures
        sensor_signatures = []
        if "tmf" in fm.failure_mode.lower() or "thermal" in fm.failure_mode.lower():
            sensor_signatures = ["EGT_trend_divergence", "HPT_cooling_differential_pressure"]
        elif "creep" in fm.failure_mode.lower():
            sensor_signatures = ["shaft_vibration_N2_harmonic", "blade_tip_clearance_proximity"]
        elif "blockage" in fm.failure_mode.lower():
            sensor_signatures = ["P25_to_P3_pressure_ratio", "interstage_turbine_temperature"]
        elif "fretting" in fm.failure_mode.lower():
            sensor_signatures = ["accelerometer_bearing_4_peak_radial"]
        else:
            sensor_signatures = ["vibration_broadband", "temperature_margin"]

        model_entry = {
            "fault_code": fm.mode_id,
            "failure_mode_title": fm.failure_mode,
            "physical_mechanism": fm.root_cause,
            "risk_metrics": {
                "severity_index": fm.severity,
                "occurrence_probability_rank": fm.occurrence,
                "detection_difficulty": fm.detection,
                "rpn": fm.rpn,
                "criticality_level": fm.mil_std_severity_category,
                "is_single_point_failure": fm.single_point_failure
            },
            "telemetry_indicators": sensor_signatures,
            "mitigation_protocol": {
                "inspection_method": fm.detection_method,
                "action": fm.recommended_action,
                "scheduled_interval": fm.inspection_interval,
                "regulatory_baseline": fm.compliance_reference
            },
            "provenance": [
                {
                    "document": c.source_document,
                    "page": c.page_number,
                    "relevance": round(c.similarity_score, 3)
                } for c in fm.citations
            ]
        }
        payload["degradation_models"].append(model_entry)

    return json.dumps(payload, indent=indent)
