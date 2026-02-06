import React, { useState, useCallback } from "react";
import { startVerification, getRun } from "../api/client";

/**
 * Paste LLM output + click Verify.
 */
export default function VerifyForm({ onRunReady }) {
  const [text, setText] = useState("");
  const [runName, setRunName] = useState("Untitled run");
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState("");

  const handleVerify = useCallback(async () => {
    if (!text.trim()) return;
    setRunning(true);
    setStatus("🔄 Starting verification…");
    try {
      const summary = await startVerification(text, "default", runName);
      let run = summary;
      while (run.status !== "done" && run.status !== "failed") {
        await new Promise((r) => setTimeout(r, 2000));
        run = await getRun(run.id);
        setStatus(`🔄 Verifying… (${run.status})`);
      }
      if (run.status === "done") {
        setStatus("✅ Verification complete!");
        if (onRunReady) onRunReady(run);
      } else {
        setStatus("❌ Verification failed");
      }
    } catch (err) {
      setStatus(`❌ Error: ${err.message}`);
    }
    setRunning(false);
  }, [text, runName, onRunReady]);

  return (
    <div style={styles.wrap}>
      <h3 style={styles.heading}>🔍 Verify LLM Output</h3>

      <label style={styles.label}>Run name</label>
      <input
        style={styles.input}
        type="text"
        placeholder="Run name"
        value={runName}
        onChange={(e) => setRunName(e.target.value)}
      />

      <label style={styles.label}>LLM-generated text</label>
      <textarea
        style={styles.textarea}
        rows={12}
        placeholder="Paste the LLM-generated text here…"
        value={text}
        onChange={(e) => setText(e.target.value)}
      />

      <div style={styles.actions}>
        <button
          style={{
            ...styles.btn,
            opacity: running || !text.trim() ? 0.5 : 1,
            cursor: running || !text.trim() ? "not-allowed" : "pointer",
          }}
          onClick={handleVerify}
          disabled={running || !text.trim()}
        >
          {running ? "⏳ Verifying…" : "▶️ Verify"}
        </button>
      </div>

      {status && <p style={styles.status}>{status}</p>}
    </div>
  );
}

const styles = {
  wrap: { padding: 20 },
  heading: { fontSize: 16, fontWeight: 600, marginBottom: 14 },
  label: {
    display: "block", fontSize: 12, fontWeight: 500,
    color: "var(--text-dim)", marginBottom: 4, marginTop: 10,
  },
  input: {
    width: "100%", padding: "10px 12px", fontSize: 13,
    border: "1px solid var(--border)", borderRadius: "var(--radius)",
    background: "var(--bg-card)", color: "var(--text)",
    outline: "none", boxSizing: "border-box",
  },
  textarea: {
    width: "100%", padding: "12px", fontSize: 13,
    border: "1px solid var(--border)", borderRadius: "var(--radius)",
    background: "var(--bg-card)", color: "var(--text)",
    resize: "vertical", outline: "none", lineHeight: 1.6,
    fontFamily: "inherit", boxSizing: "border-box",
  },
  actions: { marginTop: 14 },
  btn: {
    display: "inline-flex", alignItems: "center", gap: 6,
    padding: "11px 24px", fontSize: 14, fontWeight: 600,
    border: "none", borderRadius: "var(--radius)",
    background: "var(--accent)", color: "#fff",
    transition: "all .15s",
  },
  status: { fontSize: 13, color: "var(--text-dim)", marginTop: 12, lineHeight: 1.4 },
};
