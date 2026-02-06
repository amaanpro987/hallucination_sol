import React, { useState, useMemo } from "react";
import UploadPanel from "./components/UploadPanel";
import VerifyForm from "./components/VerifyForm";
import TrustMeter from "./components/TrustMeter";
import FilterBar from "./components/FilterBar";
import OutputPanel from "./components/OutputPanel";
import SourceViewer from "./components/SourceViewer";
import EvidencePanel from "./components/EvidencePanel";
import "./App.css";

/**
 * Root application — orchestrates the split-pane auditor UI.
 *
 * Stages:
 *  1. Setup  — upload & ingest sources
 *  2. Verify — paste LLM text, run verification
 *  3. Review — split-pane results viewer
 */
export default function App() {
  const [stage, setStage] = useState("setup"); // setup | verify | review
  const [runData, setRunData] = useState(null);
  const [selectedClaimId, setSelectedClaimId] = useState(null);
  const [filter, setFilter] = useState("all");

  const claims = runData?.claims || [];

  const selectedClaim = useMemo(
    () => claims.find((c) => c.claim_id === selectedClaimId) || null,
    [claims, selectedClaimId]
  );

  // Called when ingestion is done
  const handleIngested = () => setStage("verify");

  // Called when verification finishes
  const handleRunReady = (run) => {
    setRunData(run);
    setStage("review");
    if (run.claims && run.claims.length > 0) {
      setSelectedClaimId(run.claims[0].claim_id);
    }
  };

  // ── Setup stage ──────────────────────────────────
  if (stage === "setup") {
    return (
      <div className="stage-container">
        <div className="stage-card">
          <header className="brand">
            <div className="brand-icon">🛡️</div>
            <h1>Hallucination Hunter</h1>
            <p>Upload trusted source documents, then verify LLM outputs against them.</p>
          </header>
          <UploadPanel onIngested={handleIngested} />
          <button
            className="skip-btn"
            type="button"
            onClick={() => setStage("verify")}
          >
            Skip — I already ingested sources →
          </button>
        </div>
      </div>
    );
  }

  // ── Verify stage ─────────────────────────────────
  if (stage === "verify") {
    return (
      <div className="stage-container">
        <div className="stage-card">
          <header className="brand">
            <div className="brand-icon">🛡️</div>
            <h1>Hallucination Hunter</h1>
            <p>Paste the LLM-generated text below and click Verify.</p>
          </header>
          <VerifyForm onRunReady={handleRunReady} />
          <button
            className="skip-btn"
            type="button"
            onClick={() => setStage("setup")}
          >
            ← Back to upload
          </button>
        </div>
      </div>
    );
  }

  // ── Review stage (split-pane) ────────────────────
  return (
    <div className="review-root">
      {/* Top bar */}
      <TrustMeter trust={runData?.trust} />
      <FilterBar filter={filter} onFilterChange={setFilter} />

      {/* Main split */}
      <div className="split-main">
        {/* Left: claims */}
        <div className="pane-left">
          <OutputPanel
            claims={claims}
            selectedClaimId={selectedClaimId}
            onSelectClaim={setSelectedClaimId}
            filter={filter}
          />
        </div>

        {/* Right: source viewer + evidence */}
        <div className="pane-right">
          <div className="pane-right-top">
            <SourceViewer
              evidence={selectedClaim?.evidence}
              sources={[]}
            />
          </div>
          <div className="pane-right-bottom">
            <EvidencePanel claim={selectedClaim} />
          </div>
        </div>
      </div>

      {/* New run button */}
      <button
        className="new-run-btn"
        type="button"
        onClick={() => {
          setStage("verify");
          setRunData(null);
          setSelectedClaimId(null);
          setFilter("all");
        }}
      >
        + New Verification
      </button>
    </div>
  );
}
