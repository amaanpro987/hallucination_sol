import React from "react";

/**
 * Right pane — source evidence viewer.
 * Shows evidence snippets from source documents for the selected claim.
 */
export default function SourceViewer({ evidence, sources }) {
  // Show evidence snippets
  if (evidence && evidence.length > 0) {
    return (
      <div style={styles.panel}>
        <h3 style={styles.heading}>📖 Source Evidence</h3>
        <div style={styles.snippets}>
          {evidence.map((e, i) => (
            <div key={i} style={styles.snippetCard}>
              <div style={styles.snippetHeader}>
                <span style={styles.docName}>📄 {e.doc_name || "Source"}</span>
                <span style={styles.location}>
                  Page {e.page || "?"} · Paragraph {e.paragraph_id || "?"}
                </span>
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
    padding: "10px 14px",
    borderBottom: "1px solid var(--border)",
    background: "rgba(99, 102, 241, 0.05)",
  },
  docName: { fontSize: 13, fontWeight: 600 },
  location: { fontSize: 11, color: "var(--text-dim)" },
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
