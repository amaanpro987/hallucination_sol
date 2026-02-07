import React, { useState } from "react";
import PDFViewer from "./PDFViewer";

/**
 * Right pane — source evidence viewer with PDF and snippets.
 * Shows evidence snippets from source documents for the selected claim.
 */
export default function SourceViewer({ evidence, sources }) {
  const [activeTab, setActiveTab] = useState("snippets"); // snippets | pdf
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [targetPage, setTargetPage] = useState(null);

  const handleViewInPDF = (docId, page) => {
    setSelectedDoc(docId);
    setTargetPage(page);
    setActiveTab("pdf");
  };

  // Show evidence snippets
  if (evidence && evidence.length > 0) {
    const firstEvidence = evidence[0];
    
    return (
      <div style={styles.panel}>
        {/* Tab Header */}
        <div style={styles.header}>
          <div style={styles.tabs}>
            <button
              style={{
                ...styles.tab,
                ...(activeTab === "snippets" ? styles.tabActive : {}),
              }}
              onClick={() => setActiveTab("snippets")}
            >
              📝 Evidence Snippets
            </button>
            <button
              style={{
                ...styles.tab,
                ...(activeTab === "pdf" ? styles.tabActive : {}),
              }}
              onClick={() => {
                setActiveTab("pdf");
                if (!selectedDoc && firstEvidence) {
                  setSelectedDoc(firstEvidence.doc_id);
                  setTargetPage(firstEvidence.page);
                }
              }}
            >
              📄 Source PDF
            </button>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === "snippets" ? (
          <div style={styles.snippets}>
            {evidence.map((e, i) => (
              <div key={i} style={styles.snippetCard}>
                <div style={styles.snippetHeader}>
                  <span style={styles.docName}>📄 {e.doc_name || "Source"}</span>
                  <span style={styles.location}>
                    Page {e.page || "?"} · Paragraph {e.paragraph_id || "?"}
                  </span>
                  <button
                    style={styles.viewPdfBtn}
                    onClick={() => handleViewInPDF(e.doc_id, e.page)}
                    title="View in PDF"
                  >
                    🔍 View
                  </button>
                </div>
                <div style={styles.scoreBar}>
                  <div style={styles.scoreLabel}>Retrieval Score</div>
                  <div style={styles.scoreMeter}>
                    <div
                      style={{
                        ...styles.scoreFill,
                        width: `${Math.min(100, (e.retrieval_score || 0) * 100)}%`,
                      }}
                    />
                  </div>
                  <span style={styles.scoreValue}>
                    {((e.retrieval_score || 0) * 100).toFixed(0)}%
                  </span>
                </div>
                <div style={styles.snippetBox}>
                  <p style={styles.snippetText}>{e.snippet}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <PDFViewer 
            docId={selectedDoc} 
            targetPage={targetPage}
          />
        )}
      </div>
    );
  }

  // Placeholder when no claim is selected
  return (
    <div style={styles.panel}>
      <h3 style={styles.heading}>📖 Source Viewer</h3>
      <div style={styles.placeholderWrap}>
        <div style={styles.placeholderIcon}>🔎</div>
        <p style={styles.placeholder}>
          Click a claim on the left to view its source evidence here.
        </p>
      </div>
    </div>
  );
}

const styles = {
  panel: {
    height: "100%",
    display: "flex",
    flexDirection: "column",
    background: "var(--bg-panel)",
  },
  header: {
    borderBottom: "1px solid var(--border)",
    flexShrink: 0,
  },
  tabs: {
    display: "flex",
    gap: 0,
  },
  tab: {
    flex: 1,
    padding: "10px 16px",
    fontSize: 13,
    fontWeight: 500,
    background: "transparent",
    border: "none",
    borderBottom: "2px solid transparent",
    cursor: "pointer",
    color: "var(--text-dim)",
    transition: "all .2s",
  },
  tabActive: {
    color: "var(--accent)",
    borderBottomColor: "var(--accent)",
    background: "rgba(99, 102, 241, 0.05)",
  },
  heading: {
    padding: "12px 16px",
    fontSize: 14,
    fontWeight: 600,
    borderBottom: "1px solid var(--border)",
    flexShrink: 0,
    margin: 0,
  },
  placeholderWrap: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    padding: 20,
  },
  placeholderIcon: { fontSize: 40, marginBottom: 12, opacity: 0.5 },
  placeholder: {
    color: "var(--text-dim)",
    fontSize: 13,
    textAlign: "center",
  },
  snippets: { flex: 1, overflowY: "auto", padding: 12 },
  snippetCard: {
    background: "var(--bg-card)",
    borderRadius: "var(--radius)",
    marginBottom: 12,
    overflow: "hidden",
    border: "1px solid var(--border)",
  },
  snippetHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 8,
    padding: "10px 14px",
    borderBottom: "1px solid var(--border)",
    background: "rgba(99, 102, 241, 0.05)",
  },
  docName: { fontSize: 13, fontWeight: 600, flex: 1 },
  location: { fontSize: 11, color: "var(--text-dim)" },
  viewPdfBtn: {
    padding: "4px 8px",
    fontSize: 11,
    background: "var(--accent)",
    color: "white",
    border: "none",
    borderRadius: 4,
    cursor: "pointer",
    fontWeight: 600,
    transition: "opacity .2s",
  },
  scoreBar: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "8px 14px",
    borderBottom: "1px solid var(--border)",
  },
  scoreLabel: { fontSize: 11, color: "var(--text-dim)", flexShrink: 0 },
  scoreMeter: {
    flex: 1,
    height: 6,
    background: "var(--border)",
    borderRadius: 3,
    overflow: "hidden",
  },
  scoreFill: {
    height: "100%",
    background: "var(--accent)",
    borderRadius: 3,
    transition: "width .3s",
  },
  scoreValue: { fontSize: 12, fontWeight: 600, color: "var(--accent)", minWidth: 32, textAlign: "right" },
  snippetBox: {
    padding: "12px 14px",
  },
  snippetText: {
    fontSize: 13,
    lineHeight: 1.6,
    color: "var(--text)",
    margin: 0,
    whiteSpace: "pre-wrap",
  },
};
