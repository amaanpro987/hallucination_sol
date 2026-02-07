import React, { useState, useEffect, useRef } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/esm/Page/AnnotationLayer.css";
import "react-pdf/dist/esm/Page/TextLayer.css";

// Configure worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

/**
 * PDF Viewer with auto-scroll to specific page
 */
export default function PDFViewer({ docId, targetPage, onLoadSuccess }) {
  const [numPages, setNumPages] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const containerRef = useRef(null);
  const pageRefs = useRef({});

  // Load PDF URL from backend
  useEffect(() => {
    if (!docId) return;
    
    const url = `http://localhost:8000/sources/${docId}/pdf`;
    setPdfUrl(url);
    setLoading(true);
    setError(null);
  }, [docId]);

  // Auto-scroll to target page
  useEffect(() => {
    if (targetPage && pageRefs.current[targetPage]) {
      setTimeout(() => {
        pageRefs.current[targetPage]?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }, 300);
    }
  }, [targetPage, numPages]);

  const handleLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
    setLoading(false);
    if (onLoadSuccess) onLoadSuccess(numPages);
  };

  const handleLoadError = (error) => {
    console.error("PDF load error:", error);
    setError("Failed to load PDF");
    setLoading(false);
  };

  if (!docId) {
    return (
      <div style={styles.placeholder}>
        <div style={styles.icon}>📄</div>
        <p>Select a claim to view source PDF</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.placeholder}>
        <div style={styles.errorIcon}>⚠️</div>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div style={styles.container} ref={containerRef}>
      {loading && (
        <div style={styles.loading}>
          <div style={styles.spinner}>⏳</div>
          <p>Loading PDF...</p>
        </div>
      )}
      
      <Document
        file={pdfUrl}
        onLoadSuccess={handleLoadSuccess}
        onLoadError={handleLoadError}
        loading=""
      >
        {Array.from(new Array(numPages), (el, index) => (
          <div
            key={`page_${index + 1}`}
            ref={(el) => (pageRefs.current[index + 1] = el)}
            style={styles.pageWrapper}
          >
            <div style={styles.pageNumber}>Page {index + 1}</div>
            <Page
              pageNumber={index + 1}
              width={Math.min(800, window.innerWidth * 0.4)}
              renderTextLayer={true}
              renderAnnotationLayer={true}
            />
          </div>
        ))}
      </Document>
    </div>
  );
}

const styles = {
  container: {
    height: "100%",
    overflowY: "auto",
    background: "var(--bg)",
    padding: "16px",
  },
  pageWrapper: {
    marginBottom: "16px",
    border: "1px solid var(--border)",
    borderRadius: "var(--radius)",
    overflow: "hidden",
    background: "white",
    boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
  },
  pageNumber: {
    padding: "8px 12px",
    background: "var(--bg-panel)",
    fontSize: "12px",
    fontWeight: 600,
    color: "var(--text-dim)",
    borderBottom: "1px solid var(--border)",
  },
  placeholder: {
    height: "100%",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    color: "var(--text-dim)",
    fontSize: "14px",
  },
  icon: { fontSize: "48px", marginBottom: "12px", opacity: 0.5 },
  errorIcon: { fontSize: "48px", marginBottom: "12px" },
  loading: {
    position: "absolute",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    textAlign: "center",
    color: "var(--text-dim)",
  },
  spinner: { fontSize: "32px", marginBottom: "8px" },
};
