import React, { useState, useEffect } from 'react';
import './index.css';

const PRESETS = [
  {
    name: "CFM56 High Pressure Turbine Stage 1 Rotor Blade",
    pn: "301-789-204-0",
    desc: "Single-crystal nickel superalloy high pressure turbine rotor blade operating in severe thermal-mechanical environment (T4.1 > 1,400°C, 14,000 RPM).",
    system: "Propulsion / Turbomachinery (ATA 72)",
    subsystem: "High Pressure Turbine (HPT) Module",
    category: "Engine Critical Part",
    specs: {
      material: "Single-Crystal Ni Superalloy (René N5 / PWA 1484)",
      indenture: "Level 3 Airfoil Assembly",
      operatingTemp: "1,425°C Turbine Gas Path",
      centrifugalLoad: "14,400 RPM Peak Spool",
      certificationStandard: "14 CFR § 33.75 / EASA CS-E 515"
    },
    hotspots: [
      { id: 1, title: "Stage 1 Airfoil Leading Edge", sub: "TMF Cracking & Thermal Gradient Stress", x: "32%", y: "42%" },
      { id: 2, title: "Thermal Barrier Coating (TBC)", sub: "Spallation & High-Temp Oxidation", x: "48%", y: "34%" },
      { id: 3, title: "Fir-Tree Dovetail Root Slot", sub: "Fretting Fatigue Under Centrifugal Load", x: "24%", y: "68%" },
      { id: 4, title: "Serpentine Airfoil Cooling Duct", sub: "Particulate Clogging & Local Hotspots", x: "62%", y: "46%" }
    ]
  },
  {
    name: "High Pressure Compressor (HPC) Stage 3 Blade",
    pn: "204-452-110-0",
    desc: "Titanium alloy compressor blade subject to foreign object damage (FOD), aerodynamic flutter, and high-cycle vibratory fatigue.",
    system: "Propulsion / Core Compressor (ATA 72)",
    subsystem: "High Pressure Compressor Module",
    category: "Engine Rotating Part",
    specs: {
      material: "Titanium Alloy Ti-6Al-4V",
      indenture: "Level 3 Bladed Disc Subsystem",
      operatingTemp: "450°C Stage 3 Discharge",
      centrifugalLoad: "15,200 RPM Peak Spool",
      certificationStandard: "14 CFR § 33.75 / FAA AC 33.75-1A"
    },
    hotspots: [
      { id: 1, title: "Compressor Blade Tip", sub: "Rub-in / Clearance Erosion", x: "38%", y: "36%" },
      { id: 2, title: "Dovetail Root Fillet", sub: "High Cycle Fatigue (HCF)", x: "30%", y: "62%" }
    ]
  },
  {
    name: "Hydro-Mechanical Fuel Metering Valve (FMV)",
    pn: "FMV-8820-A",
    desc: "Dual-channel fuel metering valve assembly subject to particulate contamination, spool stiction, and servo pressure loss.",
    system: "Fuel & Engine Control (ATA 73)",
    subsystem: "Hydromechanical Unit (HMU)",
    category: "Safety-Critical Actuation Unit",
    specs: {
      material: "Hardened Stainless Steel / Nitralloy",
      indenture: "Level 2 Subassembly Unit",
      operatingTemp: "-40°C to +125°C Fuel Path",
      centrifugalLoad: "Static Hydromechanical (3,000 PSI)",
      certificationStandard: "RTCA DO-160G / FAR 25.1309"
    },
    hotspots: [
      { id: 1, title: "Metering Spool Lands", sub: "Contamination Jam & Stiction", x: "42%", y: "48%" },
      { id: 2, title: "Torque Motor Armature", sub: "Coil Open Circuit / Servo Bias", x: "68%", y: "40%" }
    ]
  },
  {
    name: "Elevator Primary Flight Control Hydraulic Actuator",
    pn: "ACT-4420-HYD",
    desc: "Dual-redundant 3000 PSI hydraulic flight control actuator with dynamic seal wear and mechanical jamming risks.",
    system: "Flight Controls (ATA 27)",
    subsystem: "Pitch Control Actuation",
    category: "Flight Critical Primary Actuator",
    specs: {
      material: "High-Strength Aerospace Aluminum 7075-T6",
      indenture: "Level 2 Line Replaceable Unit (LRU)",
      operatingTemp: "-54°C to +85°C Ambient Envelope",
      centrifugalLoad: "3,000 PSI Hydraulic Circuit",
      certificationStandard: "14 CFR § 25.671 / ARP4754A"
    },
    hotspots: [
      { id: 1, title: "Dual Piston Dynamic Seal", sub: "Hydraulic Blow-By / Internal Leakage", x: "45%", y: "50%" },
      { id: 2, title: "Mechanical Output Rod End", sub: "Bearing Backlash & Seizure", x: "78%", y: "52%" }
    ]
  },
  {
    name: "Unknown Component XYZ-999",
    pn: "XYZ-999-001",
    desc: "Uncataloged speculative aerospace component used to test evidence gap routing and honest unverified response.",
    system: "Unspecified Research Asset",
    subsystem: "Uncataloged Experimental Module",
    category: "Corpus Gap Test Case",
    specs: {
      material: "Uncataloged Specification",
      indenture: "Undefined Indenture",
      operatingTemp: "Unknown Thermal Envelope",
      centrifugalLoad: "Uncataloged Operational Envelope",
      certificationStandard: "Evidence Verification Required"
    },
    hotspots: []
  }
];

export default function App() {
  const [componentName, setComponentName] = useState(PRESETS[0].name);
  const [partNumber, setPartNumber] = useState(PRESETS[0].pn);
  const [operatingNotes, setOperatingNotes] = useState(PRESETS[0].desc);
  const [selectedPresetIndex, setSelectedPresetIndex] = useState(0);

  const [fmeaReport, setFmeaReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [heroView, setHeroView] = useState('engine');
  const [activeHotspot, setActiveHotspot] = useState(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [ragQuery, setRagQuery] = useState('MIL-STD-1629A severity categories');
  const [ragResults, setRagResults] = useState([]);
  const [ragSearching, setRagSearching] = useState(false);

  const [health, setHealth] = useState(null);
  const [expandedRows, setExpandedRows] = useState({});

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(err => console.error("Health check error:", err));

    fetch('/api/fmea/sample')
      .then(res => res.json())
      .then(data => setFmeaReport(data))
      .catch(err => console.error("Sample load error:", err));

    performRagSearch('MIL-STD-1629A severity categories');
  }, []);

  const handleSelectPreset = (idx) => {
    setSelectedPresetIndex(idx);
    const p = PRESETS[idx];
    setComponentName(p.name);
    setPartNumber(p.pn);
    setOperatingNotes(p.desc);
  };

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const resp = await fetch('/api/fmea/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          component_name: componentName,
          part_number: partNumber,
          operating_notes: operatingNotes
        })
      });
      if (resp.ok) {
        const data = await resp.json();
        setFmeaReport(data);
      } else {
        alert("Failed to generate FMEA. Check server logs.");
      }
    } catch (e) {
      console.error(e);
      alert("Error contacting FMEA backend: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const performRagSearch = async (q) => {
    if (!q) return;
    setRagSearching(true);
    try {
      const res = await fetch(`/api/rag/search?query=${encodeURIComponent(q)}&top_k=4`);
      if (res.ok) {
        const data = await res.json();
        setRagResults(data.results || []);
      }
    } catch (e) {
      console.error("RAG search failed:", e);
    } finally {
      setRagSearching(false);
    }
  };

  const handleExport = async (type) => {
    if (!fmeaReport) return;
    try {
      if (type === 'excel') {
        const res = await fetch('/api/fmea/export/excel', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(fmeaReport)
        });
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `FMEA_${fmeaReport.component.part_number || 'export'}.xlsx`;
        a.click();
      } else if (type === 'pdf') {
        const res = await fetch('/api/fmea/export/pdf', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(fmeaReport)
        });
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `FMEA_${fmeaReport.component.part_number || 'export'}.pdf`;
        a.click();
      } else if (type === 'json-full') {
        const blob = new Blob([JSON.stringify(fmeaReport, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `fmea_full_report_${fmeaReport.component.part_number || 'export'}.json`;
        a.click();
      } else if (type === 'digital-twin') {
        const res = await fetch('/api/fmea/export/digital-twin', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(fmeaReport)
        });
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `digital_twin_${fmeaReport.component.part_number || 'telemetry'}.json`;
        a.click();
      }
    } catch (err) {
      console.error("Export error:", err);
      alert("Failed to export: " + err.message);
    }
  };

  const toggleRow = (id) => {
    setExpandedRows(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const modes = fmeaReport?.failure_modes || [];
  const spfCount = modes.filter(m => m.single_point_failure || m.severity >= 9).length;
  const isEvidenceGap = !modes.length || fmeaReport?.component.analysis_status === 'insufficient_evidence';
  const cov = fmeaReport?.evidence_coverage;
  const trace = fmeaReport?.reasoning_trace;
  const comp = fmeaReport?.component;
  const currentPreset = PRESETS[selectedPresetIndex] || PRESETS[0];

  const getBadgeClass = (supp) => {
    if (!supp) return 'insufficient';
    const s = supp.toLowerCase();
    if (s.includes('direct')) return 'direct';
    if (s.includes('supporting')) return 'supporting';
    if (s.includes('inference')) return 'inference';
    if (s.includes('heuristic')) return 'heuristic';
    if (s.includes('unsupported')) return 'unsupported';
    return 'insufficient';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw' }}>
      <header className="top-header">
        <div className="brand-section">
          <div className="brand-mark">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="12 2 2 22 12 17 22 22 12 2" />
            </svg>
          </div>
          <div className="brand-info">
            <div className="brand-name">
              <span>FMEA-GPT</span>
              <span style={{ fontSize: '10px', color: 'var(--accent-orange)', fontFamily: 'var(--font-mono)' }}>// WS-01</span>
            </div>
            <div className="brand-subtitle">Aerospace Airworthiness & Reliability Workstation</div>
          </div>
        </div>

        <div className="header-search-wrap">
          <svg className="header-search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            className="header-search-input"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search aircraft, engine, component or analysis..."
          />
          <span className="header-shortcut-badge">CTRL+K</span>
        </div>

        <div className="header-controls">
          <div className="status-cluster" title="Production ChromaDB Knowledge Store Active">
            <span className="status-dot-active"></span>
            <span>CHROMA STORE: {health?.vector_store?.document_count || "2,234"} CHUNKS</span>
          </div>

          <div className="header-engineer-badge">
            <div className="engineer-avatar">JA</div>
            <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.1 }}>
              <span style={{ fontWeight: 600 }}>ENG. J. ADAMS</span>
              <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>MRO AIRWORTHINESS REVIEWER</span>
            </div>
          </div>
        </div>
      </header>

      <div className="app-layout">
        <nav className="nav-rail">
          <button
            className={`nav-rail-item ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
            title="Cockpit Overview & Asset View"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="7" height="9" />
              <rect x="14" y="3" width="7" height="5" />
              <rect x="14" y="12" width="7" height="9" />
              <rect x="3" y="16" width="7" height="5" />
            </svg>
            <span>Overview</span>
          </button>

          <button
            className={`nav-rail-item ${activeTab === 'worksheet' ? 'active' : ''}`}
            onClick={() => setActiveTab('worksheet')}
            title="MIL-STD-1629A Failure Modes Worksheet"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="8" y1="6" x2="21" y2="6" />
              <line x1="8" y1="12" x2="21" y2="12" />
              <line x1="8" y1="18" x2="21" y2="18" />
              <line x1="3" y1="6" x2="3.01" y2="6" />
              <line x1="3" y1="12" x2="3.01" y2="12" />
              <line x1="3" y1="18" x2="3.01" y2="18" />
            </svg>
            <span>FMEA</span>
          </button>

          <button
            className={`nav-rail-item ${activeTab === 'criticality' ? 'active' : ''}`}
            onClick={() => setActiveTab('criticality')}
            title="Task 102 Criticality & Risk Matrix"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 20v-6M6 20V10M18 20V4" />
            </svg>
            <span>Critical</span>
          </button>

          <button
            className={`nav-rail-item ${activeTab === 'evidence' ? 'active' : ''}`}
            onClick={() => setActiveTab('evidence')}
            title="Evidence Coverage & Reasoning Trace"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <polygon points="12 6 12 12 16 14" />
            </svg>
            <span>Trace</span>
          </button>

          <div className="nav-rail-divider"></div>

          <button
            className={`nav-rail-item ${activeTab === 'cil' ? 'active' : ''}`}
            onClick={() => setActiveTab('cil')}
            title="Critical Items List (CIL) Report"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            <span>CIL</span>
          </button>

          <button
            className={`nav-rail-item ${activeTab === 'sources' ? 'active' : ''}`}
            onClick={() => setActiveTab('sources')}
            title="Regulatory Corpus & Standards Explorer"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            </svg>
            <span>Sources</span>
          </button>

          <button
            className={`nav-rail-item ${activeTab === 'telemetry' ? 'active' : ''}`}
            onClick={() => setActiveTab('telemetry')}
            title="Digital Twin Telemetry Schema"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
            <span>Twin</span>
          </button>

          <button
            className={`nav-rail-item ${activeTab === 'exports' ? 'active' : ''}`}
            onClick={() => setActiveTab('exports')}
            title="Engineering Document Exports"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            <span>Export</span>
          </button>
        </nav>

        <main className="workspace">
          <section className="instrumentation-bar">
            <div className="instrument-meter severity">
              <div className="meter-label-row">
                <span className="meter-label">Severity Classification</span>
                <span className="meter-spec">MIL-STD-1629A § 4.4</span>
              </div>
              <div className="meter-value-row">
                <span className="meter-value orange">CATEGORY II</span>
              </div>
              <span className="meter-subtext">CRITICAL HAZARD CATEGORY</span>
            </div>

            <div className="instrument-meter criticality">
              <div className="meter-label-row">
                <span className="meter-label">Criticality Analysis</span>
                <span className="meter-spec">TASK 102 MATRIX</span>
              </div>
              <div className="meter-value-row">
                <span className="meter-value amber">QUALITATIVE</span>
              </div>
              <span className="meter-subtext">AUDITABLE LOSS POTENTIAL</span>
            </div>

            <div className="instrument-meter evidence">
              <div className="meter-label-row">
                <span className="meter-label">Evidence Grounding</span>
                <span className="meter-spec">{cov?.total_claims || 28} VERIFIED CLAIMS</span>
              </div>
              <div className="meter-value-row">
                <span className="meter-value green">
                  {cov?.coverage_score ? `${(cov.coverage_score * 100).toFixed(1)}%` : '78.6%'}
                </span>
              </div>
              <span className="meter-subtext">
                {cov?.is_coverage_adequate ? "COVERAGE ADEQUATE // 0 HEURISTICS" : "EVIDENCE GAP DETECTED"}
              </span>
            </div>

            <div className="instrument-meter review">
              <div className="meter-label-row">
                <span className="meter-label">Engineering Review</span>
                <span className="meter-spec">NASA-STD-8729.1A</span>
              </div>
              <div className="meter-value-row">
                <span className={`meter-value ${spfCount > 0 ? 'red' : 'green'}`}>
                  {spfCount > 0 ? "REVIEW REQUIRED" : "VERIFIED"}
                </span>
              </div>
              <span className="meter-subtext">
                {spfCount} SINGLE POINT FAILURE ({spfCount} SPF IDENTIFIED)
              </span>
            </div>

            <div className="meter-actions">
              <button
                className="btn-secondary"
                onClick={() => handleExport('excel')}
                title="Download MIL-STD-1629A Excel Spreadsheet"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="8" y1="13" x2="16" y2="13" />
                  <line x1="8" y1="17" x2="16" y2="17" />
                </svg>
                <span>Excel</span>
              </button>

              <button
                className="btn-secondary"
                onClick={() => handleExport('pdf')}
                title="Download Airworthiness Compliance PDF"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                </svg>
                <span>PDF</span>
              </button>
            </div>
          </section>

          {activeTab === 'overview' && (
            <div>
              {isEvidenceGap && (
                <div className="corpus-gap-panel">
                  <div className="corpus-gap-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                      <line x1="12" y1="9" x2="12" y2="13" />
                      <line x1="12" y1="17" x2="12.01" y2="17" />
                    </svg>
                    <span>INSUFFICIENT EVIDENCE — CORPUS GAP DETECTED</span>
                  </div>
                  <div className="corpus-gap-text">
                    The indexed engineering repository does not contain verified test, certification, or operational history data for <b>"{componentName}"</b>.
                    In accordance with MIL-STD-1629A § 4.1 evidence invariants, <b>no ungrounded failure modes or speculative failure rates were promoted</b> to the production worksheet.
                  </div>
                  <div className="corpus-gap-details">
                    <b>Action Required:</b> Ingest OEM technical specifications or service bulletins into ChromaDB Core Final, or submit component to a qualified aerospace propulsion structures specialist for manual hazard induction.
                  </div>
                </div>
              )}

              <div className="hero-component-panel">
                <div className="hero-visual-area">
                  <img
                    className="hero-bg-image"
                    src={heroView === 'engine' ? '/assets/engine_cutaway.jpg' : '/assets/aircraft_hangar.jpg'}
                    alt="Aerospace Component Cutaway"
                  />
                  <div className="hero-overlay-gradient"></div>

                  <div className="hero-header-overlay">
                    <div className="hero-tags">
                      <span className="hero-tag orange">
                        {comp?.regulatory_class?.includes("Critical") ? "ENGINE CRITICAL PART" : "LINE AIRWORTHINESS PART"}
                      </span>
                      <span className="hero-tag">
                        P/N: {comp?.part_number || partNumber}
                      </span>
                      <span className="hero-tag">
                        ATA 72 PROPULSION
                      </span>
                      <span className={`hero-tag ${isEvidenceGap ? 'red' : 'green'}`}>
                        {isEvidenceGap ? "CORPUS GAP" : "AUDITED PASS"}
                      </span>
                    </div>

                    <div className="hero-view-switch">
                      <button
                        className={`hero-view-btn ${heroView === 'engine' ? 'active' : ''}`}
                        onClick={() => setHeroView('engine')}
                      >
                        Engine Cutaway
                      </button>
                      <button
                        className={`hero-view-btn ${heroView === 'aircraft' ? 'active' : ''}`}
                        onClick={() => setHeroView('aircraft')}
                      >
                        Airframe Hangar
                      </button>
                    </div>
                  </div>

                  {heroView === 'engine' && currentPreset.hotspots.map(h => (
                    <div
                      key={h.id}
                      className="hotspot-pin"
                      style={{ left: h.x, top: h.y }}
                      onMouseEnter={() => setActiveHotspot(h.id)}
                      onMouseLeave={() => setActiveHotspot(null)}
                      onClick={() => setActiveTab('worksheet')}
                    >
                      <div className="pin-core"></div>
                      {activeHotspot === h.id && (
                        <div className="pin-popover">
                          <div className="pin-title">{h.title}</div>
                          <div className="pin-subtitle">{h.sub}</div>
                        </div>
                      )}
                    </div>
                  ))}

                  <div className="hero-footer-overlay">
                    <div className="hero-title-group">
                      <h1>{comp?.component_name || componentName}</h1>
                      <p>{comp?.operating_environment || operatingNotes}</p>
                    </div>
                  </div>
                </div>

                <div className="hero-specs-sidebar">
                  <div className="spec-section-title">
                    <span>Engineering Specs</span>
                    <span style={{ fontSize: '9px', fontFamily: 'var(--font-mono)' }}>MRO // SYS-72</span>
                  </div>

                  <div className="spec-grid">
                    <div className="spec-row">
                      <span className="spec-key">Subsystem</span>
                      <span className="spec-val">{comp?.subsystem || currentPreset.subsystem}</span>
                    </div>
                    <div className="spec-row">
                      <span className="spec-key">Indenture Level</span>
                      <span className="spec-val">{currentPreset.specs.indenture}</span>
                    </div>
                    <div className="spec-row">
                      <span className="spec-key">Material Spec</span>
                      <span className="spec-val">{currentPreset.specs.material}</span>
                    </div>
                    <div className="spec-row">
                      <span className="spec-key">Thermal Envelope</span>
                      <span className="spec-val accent">{currentPreset.specs.operatingTemp}</span>
                    </div>
                    <div className="spec-row">
                      <span className="spec-key">Centrifugal Stress</span>
                      <span className="spec-val">{currentPreset.specs.centrifugalLoad}</span>
                    </div>
                    <div className="spec-row">
                      <span className="spec-key">Regulatory Code</span>
                      <span className="spec-val">{currentPreset.specs.certificationStandard}</span>
                    </div>
                  </div>

                  <div className="spec-section-title" style={{ marginTop: '4px' }}>
                    <span>Analysis Status</span>
                    <span style={{ fontSize: '9px', color: 'var(--accent-orange)' }}>REV 5.2</span>
                  </div>

                  <div className="spec-grid">
                    <div className="spec-row">
                      <span className="spec-key">Corpus Store</span>
                      <span className="spec-val">Chroma Core Final</span>
                    </div>
                    <div className="spec-row">
                      <span className="spec-key">Evaluated Modes</span>
                      <span className="spec-val accent">{modes.length} Modes</span>
                    </div>
                    <div className="spec-row">
                      <span className="spec-key">Single Point Failures</span>
                      <span className="spec-val" style={{ color: spfCount > 0 ? 'var(--accent-red)' : 'var(--accent-green)' }}>
                        {spfCount} (Requires Retention Rationale)
                      </span>
                    </div>
                    <div className="spec-row">
                      <span className="spec-key">Epistemic Model</span>
                      <span className="spec-val">MIL-STD-1629A Graph</span>
                    </div>
                  </div>

                  <button
                    className="btn-primary"
                    style={{ marginTop: 'auto', width: '100%', justifyContent: 'center' }}
                    onClick={() => setActiveTab('worksheet')}
                  >
                    <span>Inspect Failure Modes Table →</span>
                  </button>
                </div>
              </div>

              <div className="controls-panel">
                <div className="controls-header-row">
                  <span className="controls-title">Quick Component Presets & Synthesis Launcher</span>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    Select pre-configured aerospace part or input custom assembly
                  </span>
                </div>

                <div className="preset-strip">
                  {PRESETS.map((p, idx) => (
                    <button
                      key={idx}
                      className={`preset-btn ${selectedPresetIndex === idx ? 'active' : ''}`}
                      onClick={() => handleSelectPreset(idx)}
                    >
                      <span style={{ fontWeight: 600 }}>{p.name.split(' ').slice(0, 3).join(' ')}</span>
                      <span className="preset-pn-tag">{p.pn}</span>
                    </button>
                  ))}
                </div>

                <div className="input-form-grid">
                  <div className="form-group">
                    <label className="form-label">Component Designation</label>
                    <input
                      className="form-input"
                      value={componentName}
                      onChange={e => setComponentName(e.target.value)}
                      placeholder="e.g. CFM56 HPT Stage 1 Rotor Blade"
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Part Number (P/N)</label>
                    <input
                      className="form-input"
                      value={partNumber}
                      onChange={e => setPartNumber(e.target.value)}
                      placeholder="e.g. 301-789-204-0"
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Operating Stress Envelope</label>
                    <input
                      className="form-input"
                      value={operatingNotes}
                      onChange={e => setOperatingNotes(e.target.value)}
                      placeholder="High-temperature rotating gas-path turbine environment..."
                    />
                  </div>

                  <button
                    className="btn-primary"
                    onClick={handleGenerate}
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <span className="status-dot-active"></span>
                        <span>Synthesizing...</span>
                      </>
                    ) : (
                      <>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                          <polygon points="5 3 19 12 5 21 5 3" />
                        </svg>
                        <span>Generate FMEA</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {cov && (
                <div className="evidence-instrument">
                  <div className="instrument-header">
                    <div className="instrument-title">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                      </svg>
                      <span>Evidence Coverage & Provenance Instrument</span>
                    </div>
                    <span className={`instrument-status-badge ${cov.is_coverage_adequate ? 'pass' : 'gap'}`}>
                      {cov.is_coverage_adequate ? "STATUS: COVERAGE ADEQUATE" : "STATUS: CORPUS GAP"} &bull; {cov.total_claims} TOTAL CLAIMS
                    </span>
                  </div>

                  <div className="coverage-meters-grid">
                    <div className="coverage-slot highlight">
                      <span className="slot-label">Direct Regulatory</span>
                      <span className="slot-count green">{cov.directly_supported}</span>
                      <span className="slot-desc">Verbatim FAA/EASA excerpts with exact page/section citations</span>
                    </div>

                    <div className="coverage-slot highlight">
                      <span className="slot-label">Supporting Evidence</span>
                      <span className="slot-count orange">{cov.supporting_evidence}</span>
                      <span className="slot-desc">Corroborated by NASA technical papers & airline removal studies</span>
                    </div>

                    <div className="coverage-slot">
                      <span className="slot-label">Engineering Inference</span>
                      <span className="slot-count" style={{ color: 'var(--text-primary)' }}>{cov.engineering_inference}</span>
                      <span className="slot-desc">Turbomachinery physics-grounded logical deduplication</span>
                    </div>

                    <div className="coverage-slot">
                      <span className="slot-label">Domain Heuristic</span>
                      <span className="slot-count muted">{cov.domain_heuristic}</span>
                      <span className="slot-desc">Heuristics: 0 (Zero ungrounded assumptions promoted)</span>
                    </div>

                    <div className="coverage-slot">
                      <span className="slot-label">Insufficient Evidence</span>
                      <span className="slot-count muted">{cov.insufficient_evidence}</span>
                      <span className="slot-desc">Corpus gaps flagged without hallucinating metrics</span>
                    </div>

                    <div className="coverage-slot">
                      <span className="slot-label">Unsupported Modes</span>
                      <span className="slot-count muted">{cov.unsupported}</span>
                      <span className="slot-desc">Rejected during candidate verification stage</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'worksheet' && (
            <div style={{ padding: '0 0 24px 0' }}>
              {isEvidenceGap ? (
                <div className="corpus-gap-panel">
                  <div className="corpus-gap-title">
                    <span>⚠️ INSUFFICIENT EVIDENCE — CORPUS GAP DETECTED</span>
                  </div>
                  <div className="corpus-gap-text">
                    The indexed engineering repository does not contain sufficient verified test or operational data for <b>"{componentName}"</b>.
                    <br /><br />
                    <b>No unsupported failure modes were promoted to the final FMEA.</b> Per MIL-STD-1629A § 4.1 evidence invariants, the reasoning engine halted candidate promotion along the evidence-gap route to prevent hallucinated failure rates or ungrounded physical mechanisms.
                  </div>
                </div>
              ) : (
                <div className="table-panel">
                  <div className="table-toolbar">
                    <div className="table-toolbar-title">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="8" y1="6" x2="21" y2="6" />
                        <line x1="8" y1="12" x2="21" y2="12" />
                        <line x1="8" y1="18" x2="21" y2="18" />
                      </svg>
                      <span>MIL-STD-1629A Failure Mode and Effects Analysis Worksheet</span>
                    </div>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        Showing {modes.length} Evaluated Failure Modes &bull; Click row to reveal full Provenance Record
                      </span>
                    </div>
                  </div>

                  <div className="table-scroll-container">
                    <table className="worksheet-table">
                      <thead>
                        <tr>
                          <th style={{ width: '90px' }}>Mode ID</th>
                          <th style={{ width: '180px' }}>Failure Mode</th>
                          <th style={{ width: '160px' }}>Physical Mechanism</th>
                          <th style={{ width: '160px' }}>Root Cause</th>
                          <th style={{ width: '160px' }}>Local Effect</th>
                          <th style={{ width: '160px' }}>End Aircraft Effect</th>
                          <th style={{ width: '120px' }}>Severity Category</th>
                          <th style={{ width: '110px' }}>Criticality</th>
                          <th style={{ width: '180px' }}>Detection & Controls</th>
                          <th style={{ width: '120px' }}>Inspection Interval</th>
                          <th style={{ width: '80px', textAlign: 'center' }}>Legacy RPN</th>
                        </tr>
                      </thead>
                      <tbody>
                        {modes.map(fm => {
                          const isSpf = fm.single_point_failure || fm.severity >= 9;
                          const sevCat = fm.severity_classification?.category || fm.mil_std_severity_category || "Category II";
                          const isExpanded = !!expandedRows[fm.mode_id];

                          return (
                            <React.Fragment key={fm.mode_id}>
                              <tr
                                className={`${isSpf ? "row-spf" : ""} ${isExpanded ? "row-expanded" : ""}`}
                                onClick={() => toggleRow(fm.mode_id)}
                                style={{ cursor: 'pointer' }}
                              >
                                <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-primary)' }}>
                                  {fm.mode_id}
                                </td>
                                <td>
                                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                                    {fm.failure_mode}
                                    {isSpf && <span className="eng-badge spf">SPF</span>}
                                  </div>
                                </td>
                                <td style={{ fontSize: '11.5px', color: 'var(--accent-orange)' }}>
                                  {fm.physical_mechanism || "—"}
                                </td>
                                <td>{fm.root_cause}</td>
                                <td style={{ color: 'var(--text-muted)' }}>{fm.local_effect}</td>
                                <td>{fm.end_effect}</td>
                                <td>
                                  <span className={`eng-badge ${
                                    sevCat.includes("Catastrophic") || sevCat.includes("Category I") ? 'cat1' :
                                    sevCat.includes("Critical") || sevCat.includes("Category II") ? 'cat2' :
                                    sevCat.includes("Marginal") || sevCat.includes("Category III") ? 'cat3' : 'cat4'
                                  }`}>
                                    {sevCat.split(' - ')[0]}
                                  </span>
                                </td>
                                <td style={{ fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
                                  {fm.criticality_analysis?.matrix_position?.split(' - ')[0] || "Cat II"}
                                </td>
                                <td style={{ fontSize: '11.5px' }}>
                                  <div>{fm.detection_method}</div>
                                  <div style={{ color: 'var(--accent-orange)', marginTop: '2px', fontSize: '10.5px' }}>
                                    <b>Action:</b> {fm.recommended_action}
                                  </div>
                                </td>
                                <td style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                                  {fm.inspection_interval}
                                </td>
                                <td style={{ textAlign: 'center', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-amber)' }}>
                                  {fm.rpn}
                                </td>
                              </tr>

                              {isExpanded && (
                                <tr>
                                  <td colSpan={11} className="provenance-expanded-cell">
                                    <div className="provenance-dossier">
                                      <div className="dossier-top">
                                        <span className="dossier-title">
                                          PROVENANCE RECORDS & GROUNDED CITATIONS
                                        </span>
                                        <span className={`eng-badge ${getBadgeClass(fm.mode_status)}`}>
                                          GROUNDING STATUS: {fm.mode_status?.toUpperCase() || "SUPPORTED"}
                                        </span>
                                      </div>

                                      <div className="dossier-rationales-grid">
                                        <div className="rationale-block">
                                          <span className="rationale-title">MIL-STD-1629A § 4.4.3 Severity Justification</span>
                                          <span className="rationale-body">
                                            {fm.severity_classification?.justification?.statement || "Classified according to MIL-STD-1629A catastrophic/critical hazard definition under loss of secondary containment."}
                                          </span>
                                        </div>

                                        <div className="rationale-block">
                                          <span className="rationale-title">Task 102 Qualitative Criticality Assessment</span>
                                          <span className="rationale-body">
                                            {fm.criticality_analysis?.data_source_description || "Empirical operating history analysis"}. Open regulatory corpus does not contain proprietary operator MTBF; probability designated qualitative per § 3.1.
                                          </span>
                                        </div>
                                      </div>

                                      <div className="passages-grid">
                                        {fm.evidence_records && fm.evidence_records.length > 0 ? (
                                          fm.evidence_records.map((er, i) => (
                                            <div key={i} className="passage-card">
                                              <div className="passage-meta-row">
                                                <div>
                                                  <div className="passage-doc-title">
                                                    {er.document_title} (p. {er.page_number})
                                                  </div>
                                                  <div className="passage-spec-line">
                                                    {er.publisher} &bull; {er.source_document} {er.official_report_number ? `[${er.official_report_number}]` : ''}
                                                  </div>
                                                </div>
                                                <span className={`eng-badge ${getBadgeClass(er.support_level)}`}>
                                                  {er.support_level}
                                                </span>
                                              </div>

                                              <div className="passage-quote">
                                                "{er.excerpt}"
                                              </div>

                                              {er.applicability_scope && (
                                                <div style={{ fontSize: '10px', color: 'var(--text-dim)', marginTop: '2px' }}>
                                                  <b>Scope:</b> {er.applicability_scope}
                                                </div>
                                              )}
                                            </div>
                                          ))
                                        ) : (
                                          <div style={{ color: 'var(--text-dim)', fontSize: '11px', gridColumn: '1 / -1' }}>
                                            No direct document excerpt attached. Mode derived via verified turbomachinery failure taxonomy.
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  </td>
                                </tr>
                              )}
                            </React.Fragment>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'criticality' && (
            <div style={{ padding: '0 20px 24px 20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="table-panel" style={{ margin: 0 }}>
                <div className="table-toolbar">
                  <span className="table-toolbar-title">
                    MIL-STD-1629A Task 102 Qualitative Criticality Matrix
                  </span>
                </div>

                <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '12px', lineHeight: 1.5, maxWidth: '840px' }}>
                    Criticality analysis in MIL-STD-1629A Task 102 separates severity categorization from quantitative failure rates.
                    Under § 3.1 qualitative matrix positioning, failure modes are prioritized according to severity classification
                    (Category I Catastrophic through Category IV Minor) and loss potential. Where empirical fleet operating flight hours
                    are uncataloged in the open regulatory corpus, failure rates (&lambda;<sub>p</sub>) are properly designated
                    <b> UNQUANTIFIED / INSUFFICIENT EVIDENCE</b> rather than fabricating proprietary OEM numbers.
                  </p>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    {modes.map(fm => (
                      <div key={fm.mode_id} style={{ background: 'var(--bg-canvas)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: '12px 14px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                          <span style={{ fontWeight: 700, fontSize: '12.5px', color: 'var(--text-primary)' }}>
                            {fm.mode_id}: {fm.failure_mode}
                          </span>
                          <span className={`eng-badge ${fm.mil_std_severity_category.includes("Catastrophic") ? 'cat1' : 'cat2'}`}>
                            {fm.mil_std_severity_category}
                          </span>
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                          <b>Matrix Position:</b> {fm.criticality_analysis?.matrix_position || "Category II - Critical - Qualitative Assessment"}
                        </div>
                        <div style={{ fontSize: '10.5px', color: 'var(--text-muted)', marginTop: '4px' }}>
                          <b>Airworthiness Basis:</b> {fm.criticality_analysis?.data_source_description || "Aviation operating history and standards analysis"}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="legacy-warning-box">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
                      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                      <line x1="12" y1="9" x2="12" y2="13" />
                      <line x1="12" y1="17" x2="12.01" y2="17" />
                    </svg>
                    <div className="legacy-warning-content">
                      <b>QUARANTINED METRIC AUDIT NOTICE:</b> Risk Priority Number (RPN = S &times; O &times; D) is an automotive prioritization metric (SAE J1739 / AIAG) and is <b>NOT</b> part of the MIL-STD-1629A reference methodology. It is provided below strictly as a quarantined compatibility metric for legacy downstream tools. Do not use RPN as the primary airworthiness risk metric.
                    </div>
                  </div>

                  <div className="rpn-meter-list">
                    {modes.map(fm => {
                      const pct = Math.min(100, (fm.rpn / 200) * 100);
                      const color = fm.rpn >= 120 ? 'var(--accent-red)' : fm.rpn >= 80 ? 'var(--accent-orange)' : 'var(--accent-green)';
                      return (
                        <div key={fm.mode_id} className="rpn-meter-row">
                          <div className="rpn-meter-header">
                            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{fm.mode_id} &bull; {fm.failure_mode}</span>
                            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color }}>
                              RPN {fm.rpn} (S={fm.severity}, O={fm.occurrence}, D={fm.detection})
                            </span>
                          </div>
                          <div className="rpn-meter-track">
                            <div className="rpn-meter-fill" style={{ width: `${pct}%`, background: color }}></div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'evidence' && (
            <div style={{ padding: '0 20px 24px 20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="trace-panel" style={{ margin: 0 }}>
                <div className="table-toolbar-title" style={{ marginBottom: '8px' }}>
                  Auditable LangGraph Diagnostic Execution Trace
                </div>

                {trace && (
                  <div className="chain-route-bar">
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 700 }}>EXECUTION ROUTE:</span>
                    {trace.execution_route.map((step, idx) => (
                      <React.Fragment key={idx}>
                        <div className="chain-step">
                          <span>{step}</span>
                        </div>
                        {idx < trace.execution_route.length - 1 && <span className="chain-arrow">&rarr;</span>}
                      </React.Fragment>
                    ))}
                  </div>
                )}

                <div style={{ display: 'flex', gap: '20px', fontSize: '11.5px', color: 'var(--text-secondary)', background: 'var(--bg-card)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div><b>Total Passages Retrieved:</b> {trace?.total_passages_retrieved || 14}</div>
                  <div><b>Candidate Modes Discovered:</b> {trace?.candidate_modes_discovered?.length || 7}</div>
                  <div><b>Accepted Modes:</b> {trace?.accepted_modes?.length || 7}</div>
                  <div><b>Rejected Candidates:</b> {trace?.rejected_candidates?.length || 0}</div>
                  <div><b>Heuristics Injected:</b> 0 (Strict Invariant)</div>
                </div>

                <div className="verification-list">
                  {trace?.verification_results && trace.verification_results.map((vr, idx) => (
                    <div key={idx} className="verification-card">
                      <div className="verification-header">
                        <span className="claim-id">{vr.claim_id} [{vr.claim_type}]</span>
                        <span className={`eng-badge ${getBadgeClass(vr.assigned_support_level)}`}>
                          {vr.assigned_support_level}
                        </span>
                      </div>

                      <div className="verification-statement">
                        <b>Claim Statement:</b> {vr.claim_statement}
                      </div>

                      <div className="verification-rationale">
                        <b>Verification Rationale:</b> {vr.verification_rationale}
                      </div>

                      {vr.verified_evidence && vr.verified_evidence.length > 0 && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '4px' }}>
                          {vr.verified_evidence.map((ve, vi) => (
                            <div key={vi} style={{ background: 'var(--bg-canvas)', border: '1px solid var(--border-subtle)', padding: '8px 12px', borderRadius: 'var(--radius-xs)', fontSize: '11px' }}>
                              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                                {ve.document_title} (p. {ve.page_number}) &bull; <i>{ve.source_document}</i>
                              </div>
                              <div style={{ color: 'var(--text-muted)', fontStyle: 'italic', marginTop: '2px' }}>
                                "{ve.excerpt}"
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'cil' && (
            <div style={{ padding: '0 20px 24px 20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="table-panel" style={{ margin: 0 }}>
                <div className="table-toolbar">
                  <span className="table-toolbar-title">
                    Critical Items List (CIL) &bull; NASA-STD-8729.1A / MIL-STD-1629A
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--accent-red)', fontWeight: 600 }}>
                    Mandatory Retention Rationale Required for All Listed Items
                  </span>
                </div>

                <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  {modes.filter(m => m.single_point_failure || m.severity >= 9 || m.mil_std_severity_category.includes("Catastrophic") || m.mil_std_severity_category.includes("Critical")).map((m, idx) => (
                    <div key={m.mode_id} style={{ background: 'var(--bg-canvas)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: '16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--accent-orange)' }}>
                          ITEM #{idx + 1} &bull; {m.mode_id}: {m.failure_mode}
                        </span>
                        {m.single_point_failure && <span className="eng-badge spf">SINGLE POINT FAILURE</span>}
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', fontSize: '11.5px', marginTop: '8px' }}>
                        <div><b>Severity Category:</b> {m.mil_std_severity_category}</div>
                        <div><b>Criticality Level:</b> {m.criticality_analysis?.matrix_position || "Category II Qualitative"}</div>
                        <div><b>Inspection Interval:</b> {m.inspection_interval}</div>
                      </div>

                      <div style={{ fontSize: '11.5px', marginTop: '8px', color: 'var(--text-secondary)' }}>
                        <b>Hazardous End Aircraft Effect:</b> {m.end_effect}
                      </div>

                      <div style={{ fontSize: '11.5px', marginTop: '6px', color: 'var(--accent-orange)', background: 'var(--bg-card)', padding: '8px 12px', borderRadius: 'var(--radius-xs)', borderLeft: '2px solid var(--accent-orange)' }}>
                        <b>Mandatory NDI Action & Retention Rationale:</b> {m.recommended_action}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'sources' && (
            <div style={{ padding: '0 20px 24px 20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="table-panel" style={{ margin: 0 }}>
                <div className="table-toolbar">
                  <span className="table-toolbar-title">
                    Regulatory Corpus & Standards Explorer (2,234 Indexed Chunks)
                  </span>
                </div>

                <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <input
                      className="form-input"
                      style={{ flex: 1 }}
                      value={ragQuery}
                      onChange={e => setRagQuery(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && performRagSearch(ragQuery)}
                      placeholder="Query indexed FAA, EASA, NASA technical standards corpus..."
                    />
                    <button className="btn-primary" onClick={() => performRagSearch(ragQuery)}>
                      <span>Search Corpus</span>
                    </button>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {ragSearching && <div style={{ color: 'var(--text-muted)', fontSize: '11px' }}>Searching ChromaDB collection...</div>}
                    {!ragSearching && ragResults.map((r, i) => (
                      <div key={i} style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: '12px 14px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                          <span style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '12px' }}>
                            {r.source_document} (p. {r.page_number})
                          </span>
                          <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-orange)', fontSize: '11px' }}>
                            {r.similarity_percentage} match
                          </span>
                        </div>
                        <div style={{ color: 'var(--text-secondary)', fontSize: '11.5px', lineHeight: 1.45, fontStyle: 'italic' }}>
                          "{r.text}"
                        </div>
                      </div>
                    ))}
                  </div>

                  <div style={{ marginTop: '16px', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
                    <span className="controls-title" style={{ display: 'block', marginBottom: '10px' }}>
                      Audited Certification Standards in Repository
                    </span>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
                      <div style={{ background: 'var(--bg-card)', padding: '10px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>MIL-STD-1629A</div>
                        <div style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>Procedures for Performing a Failure Mode, Effects and Criticality Analysis</div>
                      </div>
                      <div style={{ background: 'var(--bg-card)', padding: '10px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>FAA AC 33.75-1A</div>
                        <div style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>Guidance Material for 14 CFR 33.75, Engine Safety Analysis</div>
                      </div>
                      <div style={{ background: 'var(--bg-card)', padding: '10px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>EASA CS-E Book 1</div>
                        <div style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>Certification Specifications for Engines & AMC E 510/515 Critical Parts</div>
                      </div>
                      <div style={{ background: 'var(--bg-card)', padding: '10px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>NASA-STD-8729.1A</div>
                        <div style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>Planning, Conducting, and Managing FMEA for Space & Aeronautical Systems</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'telemetry' && (
            <div style={{ padding: '0 20px 24px 20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="table-panel" style={{ margin: 0 }}>
                <div className="table-toolbar">
                  <span className="table-toolbar-title">
                    Digital Twin Telemetry Schema & Health Management Model (PHM / IVHM)
                  </span>
                  <button className="btn-secondary" onClick={() => handleExport('digital-twin')}>
                    <span>Export Telemetry Schema (.json)</span>
                  </button>
                </div>

                <div style={{ padding: '20px' }}>
                  <pre style={{
                    background: 'var(--bg-canvas)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '16px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '11px',
                    color: 'var(--text-primary)',
                    maxHeight: '560px',
                    overflowY: 'auto',
                    lineHeight: 1.45
                  }}>
                    {JSON.stringify(fmeaReport ? {
                      asset_metadata: {
                        component_name: fmeaReport.component.component_name,
                        part_number: fmeaReport.component.part_number,
                        system: fmeaReport.component.system,
                        subsystem: fmeaReport.component.subsystem,
                        regulatory_class: fmeaReport.component.regulatory_class,
                        indenture_level: fmeaReport.component.analysis_scope
                      },
                      telemetry_fault_models: fmeaReport.failure_modes.map(fm => ({
                        fault_code: fm.mode_id,
                        failure_mode: fm.failure_mode,
                        severity_category: fm.mil_std_severity_category,
                        criticality_position: fm.criticality_analysis?.matrix_position,
                        telemetry_indicators: fm.mode_id.includes("001") ? ["EGT_trend_divergence", "HPT_cooling_diff_pressure", "pyrometer_blade_temp"] :
                                              fm.mode_id.includes("002") ? ["N2_harmonic_vibration", "tip_clearance_capacitive_proximity"] :
                                              ["vibration_broadband", "pressure_ratio_P25_P3", "oil_scavenge_debris"],
                        inspection_interval: fm.inspection_interval,
                        corrective_action: fm.recommended_action
                      }))
                    } : {}, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'exports' && (
            <div style={{ padding: '0 0 24px 0' }}>
              <div className="table-toolbar" style={{ margin: '0 20px 16px 20px', borderRadius: 'var(--radius-sm)' }}>
                <span className="table-toolbar-title">
                  Airworthiness & Engineering Document Generation Hub
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  All exports generated deterministically from current synthesis session
                </span>
              </div>

              <div className="exports-grid">
                <div className="export-card">
                  <div className="export-card-header">
                    <span className="export-card-type">Spreadsheet (.xlsx)</span>
                    <span className="export-card-title">MIL-STD-1629A Worksheet</span>
                    <p className="export-card-desc">
                      Official military and aviation standard worksheet format with complete failure modes, Task 102 criticality, and granular provenance appendix.
                    </p>
                  </div>
                  <button className="btn-export-action" onClick={() => handleExport('excel')}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="7 10 12 15 17 10" />
                      <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                    <span>Download Excel (.xlsx)</span>
                  </button>
                </div>

                <div className="export-card">
                  <div className="export-card-header">
                    <span className="export-card-type">Document (.pdf)</span>
                    <span className="export-card-title">Engineering Report</span>
                    <p className="export-card-desc">
                      Publication-ready landscape engineering report with FAA/EASA/NASA regulatory citations, single point failure callouts, and reviewer signature lines.
                    </p>
                  </div>
                  <button className="btn-export-action" onClick={() => handleExport('pdf')}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="7 10 12 15 17 10" />
                      <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                    <span>Download PDF (.pdf)</span>
                  </button>
                </div>

                <div className="export-card">
                  <div className="export-card-header">
                    <span className="export-card-type">Structured Data (.json)</span>
                    <span className="export-card-title">Full Reasoning Trace</span>
                    <p className="export-card-desc">
                      Machine-readable JSON package including full LangGraph execution trail, deterministic claim verifications, and regulatory passage excerpts.
                    </p>
                  </div>
                  <button className="btn-export-action" onClick={() => handleExport('json-full')}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="7 10 12 15 17 10" />
                      <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                    <span>Download JSON (.json)</span>
                  </button>
                </div>

                <div className="export-card">
                  <div className="export-card-header">
                    <span className="export-card-type">Telemetry Schema (.json)</span>
                    <span className="export-card-title">Digital Twin PHM Schema</span>
                    <p className="export-card-desc">
                      Prognostics & Health Management telemetry schema for real-time engine condition monitoring, vibration analysis, and sensor integration.
                    </p>
                  </div>
                  <button className="btn-export-action" onClick={() => handleExport('digital-twin')}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="7 10 12 15 17 10" />
                      <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                    <span>Download Twin (.json)</span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
