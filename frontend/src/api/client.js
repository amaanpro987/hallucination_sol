/**
 * API client — thin wrapper around fetch.
 */
const BASE = "";          // proxied via Vite in dev

async function request(method, path, body, isFormData = false) {
  const opts = { method, headers: {} };
  if (body && !isFormData) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  } else if (body && isFormData) {
    // Let the browser set the multipart boundary automatically
    opts.body = body;
  }
  const res = await fetch(`${BASE}${path}`, opts);
  if (!res.ok) {
    let text;
    try { text = await res.text(); } catch { text = res.statusText; }
    throw new Error(`${res.status}: ${text}`);
  }
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return res.json();
  }
  return res.text();
}

// ── Sources ────────────────────────────────────────────────
export function uploadSources(files, sourceSetId = "default") {
  const fd = new FormData();
  for (const f of files) fd.append("files", f);
  return request("POST", `/sources/upload?source_set_id=${sourceSetId}`, fd, true);
}

export function ingestSources(sourceSetId = "default") {
  return request("POST", "/sources/ingest", { source_set_id: sourceSetId });
}

export function listSources(sourceSetId = "default") {
  return request("GET", `/sources?source_set_id=${sourceSetId}`);
}

export function getPdfUrl(docId) {
  return `${BASE}/sources/${docId}/pdf`;
}

// ── Jobs ───────────────────────────────────────────────────
export function getJob(jobId) {
  return request("GET", `/jobs/${jobId}`);
}

// ── Verification ───────────────────────────────────────────
export function startVerification(llmOutput, sourceSetId = "default", runName = "Untitled run") {
  return request("POST", "/verify", {
    run_name: runName,
    llm_output: llmOutput,
    source_set_id: sourceSetId,
  });
}

// ── Runs ───────────────────────────────────────────────────
export function listRuns() {
  return request("GET", "/runs");
}

export function getRun(runId) {
  return request("GET", `/runs/${runId}`);
}
