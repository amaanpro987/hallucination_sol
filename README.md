# 🛡️ DataForge Hallucination Auditor

**Audit-grade hallucination detection with citation grounding.**

A full-stack application that verifies LLM-generated text against trusted source documents, providing:

- **Claim-level labels**: Supported ✅ / Contradicted 🔴 / Unverifiable 🟡
- **Citations** to exact source spans (document → page → paragraph → snippet)
- **Corrections** for contradicted claims
- **Split-pane UI**: click a claim → scroll to evidence, plus a document-level trust meter

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  React Frontend (Vite)                                   │
│  ┌────────────┐ ┌─────────────┐ ┌──────────────────────┐│
│  │ Upload     │ │ Output Panel│ │ Source Viewer (PDF.js)││
│  │ Verify Form│ │ (Green/Red/ │ │ Evidence Panel        ││
│  │            │ │  Yellow)    │ │ Trust Meter           ││
│  └────────────┘ └─────────────┘ └──────────────────────┘│
└──────────────────────┬───────────────────────────────────┘
                       │  REST API
┌──────────────────────▼───────────────────────────────────┐
│  FastAPI Backend                                         │
│  ┌──────────────────────────────────────────────────────┐│
│  │  Verification Pipeline                               ││
│  │  1. Claim Decomposition (sentences → atomic claims)  ││
│  │  2. Hybrid Retrieval (FAISS dense + BM25 sparse)     ││
│  │  3. Cross-encoder Reranking                          ││
│  │  4. Two-layer Verification                           ││
│  │     a. Deterministic (numeric/date checks)           ││
│  │     b. NLI (entailment/contradiction/neutral)        ││
│  │  5. Citation Grounding (exact snippet + offsets)     ││
│  │  6. Correction Engine (template + evidence-based)    ││
│  │  7. Trust Score (weighted, with penalties)           ││
│  └──────────────────────────────────────────────────────┘│
│  Storage: SQLite │ FAISS index │ BM25 index              │
└──────────────────────────────────────────────────────────┘
```

---

## Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 18+
- (Optional) Docker & Docker Compose

### 1. Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run the server
python run.py
```

The API will be available at **http://localhost:8000**.  
Swagger docs: **http://localhost:8000/docs**

### 2. Frontend

```bash
cd frontend

npm install
npm run dev
```

The UI will be available at **http://localhost:5173**.  
API calls are proxied to the backend automatically.

### 3. Docker Compose (full stack)

```bash
docker-compose up --build
```

- Frontend → **http://localhost:3000**
- Backend API → **http://localhost:8000**

---

## Usage Flow

1. **Upload** — Drag-drop PDF or TXT source documents
2. **Ingest** — Click "Ingest & Index" to parse, chunk, and build search indexes
3. **Verify** — Paste LLM-generated text and click "Verify"
4. **Review** — Explore the split-pane results:
   - **Left**: LLM output with per-claim color coding (Green/Red/Yellow)
   - **Right top**: PDF viewer that auto-scrolls to evidence
   - **Right bottom**: Evidence details with NLI scores
   - **Top bar**: Trust meter + filter controls

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/sources/upload` | Upload PDF/TXT files |
| `POST` | `/sources/ingest` | Trigger ingestion (async) |
| `GET` | `/sources` | List uploaded documents |
| `GET` | `/sources/{id}/pdf` | Stream PDF for viewer |
| `GET` | `/jobs/{id}` | Check ingestion job status |
| `POST` | `/verify` | Start verification run (async) |
| `GET` | `/runs` | List all verification runs |
| `GET` | `/runs/{id}` | Get full annotated results |
| `GET` | `/health` | Health check |

---

## Verification Pipeline Details

### Claim Decomposition
- Splits LLM text into sentences, then into atomic claims
- Tags each claim: `numeric_date`, `entity_relation`, `negation`, `causal`, `definition`, `general`
- Assigns risk weights (numeric/negation claims weigh more)

### Hybrid Retrieval
- **Dense**: Sentence-transformer embeddings → FAISS cosine similarity
- **Sparse**: BM25 for exact-match (dates, numbers, names)
- **Rerank**: Cross-encoder reranker selects top 5 passages

### Two-Layer Verification
- **Layer 1 — Deterministic**: Extracts numbers/dates from claim + evidence, compares with tolerance
- **Layer 2 — NLI**: DeBERTa-v3 NLI model scores entailment/contradiction/neutral per evidence passage

### Trust Score
```
Overall  = 100 × ( Σ weight_i × score_i ) / Σ weight_i  −  critical_penalties

score: Supported=1.0, Unverifiable=0.5, Contradicted=0.0
penalty: 5 pts per high-risk contradiction (numeric/negation/causal)
```

Also computes:
- **Faithfulness** = Supported / (Supported + Contradicted)
- **Groundedness** = Supported / (Supported + Unverifiable)

---

## Models Used (no retraining required)

| Role | Model | Size |
|------|-------|------|
| Embeddings | `all-MiniLM-L6-v2` | ~80 MB |
| Reranker | `ms-marco-MiniLM-L-6-v2` | ~80 MB |
| NLI Verifier | `nli-deberta-v3-base` | ~400 MB |

Models are downloaded automatically on first use.

---

## Project Structure

```
product1_hall/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + lifespan
│   │   ├── config.py            # Settings (env-driven)
│   │   ├── database.py          # SQLAlchemy ORM models
│   │   ├── models.py            # Pydantic schemas
│   │   ├── routers/
│   │   │   ├── sources.py       # Upload / ingest
│   │   │   ├── verify.py        # Verification trigger
│   │   │   └── runs.py          # Run & job retrieval
│   │   ├── services/
│   │   │   ├── ingestion.py     # PDF parse → chunk → index
│   │   │   ├── claim_decomposer.py
│   │   │   ├── retriever.py     # FAISS + BM25 + rerank
│   │   │   ├── verifier.py      # Deterministic + NLI
│   │   │   ├── citation.py      # Snippet extraction
│   │   │   ├── correction.py    # Fix generation
│   │   │   ├── trust_score.py   # Scoring
│   │   │   └── orchestrator.py  # Full pipeline
│   │   └── utils/
│   │       ├── pdf_parser.py    # PyMuPDF extraction
│   │       └── text_utils.py    # Sentence split, nums, dates
│   ├── requirements.txt
│   ├── run.py
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx / App.css
│   │   ├── api/client.js
│   │   ├── components/
│   │   │   ├── TrustMeter.jsx
│   │   │   ├── FilterBar.jsx
│   │   │   ├── OutputPanel.jsx
│   │   │   ├── SourceViewer.jsx
│   │   │   ├── EvidencePanel.jsx
│   │   │   ├── UploadPanel.jsx
│   │   │   └── VerifyForm.jsx
│   │   └── utils/colors.js
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Configuration

All backend settings can be overridden via environment variables prefixed with `AUDITOR_`:

| Variable | Default | Description |
|----------|---------|-------------|
| `AUDITOR_EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformer model |
| `AUDITOR_NLI_MODEL` | `cross-encoder/nli-deberta-v3-base` | NLI model |
| `AUDITOR_NLI_CONTRADICT_THRESHOLD` | `0.70` | Min contradiction score |
| `AUDITOR_NLI_ENTAIL_THRESHOLD` | `0.65` | Min entailment score |
| `AUDITOR_DENSE_TOP_K` | `20` | Dense retrieval candidates |
| `AUDITOR_BM25_TOP_K` | `20` | BM25 retrieval candidates |
| `AUDITOR_RERANK_TOP_K` | `5` | Final evidence passages |

---

## License

Internal / proprietary — DataForge
