import React, { useState, useRef, useCallback } from "react";
import { uploadSources, ingestSources, getJob } from "../api/client";

/**
 * Upload panel — drag-drop or click to upload PDFs/text,
 * then trigger ingestion.
 */
export default function UploadPanel({ onIngested }) {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [uploaded, setUploaded] = useState([]);
  const [status, setStatus] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef(null);

  const handleFiles = useCallback((fileList) => {
    setFiles(Array.from(fileList));
  }, []);

  const handleUpload = useCallback(async () => {
    if (files.length === 0) return;
    setUploading(true);
    setStatus("Uploading…");
    try {
      const docs = await uploadSources(files);
      setUploaded((prev) => [...prev, ...docs]);
      setStatus(`✅ Uploaded ${docs.length} file(s) successfully.`);
      setFiles([]);
      if (inputRef.current) inputRef.current.value = "";
    } catch (err) {
      setStatus(`❌ Upload error: ${err.message}`);
    }
    setUploading(false);
  }, [files]);

  const handleIngest = useCallback(async () => {
    setIngesting(true);
    setStatus("🔄 Ingesting — parsing, chunking, indexing…");
    try {
      const job = await ingestSources();
      let current = job;
      while (current.status !== "done" && current.status !== "failed") {
        await new Promise((r) => setTimeout(r, 2000));
        current = await getJob(current.id);
        setStatus(`🔄 Ingesting… ${Math.round((current.progress || 0) * 100)}%`);
      }
      if (current.status === "done") {
        setStatus("✅ Ingestion complete! Sources are indexed and ready.");
        if (onIngested) onIngested();
      } else {
        setStatus(`❌ Ingestion failed: ${current.error || "Unknown error"}`);
      }
    } catch (err) {
      setStatus(`❌ Ingestion error: ${err.message}`);
    }
    setIngesting(false);
  }, [onIngested]);

  return (
    <div style={styles.wrap}>
      <h3 style={styles.heading}>📁 Upload Source Documents</h3>

      {/* Drop zone */}
      <div
        style={{
          ...styles.dropZone,
          ...(dragOver ? styles.dropZoneActive : {}),
        }}
        onClick={() => inputRef.current && inputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); setDragOver(true); }}
        onDragLeave={(e) => { e.preventDefault(); e.stopPropagation(); setDragOver(false); }}
        onDrop={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setDragOver(false);
          if (e.dataTransfer.files.length > 0) handleFiles(e.dataTransfer.files);
        }}
      >
        <div style={styles.dropIcon}>📄</div>
        <p style={styles.dropText}>
          {files.length > 0
            ? files.map((f) => f.name).join(", ")
            : "Drop PDF / TXT files here, or click to browse"}
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.txt,.text,.md"
          style={{ display: "none" }}
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleFiles(e.target.files);
            }
          }}
        />
      </div>

      <div style={styles.actions}>
        <button
          style={{
            ...styles.btn,
            opacity: uploading || files.length === 0 ? 0.5 : 1,
            cursor: uploading || files.length === 0 ? "not-allowed" : "pointer",
          }}
          onClick={handleUpload}
          disabled={uploading || files.length === 0}
        >
          {uploading ? "⏳ Uploading…" : "⬆️ Upload"}
        </button>
        <button
          style={{
            ...styles.btn,
            ...styles.btnPrimary,
            opacity: ingesting || uploaded.length === 0 ? 0.5 : 1,
            cursor: ingesting || uploaded.length === 0 ? "not-allowed" : "pointer",
          }}
          onClick={handleIngest}
          disabled={ingesting || uploaded.length === 0}
        >
          {ingesting ? "⏳ Ingesting…" : "🔍 Ingest & Index"}
        </button>
      </div>

      {status && <p style={styles.status}>{status}</p>}

      {/* Uploaded file list */}
      {uploaded.length > 0 && (
        <div style={styles.fileList}>
          <p style={styles.fileListTitle}>Uploaded files:</p>
          {uploaded.map((s) => (
            <div key={s.id} style={styles.fileItem}>
              <span style={styles.fileIcon}>📄</span>
              <span>{s.filename}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const styles = {
  wrap: { padding: 20 },
  heading: { fontSize: 16, fontWeight: 600, marginBottom: 14 },
  dropZone: {
    border: "2px dashed var(--border)",
    borderRadius: "var(--radius)",
    padding: "36px 20px",
    textAlign: "center",
    cursor: "pointer",
    transition: "all .2s",
    background: "var(--bg-card)",
  },
  dropZoneActive: {
    borderColor: "var(--accent)",
    background: "rgba(99, 102, 241, 0.08)",
  },
  dropIcon: { fontSize: 32, marginBottom: 8 },
  dropText: { fontSize: 13, color: "var(--text-dim)", margin: 0 },
  actions: { display: "flex", gap: 10, marginTop: 14 },
  btn: {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    padding: "10px 20px",
    fontSize: 13,
    fontWeight: 500,
    border: "1px solid var(--border)",
    borderRadius: "var(--radius)",
    background: "var(--bg-card)",
    color: "var(--text)",
    cursor: "pointer",
    transition: "all .15s",
  },
  btnPrimary: {
    background: "var(--accent)",
    borderColor: "var(--accent)",
    color: "#fff",
  },
  status: { fontSize: 13, color: "var(--text-dim)", marginTop: 12, lineHeight: 1.4 },
  fileList: { marginTop: 16 },
  fileListTitle: { fontSize: 12, color: "var(--text-dim)", marginBottom: 6 },
  fileItem: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    fontSize: 13,
    color: "var(--text)",
    padding: "5px 0",
  },
  fileIcon: { fontSize: 16 },
};
