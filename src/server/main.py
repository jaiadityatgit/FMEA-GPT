"""FastAPI backend application for FMEA-GPT."""
import io
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ..rag.config import RAGConfig
from ..rag.retriever import AerospaceRetriever
from ..agents.graph import FMEAGeneratorGraph
from ..agents.state import FMEAReport
from ..agents.exporters.fmea_table import format_mil_std_1629a_markdown
from ..agents.exporters.digital_twin import export_digital_twin_json
from ..agents.exporters.cil_exporter import format_critical_items_list_markdown
from .exporters_binary import generate_fmea_excel, generate_fmea_pdf

app = FastAPI(
    title="FMEA-GPT Aerospace API",
    description="Automated standards-compliant Failure Mode and Effects Analysis for aerospace systems.",
    version="1.0.0"
)

# CORS middleware for development and frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine singletons
config = RAGConfig.get_production_config()
retriever = AerospaceRetriever(config=config)
generator = FMEAGeneratorGraph(retriever=retriever, config=config)


class GenerateRequest(BaseModel):
    component_name: str = Field(..., description="Name or description of the component")
    part_number: Optional[str] = Field(default=None, description="Optional Part Number")
    operating_notes: Optional[str] = Field(default=None, description="Optional operating envelope or mission notes")


@app.get("/api/health")
def get_health() -> Dict[str, Any]:
    """Check system health, vector database status, and active provider."""
    stats = retriever.vector_store.get_stats()
    return {
        "status": "healthy",
        "system": "FMEA-GPT Aerospace Engine",
        "compliance": ["MIL-STD-1629A", "FAA AC 33.75-1A", "EASA CS-E 510", "NASA-STD-8729.1A"],
        "vector_store": stats,
        "active_provider": generator.provider.provider_name
    }


@app.get("/api/fmea/sample")
def get_sample_fmea() -> Dict[str, Any]:
    """Retrieve pre-computed CFM56 turbine blade FMEA for instantaneous demo load."""
    for trace_name in ["fresh_hpt_trace.json", "hpt_core_final_trace.json"]:
        sample_file = Path("data/output") / trace_name
        if sample_file.exists():
            with open(sample_file, "r", encoding="utf-8") as f:
                return json.load(f)
    report = generator.run("CFM56 High Pressure Turbine Stage 1 Rotor Blade", target_part_number="301-789-204-0")
    return report.model_dump()


@app.post("/api/fmea/generate")
def generate_fmea(req: GenerateRequest) -> Dict[str, Any]:
    """Execute multi-agent LangGraph workflow to generate full FMEA."""
    if not req.component_name.strip():
        raise HTTPException(status_code=400, detail="Component name cannot be empty.")

    try:
        report = generator.run(
            component_input=req.component_name.strip(),
            target_part_number=req.part_number,
            operating_notes=req.operating_notes
        )
        return report.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FMEA Generation error: {str(e)}")


@app.post("/api/fmea/export/excel")
def export_excel(report_data: Dict[str, Any]):
    """Generate and download formatted MIL-STD-1629A Excel file."""
    try:
        report = FMEAReport.model_validate(report_data)
        excel_stream = generate_fmea_excel(report)
        filename = f"FMEA_{report.component.part_number or 'MIL-STD-1629A'}.xlsx"
        return StreamingResponse(
            excel_stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate Excel: {str(e)}")


@app.post("/api/fmea/export/pdf")
def export_pdf(report_data: Dict[str, Any]):
    """Generate and download formatted MIL-STD-1629A PDF file."""
    try:
        report = FMEAReport.model_validate(report_data)
        pdf_stream = generate_fmea_pdf(report)
        filename = f"FMEA_{report.component.part_number or 'MIL-STD-1629A'}.pdf"
        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate PDF: {str(e)}")


@app.post("/api/fmea/export/digital-twin")
def export_digital_twin(report_data: Dict[str, Any]):
    """Format and return Digital Twin telemetry JSON."""
    try:
        report = FMEAReport.model_validate(report_data)
        dt_json_str = export_digital_twin_json(report)
        return JSONResponse(content=json.loads(dt_json_str))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to format Digital Twin: {str(e)}")


@app.post("/api/fmea/export/cil")
def export_cil(report_data: Dict[str, Any]):
    """Return Critical Items List Markdown report."""
    try:
        report = FMEAReport.model_validate(report_data)
        cil_md = format_critical_items_list_markdown(report)
        return {"markdown": cil_md}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate CIL: {str(e)}")


@app.get("/api/rag/search")
def search_rag(
    query: str = Query(..., description="Search query string"),
    top_k: int = Query(5, ge=1, le=20),
    publisher: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Perform real-time semantic retrieval against aerospace knowledge base."""
    results = retriever.retrieve(query=query, top_k=top_k, publisher=publisher)
    return {
        "query": query,
        "top_k": top_k,
        "count": len(results),
        "results": [r.to_dict() for r in results]
    }


@app.get("/api/rag/sources")
def get_sources_catalog() -> List[Dict[str, Any]]:
    """Return catalog of authoritative aerospace sources."""
    sources_path = config.metadata_file
    if sources_path.exists():
        with open(sources_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


# Mount frontend static directory if exists
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
