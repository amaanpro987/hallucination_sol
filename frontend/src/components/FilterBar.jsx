import React from "react";
import { labelColor } from "../utils/colors";

/**
 * Filter bar — show only Red / Yellow / all; sort by confidence.
 */
export default function FilterBar({ filter, onFilterChange }) {
  const options = [
    { key: "all",           label: "All" },
    { key: "CONTRADICTED",  label: "🔴 Red only" },
    { key: "UNVERIFIABLE",  label: "🟡 Yellow only" },
    { key: "SUPPORTED",     label: "🟢 Green only" },
  ];

  return (
    <div style={styles.wrap}>
      {options.map((o) => (
        <button
          key={o.key}
          onClick={() => onFilterChange(o.key)}
          style={{
            ...styles.btn,
            ...(filter === o.key ? styles.active : {}),
          }}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

const styles = {
  wrap: {
    display: "flex",
    gap: 6,
    padding: "8px 20px",
    background: "var(--bg-panel)",
    borderBottom: "1px solid var(--border)",
  },
  btn: {
    padding: "6px 16px",
    fontSize: 12,
    border: "1px solid var(--border)",
    borderRadius: 999,
    background: "transparent",
    color: "var(--text-dim)",
    cursor: "pointer",
    transition: "all .15s",
  },
  active: {
    background: "var(--accent)",
    color: "#fff",
    borderColor: "var(--accent)",
  },
};
