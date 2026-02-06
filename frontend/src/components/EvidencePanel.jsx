import React from "react";
import { labelColor } from "../utils/colors";

/**
 * Bottom / side panel – evidence details, NLI breakdown, citation link.
 */
export default function EvidencePanel({ claim }) {
  if (!claim) {
    return (
      <div style={styles.panel}>
        <p style={styles.empty}>Select a claim to see evidence details.</p>
      </div>
    );
  }

  const lc = labelColor(claim.label);

  return (
    <div style={styles.panel}>
      <div style={styles.header}>
        <span style={{ ...styles.badge, color: lc.text }}>{lc.label}</span>
        <span style={styles.claimId}>Claim {claim.claim_id}</span>
        <span style={styles.type}>{claim.claim_type}</span>
        <span style={styles.weight}>weight {claim.risk_weight}</span>
      </div>

      <p style={styles.claim}>{claim.claim_text}</p>
      <p style={styles.rationale}>{claim.rationale}</p>

      {claim.suggested_correction && (
        <div style={styles.corrBox}>
          <strong>✏️ Suggested correction:</strong> {claim.suggested_correction}
        </div>
      )}

      <h4 style={styles.evTitle}>Evidence ({(claim.evidence || []).length})</h4>

      <div style={styles.evList}>
        {(claim.evidence || []).map((ev, idx) => (
          <div key={idx} style={styles.evCard}>
            <div style={styles.evMeta}>
              <span>📄</span>
              <span>{ev.doc_name}</span>
              <span>p.{ev.page}, ¶{ev.paragraph_id}</span>
              <span style={styles.score}>
                score {(ev.retrieval_score || 0).toFixed(2)}
              </span>
            </div>
            <p style={styles.evSnippet}>{ev.snippet}</p>

            {ev.nli && Object.keys(ev.nli).length > 0 && (
              <div style={styles.nliRow}>
                {Object.entries(ev.nli).map(([k, v]) => (
                  <span key={k} style={styles.nliItem}>
                    {k}: E {v.entail} · C {v.contradict} · N {v.neutral}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        {(claim.evidence || []).length === 0 && (
          <p style={{ fontSize: 12, color: "var(--text-dim)" }}>No evidence retrieved.</p>
        )}
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
    borderTop: "1px solid var(--border)",
    overflowY: "auto",
    padding: 14,
  },
  empty: { color: "var(--text-dim)", fontSize: 13, textAlign: "center", marginTop: 20 },
  header: { display: "flex", alignItems: "center", gap: 10, marginBottom: 8 },
  badge: { fontWeight: 700, fontSize: 13, textTransform: "uppercase" },
  claimId: { fontSize: 12, color: "var(--text-dim)" },
  type: {
    fontSize: 10, padding: "2px 6px", background: "var(--bg)", borderRadius: 4,
    color: "var(--text-dim)",
  },
  weight: { fontSize: 10, color: "var(--text-dim)", marginLeft: "auto" },
  claim: { fontSize: 13, lineHeight: 1.5, marginBottom: 4 },
  rationale: { fontSize: 12, color: "var(--text-dim)", marginBottom: 8 },
  corrBox: {
    fontSize: 12, color: "var(--green)", padding: "8px 10px",
    background: "var(--green-bg)", borderRadius: "var(--radius)", marginBottom: 10,
  },
  evTitle: { fontSize: 12, fontWeight: 600, marginBottom: 6 },
  evList: { display: "flex", flexDirection: "column", gap: 8 },
  evCard: {
    padding: "10px 12px", background: "var(--bg-card)",
    borderRadius: "var(--radius)",
  },
  evMeta: {
    display: "flex", alignItems: "center", gap: 8,
    fontSize: 11, color: "var(--text-dim)", marginBottom: 6,
  },
  score: { marginLeft: "auto", fontWeight: 600 },
  evSnippet: { fontSize: 12, lineHeight: 1.5 },
  nliRow: {
    marginTop: 6, display: "flex", flexWrap: "wrap", gap: 8,
    fontSize: 10, color: "var(--text-dim)",
  },
  nliItem: { background: "var(--bg)", padding: "2px 6px", borderRadius: 4 },
};
