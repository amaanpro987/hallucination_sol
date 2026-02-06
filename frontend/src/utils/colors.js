/** Label → colour mapping */
export const LABEL_COLORS = {
  SUPPORTED:    { text: "var(--green)",  bg: "var(--green-bg)",  label: "Supported"    },
  CONTRADICTED: { text: "var(--red)",    bg: "var(--red-bg)",    label: "Contradicted" },
  UNVERIFIABLE: { text: "var(--yellow)", bg: "var(--yellow-bg)", label: "Unverifiable" },
};

export function labelColor(label) {
  return LABEL_COLORS[label] || LABEL_COLORS.UNVERIFIABLE;
}

/** Trust score → colour */
export function trustColor(score) {
  if (score >= 80) return "var(--green)";
  if (score >= 50) return "var(--yellow)";
  return "var(--red)";
}
