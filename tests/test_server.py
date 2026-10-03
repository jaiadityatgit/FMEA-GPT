"""Unit and integration tests for FMEA-GPT FastAPI backend."""
import sys
import unittest
from pathlib import Path
from starlette.testclient import TestClient

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.server.main import app


class TestFastAPIServer(unittest.TestCase):
    """Integration test suite for the FastAPI REST API."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("vector_store", data)
        self.assertIn("MIL-STD-1629A", data["compliance"])

    def test_sample_fmea_endpoint(self):
        resp = self.client.get("/api/fmea/sample")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("component", data)
        self.assertIn("failure_modes", data)
        self.assertGreaterEqual(len(data["failure_modes"]), 4)

    def test_generate_fmea_endpoint(self):
        payload = {
            "component_name": "High Pressure Turbine Blade",
            "part_number": "301-789-204-0"
        }
        resp = self.client.post("/api/fmea/generate", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["component"]["part_number"], "301-789-204-0")
        self.assertTrue(data["validation"]["is_compliant"])

    def test_export_excel_endpoint(self):
        # Fetch sample report first
        sample = self.client.get("/api/fmea/sample").json()
        resp = self.client.post("/api/fmea/export/excel", json=sample)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["content-type"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.assertGreater(len(resp.content), 2000)

    def test_export_pdf_endpoint(self):
        sample = self.client.get("/api/fmea/sample").json()
        resp = self.client.post("/api/fmea/export/pdf", json=sample)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["content-type"], "application/pdf")
        self.assertGreater(len(resp.content), 2000)

    def test_export_digital_twin_endpoint(self):
        sample = self.client.get("/api/fmea/sample").json()
        resp = self.client.post("/api/fmea/export/digital-twin", json=sample)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["digital_twin_schema_version"], "1.0.0")
        self.assertIn("degradation_models", data)

    def test_rag_search_endpoint(self):
        resp = self.client.get("/api/rag/search", params={"query": "MIL-STD-1629A severity", "top_k": 2})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["top_k"], 2)
        self.assertGreaterEqual(len(data["results"]), 1)

    def test_rag_sources_endpoint(self):
        resp = self.client.get("/api/rag/sources")
        self.assertEqual(resp.status_code, 200)
        sources = resp.json()
        self.assertGreaterEqual(len(sources), 10)


if __name__ == "__main__":
    unittest.main()
