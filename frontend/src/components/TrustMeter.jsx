import React from "react";
import { trustColor } from "../utils/colors";

/**
 * Top-bar trust meter + claim count badges + performance metrics.
 */
export default function TrustMeter({ trust }) {
  if (!trust) return null;

  const pct = Math.round(trust.overall);
  const color = trustColor(trust.overall);
  const perf = trust.performance_metrics;

  return (
    <div style={styles.bar}>
      {/* ── Score gauge ─────────────────── */}
      <div style={styles.gauge}>
        <svg width="56" height="56" viewBox="0 0 56 56">
          <circle cx="28" cy="28" r="24" fill="none" stroke="var(--border)" strokeWidth="5" />
          <circle
            cx="28" cy="28" r="24"
            fill="none"
            stroke={color}
            strokeWidth="5"
            strokeDasharray={`${(pct / 100) * 150.8} 150.8`}
            strokeLinecap="round"
            transform="rotate(-90 28 28)"
          />
        </svg>
        <span style={{ ...styles.pct, color }}>{pct}</span>
      </div>

      <div style={styles.labels}>
        <span style={styles.title}>Trust Score</span>
        <span style={styles.sub}>
          Faith {Math.round(trust.faithfulness)}% · Ground {Math.round(trust.groundedness)}%
        </span>
        {perf && (
          <span style={styles.perf}>
            ⏱️ {perf.total_sec}s ({perf.claims_count} claims)
          </span>
        )}
      </div>

      {/* ── Count badges ───────────────── */}
      <div style={styles.badges}>
        <Badge icon="🟢" count={trust.supported_count}    color="var(--green)"  label="Supported" />
        <Badge icon="🔴" count={trust.contradicted_count} color="var(--red)"    label="Contradicted" />
        <Badge icon="🟡" count={trust.unverifiable_count} color="var(--yellow)" label="Unverifiable" />
      </div>
    </div>
  );
}

function Badge({ icon, count, color, label }) {
  return (
    <div style={{ ...styles.badge, borderColor: color }} title={label}>
      <span>{icon}</span>
      <span style={{ color, fontWeight: 600, fontSize: 14 }}>{count}</span>
      <span style={{ fontSize: 11, color: "var(--text-dim)" }}>{label}</span>
    </div>
  );
}

const styles = {
  bar: {
    display: "flex",
    alignItems: "center",
    gap: 20,
    padding: "10px 20px",
    background: "var(--bg-panel)",
    borderBottom: "1px solid var(--border)",
  },
  gauge: { position: "relative", width: 56, height: 56, flexShrink: 0 },
  pct: {
    position: "absolute", top: "50%", left: "50%",
    transform: "translate(-50%,-50%)",
    fontWeight: 700, fontSize: 16,
  },
  labels: { display: "flex", flexDirection: "column", gap: 2 },
  title: { fontWeight: 600, fontSize: 14 },
  sub: { fontSize: 12, color: "var(--text-dim)" },
  perf: { fontSize: 11, color: "var(--accent)", marginTop: 2 },
  badges: { display: "flex", gap: 10, marginLeft: "auto" },
  badge: {
    display: "flex", alignItems: "center", gap: 6,
    padding: "6px 12px", borderRadius: "var(--radius)",
    border: "1px solid", background: "var(--bg-card)",
    fontSize: 13,
  },
};
