import React from "react";
import { labelColor } from "../utils/colors";

/**
 * Left pane — LLM output with sentence-level / claim-level highlighting.
 * Click a claim → propagate to parent (focuses evidence).
 */
export default function OutputPanel({ claims, selectedClaimId, onSelectClaim, filter }) {
  // Group claims by sentence_id
  const bySentence = {};
  for (const c of claims) {
    if (filter !== "all" && c.label !== filter) continue;
    if (!bySentence[c.sentence_id]) bySentence[c.sentence_id] = [];
    bySentence[c.sentence_id].push(c);
  }

  const sentenceIds = Object.keys(bySentence).sort((a, b) => +a - +b);

  return (
    <div style={styles.panel}>
      <h3 style={styles.heading}>LLM Output — Claim Annotations</h3>
      <div style={styles.list}>
        {sentenceIds.length === 0 && (
          <p style={styles.empty}>No claims match the current filter.</p>
        )}
        {sentenceIds.map((sid) => (
          <SentenceGroup
            key={sid}
            sentenceId={sid}
            claims={bySentence[sid]}
            selectedClaimId={selectedClaimId}
            onSelectClaim={onSelectClaim}
          />
        ))}
      </div>
    </div>
  );
}

function SentenceGroup({ sentenceId, claims, selectedClaimId, onSelectClaim }) {
  return (
    <div style={styles.sentGroup}>
      <span style={styles.sentLabel}>Sentence {+sentenceId + 1}</span>
      {claims.map((c) => {
        const lc = labelColor(c.label);
        const selected = c.claim_id === selectedClaimId;
        return (
          <div
            key={c.claim_id}
            onClick={() => onSelectClaim(c.claim_id)}
            style={{
              ...styles.claim,
              background: lc.bg,
              borderLeftColor: lc.text,
              outline: selected ? `2px solid ${lc.text}` : "none",
            }}
          >
            <div style={styles.claimTop}>
              <span style={{ ...styles.labelBadge, color: lc.text }}>{lc.label}</span>
              <span style={styles.conf}>{Math.round(c.confidence * 100)}%</span>
              <span style={styles.type}>{c.claim_type}</span>
            </div>
            <p style={styles.claimText}>{c.claim_text}</p>
            <p style={styles.rationale}>{c.rationale}</p>
            {c.suggested_correction && (
              <p style={styles.correction}>
                <strong>✏️ Fix:</strong> {c.suggested_correction}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}

const styles = {
  panel: {
    height: "100%",
    display: "flex",
    flexDirection: "column",
    background: "var(--bg-panel)",
    borderRight: "1px solid var(--border)",
  },
  heading: {
    padding: "12px 16px",
    fontSize: 14,
    fontWeight: 600,
    borderBottom: "1px solid var(--border)",
    flexShrink: 0,
  },
  list: { flex: 1, overflowY: "auto", padding: 12 },
  empty: { color: "var(--text-dim)", fontSize: 13, textAlign: "center", marginTop: 40 },
  sentGroup: { marginBottom: 16 },
  sentLabel: { fontSize: 11, color: "var(--text-dim)", marginBottom: 4, display: "block" },
  claim: {
    padding: "10px 12px",
    borderRadius: "var(--radius)",
    borderLeft: "3px solid",
    marginBottom: 8,
    cursor: "pointer",
    transition: "outline .15s",
  },
  claimTop: { display: "flex", alignItems: "center", gap: 8, marginBottom: 4 },
  labelBadge: { fontWeight: 700, fontSize: 12, textTransform: "uppercase" },
  conf: { fontSize: 11, color: "var(--text-dim)" },
  type: {
    fontSize: 10,
    color: "var(--text-dim)",
    background: "var(--bg)",
    padding: "2px 6px",
    borderRadius: 4,
    marginLeft: "auto",
  },
  claimText: { fontSize: 13, lineHeight: 1.5, margin: 0 },
  rationale: { fontSize: 11, color: "var(--text-dim)", marginTop: 4, margin: 0 },
  correction: {
    fontSize: 12,
    color: "var(--green)",
    marginTop: 6,
    padding: "6px 8px",
    background: "var(--green-bg)",
    borderRadius: 4,
  },
};
