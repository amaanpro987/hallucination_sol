import React, { useState } from "react";
import { quickSyntheticEvaluation } from "../api/client";

/**
 * Evaluation Dashboard
 * Run evaluations and view metrics
 */
export default function EvaluationDashboard() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const runQuickEvaluation = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await quickSyntheticEvaluation();
      setResults(data);
    } catch (err) {
      setError(err.message || "Evaluation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>📊 Evaluation Dashboard</h1>
        <p style={styles.subtitle}>
          Test system accuracy on benchmark datasets
        </p>
      </div>

      <div style={styles.controls}>
        <button
          style={styles.runBtn}
          onClick={runQuickEvaluation}
          disabled={loading}
        >
          {loading ? "⏳ Running..." : "▶️ Run Quick Evaluation (Synthetic)"}
        </button>
      </div>

      {error && (
        <div style={styles.errorBox}>
          <strong>❌ Error:</strong> {error}
        </div>
      )}

      {results && (
        <div style={styles.results}>
          {/* Summary Metrics */}
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>Summary Metrics</h2>
            <div style={styles.metricsGrid}>
              <MetricCard
                label="Accuracy"
                value={(results.summary.accuracy * 100).toFixed(1) + "%"}
                color="var(--accent)"
              />
              <MetricCard
                label="Precision"
                value={(results.summary.precision * 100).toFixed(1) + "%"}
                color="var(--green)"
              />
              <MetricCard
                label="Recall"
                value={(results.summary.recall * 100).toFixed(1) + "%"}
                color="var(--yellow)"
              />
              <MetricCard
                label="F1-Score"
                value={(results.summary.f1_score * 100).toFixed(1) + "%"}
                color="var(--accent)"
              />
            </div>
          </div>

          {/* Confusion Matrix */}
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>Confusion Matrix</h2>
            <ConfusionMatrix matrix={results.confusion_matrix} />
          </div>

          {/* Binary Classification (Hallucination Detection) */}
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>
              Hallucination Detection (Binary)
            </h2>
            <p style={styles.description}>
              Treating CONTRADICTED as positive (hallucination), others as negative
            </p>
            <div style={styles.binaryGrid}>
              <BinaryMetric
                label="True Positives"
                value={results.binary_classification.true_positives}
                subtitle="Correctly detected hallucinations"
                color="var(--green)"
              />
              <BinaryMetric
                label="False Negatives"
                value={results.binary_classification.false_negatives}
                subtitle="Missed hallucinations (CRITICAL)"
                color="var(--red)"
              />
              <BinaryMetric
                label="False Positives"
                value={results.binary_classification.false_positives}
                subtitle="False alarms"
                color="var(--yellow)"
              />
              <BinaryMetric
                label="True Negatives"
                value={results.binary_classification.true_negatives}
                subtitle="Correctly identified faithful"
                color="var(--green)"
              />
            </div>
          </div>

          {/* Per-Class Metrics */}
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>Per-Class Metrics</h2>
            <div style={styles.classMetrics}>
              <ClassMetrics
                label="SUPPORTED"
                metrics={results.per_class_metrics.SUPPORTED}
                color="var(--green)"
              />
              <ClassMetrics
                label="CONTRADICTED"
                metrics={results.per_class_metrics.CONTRADICTED}
                color="var(--red)"
              />
              <ClassMetrics
                label="UNVERIFIABLE"
                metrics={results.per_class_metrics.UNVERIFIABLE}
                color="var(--yellow)"
              />
            </div>
          </div>

          {/* Error Analysis */}
          {results.error_analysis && (
            <div style={styles.section}>
              <h2 style={styles.sectionTitle}>Error Analysis</h2>
              <div style={styles.errorAnalysis}>
                <div style={styles.errorStat}>
                  <span style={{ ...styles.errorLabel, color: "var(--red)" }}>
                    False Negatives (Missed Hallucinations)
                  </span>
                  <span style={styles.errorCount}>
                    {results.error_analysis.false_negatives.count}
                  </span>
                </div>
                <div style={styles.errorStat}>
                  <span style={{ ...styles.errorLabel, color: "var(--yellow)" }}>
                    False Positives (False Alarms)
                  </span>
                  <span style={styles.errorCount}>
                    {results.error_analysis.false_positives.count}
                  </span>
                </div>
              </div>
              {results.error_analysis.recommendations.length > 0 && (
                <div style={styles.recommendations}>
                  <h3 style={styles.recTitle}>Recommendations</h3>
                  <ul style={styles.recList}>
                    {results.error_analysis.recommendations.map((rec, i) => (
                      <li key={i} style={styles.recItem}>
                        💡 {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, color }) {
  return (
    <div style={styles.metricCard}>
      <div style={styles.metricLabel}>{label}</div>
      <div style={{ ...styles.metricValue, color }}>{value}</div>
    </div>
  );
}

function BinaryMetric({ label, value, subtitle, color }) {
  return (
    <div style={styles.binaryCard}>
      <div style={{ ...styles.binaryValue, color }}>{value}</div>
      <div style={styles.binaryLabel}>{label}</div>
      <div style={styles.binarySubtitle}>{subtitle}</div>
    </div>
  );
}

function ClassMetrics({ label, metrics, color }) {
  return (
    <div style={styles.classCard}>
      <div style={{ ...styles.classLabel, color }}>{label}</div>
      <div style={styles.classValues}>
        <div style={styles.classMetric}>
          <span>Precision:</span>
          <strong>{(metrics.precision * 100).toFixed(1)}%</strong>
        </div>
        <div style={styles.classMetric}>
          <span>Recall:</span>
          <strong>{(metrics.recall * 100).toFixed(1)}%</strong>
        </div>
        <div style={styles.classMetric}>
          <span>F1:</span>
          <strong>{(metrics.f1_score * 100).toFixed(1)}%</strong>
        </div>
      </div>
    </div>
  );
}

function ConfusionMatrix({ matrix }) {
  const labels = ["SUPPORTED", "CONTRADICTED", "UNVERIFIABLE"];
  const shortLabels = ["SUP", "CON", "UNV"];

  return (
    <div style={styles.confusionContainer}>
      <div style={styles.confusionMatrix}>
        {/* Header */}
        <div style={styles.confusionHeader}>
          <div style={styles.confusionCorner}></div>
          <div style={styles.confusionTopLabel}>Predicted</div>
        </div>
        <div style={styles.confusionColHeaders}>
          <div style={styles.confusionCorner}></div>
          {shortLabels.map((label) => (
            <div key={label} style={styles.confusionColHeader}>
              {label}
            </div>
          ))}
        </div>

        {/* Rows */}
        <div style={styles.confusionSideLabel}>True</div>
        {labels.map((trueLabel, i) => (
          <div key={trueLabel} style={styles.confusionRow}>
            <div style={styles.confusionRowHeader}>{shortLabels[i]}</div>
            {labels.map((predLabel) => {
              const value = matrix[trueLabel]?.[predLabel] || 0;
              return (
                <div key={predLabel} style={styles.confusionCell}>
                  {value}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: "100vh",
    background: "var(--bg)",
    padding: "20px",
  },
  header: {
    maxWidth: 1200,
    margin: "0 auto 20px",
    textAlign: "center",
  },
  title: {
    fontSize: 28,
    fontWeight: 700,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: "var(--text-dim)",
  },
  controls: {
    maxWidth: 1200,
    margin: "0 auto 20px",
    textAlign: "center",
  },
  runBtn: {
    padding: "12px 24px",
    fontSize: 14,
    fontWeight: 600,
    background: "var(--accent)",
    color: "white",
    border: "none",
    borderRadius: "var(--radius)",
    cursor: "pointer",
    transition: "opacity .2s",
  },
  errorBox: {
    maxWidth: 1200,
    margin: "0 auto 20px",
    padding: "12px 16px",
    background: "var(--red-bg)",
    color: "var(--red)",
    borderRadius: "var(--radius)",
    border: "1px solid var(--red)",
  },
  results: {
    maxWidth: 1200,
    margin: "0 auto",
  },
  section: {
    background: "var(--bg-panel)",
    borderRadius: "var(--radius)",
    padding: 20,
    marginBottom: 20,
    border: "1px solid var(--border)",
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 600,
    marginBottom: 16,
  },
  description: {
    fontSize: 13,
    color: "var(--text-dim)",
    marginBottom: 16,
  },
  metricsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
    gap: 12,
  },
  metricCard: {
    background: "var(--bg-card)",
    padding: 16,
    borderRadius: "var(--radius)",
    textAlign: "center",
    border: "1px solid var(--border)",
  },
  metricLabel: {
    fontSize: 12,
    color: "var(--text-dim)",
    marginBottom: 8,
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 700,
  },
  binaryGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
    gap: 12,
  },
  binaryCard: {
    background: "var(--bg-card)",
    padding: 16,
    borderRadius: "var(--radius)",
    textAlign: "center",
    border: "1px solid var(--border)",
  },
  binaryValue: {
    fontSize: 32,
    fontWeight: 700,
    marginBottom: 4,
  },
  binaryLabel: {
    fontSize: 13,
    fontWeight: 600,
    marginBottom: 4,
  },
  binarySubtitle: {
    fontSize: 11,
    color: "var(--text-dim)",
  },
  classMetrics: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
    gap: 12,
  },
  classCard: {
    background: "var(--bg-card)",
    padding: 16,
    borderRadius: "var(--radius)",
    border: "1px solid var(--border)",
  },
  classLabel: {
    fontSize: 14,
    fontWeight: 700,
    marginBottom: 12,
    textTransform: "uppercase",
  },
  classValues: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  classMetric: {
    display: "flex",
    justifyContent: "space-between",
    fontSize: 13,
  },
  confusionContainer: {
    display: "flex",
    justifyContent: "center",
  },
  confusionMatrix: {
    display: "inline-grid",
    gridTemplateColumns: "auto auto auto auto auto",
    gap: 0,
    fontSize: 13,
  },
  confusionHeader: {
    gridColumn: "1 / -1",
    display: "flex",
    alignItems: "center",
    marginBottom: 4,
  },
  confusionCorner: {
    width: 60,
  },
  confusionTopLabel: {
    flex: 1,
    textAlign: "center",
    fontWeight: 600,
    fontSize: 12,
    color: "var(--text-dim)",
  },
  confusionColHeaders: {
    gridColumn: "1 / -1",
    display: "flex",
    marginBottom: 4,
  },
  confusionColHeader: {
    flex: 1,
    textAlign: "center",
    fontWeight: 600,
    fontSize: 11,
    minWidth: 60,
  },
  confusionSideLabel: {
    gridRow: "3 / 6",
    gridColumn: 1,
    writingMode: "vertical-lr",
    transform: "rotate(180deg)",
    textAlign: "center",
    fontWeight: 600,
    fontSize: 12,
    color: "var(--text-dim)",
    padding: "0 8px",
  },
  confusionRow: {
    gridColumn: "2 / -1",
    display: "flex",
    gap: 4,
  },
  confusionRowHeader: {
    width: 60,
    textAlign: "right",
    fontWeight: 600,
    fontSize: 11,
    paddingRight: 8,
  },
  confusionCell: {
    flex: 1,
    minWidth: 60,
    padding: "8px",
    background: "var(--bg-card)",
    border: "1px solid var(--border)",
    textAlign: "center",
    fontWeight: 600,
  },
  errorAnalysis: {
    display: "flex",
    gap: 16,
    marginBottom: 16,
  },
  errorStat: {
    flex: 1,
    background: "var(--bg-card)",
    padding: 16,
    borderRadius: "var(--radius)",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 8,
  },
  errorLabel: {
    fontSize: 13,
    fontWeight: 600,
  },
  errorCount: {
    fontSize: 28,
    fontWeight: 700,
  },
  recommendations: {
    background: "var(--bg-card)",
    padding: 16,
    borderRadius: "var(--radius)",
  },
  recTitle: {
    fontSize: 14,
    fontWeight: 600,
    marginBottom: 12,
  },
  recList: {
    margin: 0,
    paddingLeft: 20,
  },
  recItem: {
    fontSize: 13,
    marginBottom: 8,
    lineHeight: 1.5,
  },
};
