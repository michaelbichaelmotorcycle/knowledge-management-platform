# Lead Architect Status Report — Unit 5 Alpha Release
## Knowledge Management Platform (feature/fix-test-and-ci-failures branch)

**Saved**: 2026-09-12
**Branch**: `feature/fix-test-and-ci-failures` (based on `develop`)
**Commit**: `3b05cfe` — "Fix CI failures: lazy init for LLM/embedding, JWT dev fallback, dedupe requirements, frontend lint, add Docker infra"

---

## 1. Local Infrastructure Audit — ✅ READY (with caveats)

**Docker Compose** (`docker-compose.yml`): Defined and working. Three services:
- **db**: `ankane/pgvector:latest` with `kma_user:kma_password` credentials, port 5432, healthcheck configured
- **backend**: Python 3.11 image, runs `alembic upgrade head` then `uvicorn app.main:app --reload`, port 8000, depends on db healthcheck
- **frontend**: Node 20 build → nginx serve, port 5173, proxies `/api/` to backend

**Verified locally**: All 3 containers start, DB is healthy, migrations apply, backend serves `/health`, frontend serves HTTP 200.

**pgvector config**: The migration `fd4969cd9550_create_documents_and_document_chunks.py` creates the `vector` extension. A later migration `b79ee6c8ae25_change_embedding_dimension_to_384.py` sets the dimension to **384** (matching the `all-MiniLM-L6-v2` model used by `fastembed`). The `app/models/chunk.py` uses `pgvector.sqlalchemy.Vector` for the embedding column.

**⚠️ Caveat — credential mismatch**: The team's `app/core/config.py` defaults to `postgresql://kma_user:kma_password@localhost:5432/kma`, but the CI workflow uses `test:test@localhost:5432/kma_test`. The docker-compose matches the app's default. If you run tests locally, you need `DATABASE_URL` set to the docker-compose DB.

---

## 2. Pipeline Integration Check — ⚠️ PARTIAL

### Text Extraction (`app/services/pdf_extraction.py`)
- ✅ PDF extraction via `pypdf` — extracts text per page, skips empty pages
- ✅ TXT extraction via UTF-8 decode in `app/api/documents.py`
- ❌ No DOCX support (only `.txt` and `.pdf` accepted; other types rejected with 400)
- ⚠️ No chunk-level failure logging — the upload endpoint (`documents.py:80-95`) chunks and embeds in a single loop with no try/except. If one chunk's embedding fails, the entire upload fails with no isolation.

### Chunking (`app/services/chunking.py`)
- ✅ Overlapping chunker (500 chars, 50 overlap by default)
- ✅ Returns `list[str]` — simple, directly consumable by the embedding service
- ⚠️ No position/index tracking — chunks are plain strings, no metadata for failure isolation

### Embedding (`app/services/embedding.py`)
- ✅ Uses `fastembed` with `all-MiniLM-L6-v2` (384 dimensions) — matches the DB schema
- ✅ Lazy initialization (my fix) — module imports without downloading the model
- ⚠️ **Not AWS Bedrock** — the team chose `fastembed` (local ONNX model) for embeddings, not Bedrock Titan. If your architecture requires Bedrock, this needs to be swapped.

### LLM (`app/services/llm.py`)
- ✅ Uses Google Gemini (`google-genai`) — lazy initialization (my fix)
- ⚠️ **Not AWS Bedrock** — the team chose Google Gemini, not AWS Bedrock Claude. If your architecture specifies Bedrock, this is a mismatch.

### RAG Pipeline (`app/services/rag.py`)
- ✅ `retrieve_context()` — semantic search → joins to documents → returns `list[dict]` with `content`, `document_id`, `filename`
- ✅ `build_prompt()` — assembles a well-structured RAG prompt with rules ("answer only from context", "don't invent information")
- ✅ The `/documents/ask` endpoint (`documents.py:206`) returns `answer` + `sources` with document attribution

### Search (`app/services/search.py`)
- ✅ Uses pgvector `cosine_distance` with `MAX_DISTANCE = 0.70` threshold
- ✅ Role-based access: admins search all, users search only their own documents

**Verdict**: The pipeline is wired correctly end-to-end (upload → extract → chunk → embed → store → search → retrieve → prompt → answer). However, (a) there's no chunk-level failure logging, (b) the team used Google Gemini + fastembed instead of AWS Bedrock, and (c) DOCX isn't supported.

---

## 3. CI/CD Status — ✅ PASSING (after my fixes)

I ran every CI step locally. Current state on `feature/fix-test-and-ci-failures`:

| CI Job | Status | Notes |
|--------|--------|-------|
| `build` (lint + frontend build) | ✅ Pass | ruff clean, eslint clean, vite build succeeds |
| `db-schema` (pgvector + alembic) | ✅ Pass | 4 migrations apply cleanly |
| `ingestion` (upload/extraction/chunking tests) | ✅ Pass | 9 tests pass |
| `embed-store` (embeddings/storage tests) | ✅ Pass | 4 tests pass |
| `retrieval` (semantic search tests) | ✅ Pass | 4 tests pass |
| `rag-llm` (RAG integration, mocked LLM) | ✅ Pass | 7 tests pass |
| `e2e-smoke` (grounded Q&A with sources) | ✅ Pass | 5 tests pass (requires seed data) |
| `auth` (JWT auth tests) | ✅ Pass | 3 tests pass |

**Total: 32/32 tests pass.** All lint clean. Frontend builds.

**Fixes I applied to make CI pass:**
1. `auth.py` — was crashing at import without `JWT_SECRET_KEY`; now falls back to a dev default
2. `llm.py` — was calling `genai.Client()` at import; now lazy-init
3. `embedding.py` — was downloading model at import; now lazy-init
4. `requirements.txt` — removed duplicate entries
5. `App.jsx` — fixed `useEffect` declaration order + lint rule

**⚠️ CI caveat**: The `e2e-smoke` job requires the seed script to run first (it creates user `ci_admin` + 3 documents). The CI workflow does run `python -m scripts.seed_test_data` before the e2e tests (line 281), so this is handled. But locally you must run it manually.

---

## 4. Lead Architect Action Items

### 🔴 Must-fix before Alpha submission
1. **Decide on Bedrock vs. Gemini/fastembed** — Your stated architecture uses AWS Bedrock, but the team implemented Google Gemini + fastembed. If Bedrock is a hard requirement, you need to:
   - Replace `embedding.py` with a Bedrock Titan client (boto3)
   - Replace `llm.py` with a Bedrock Claude client (boto3)
   - Update the embedding dimension from 384 to 1024 (Titan) and add a migration
   - Add `boto3` to requirements, remove `google-genai` and `fastembed`
   - If the team's choice of Gemini/fastembed is acceptable, document the decision in an ADR

2. **Add chunk-level failure logging** — Your requirement states "chunk logging for failure isolation." The current upload endpoint (`documents.py:80-95`) has no try/except around individual chunk embedding. Wrap each chunk's embed+store in a try/except that logs the chunk index and error, so a single failure doesn't abort the whole document.

3. **Push the feature branch and open a PR to `develop`** — The fixes are committed on `feature/fix-test-and-ci-failures`. Push it and open a PR with base `develop` so CI runs on it.

### 🟡 Should-fix before Alpha
4. **Add a `.env.example`** — Document `DATABASE_URL`, `JWT_SECRET_KEY`, `GEMINI_API_KEY` (or Bedrock equivalents) so teammates can set up locally
5. **Add DOCX support** — Add `python-docx` to requirements and a `.docx` branch in the upload endpoint
6. **Add an `ARCHITECTURE.md`** — Document the pipeline stages, the mock-vs-real LLM switch, and the service boundaries (the CI workflow comments reference backlog IDs but there's no architecture doc)
7. **Add a root `README.md`** — Local setup instructions (`docker compose up`, `alembic upgrade head`, `python scripts/seed_test_data.py`)

### 🟢 Nice-to-have (post-Alpha)
8. **Add a `Makefile`** — Standardize `make up`, `make migrate`, `make seed`, `make test`
9. **Consolidate CI test jobs** — Currently 6 separate jobs each spin up a Postgres container; consider a single `test` job for faster feedback
10. **Add frontend lint to CI** — The CI workflow doesn't run `npm run lint`; only `npm run build`

---

## Summary

| Area | Status |
|------|--------|
| Local Docker infra | ✅ Working (docker-compose.yml + Dockerfiles added) |
| pgvector DB | ✅ Migrations apply, 384-dim vectors match fastembed model |
| Text extraction | ✅ PDF + TXT working; ❌ no DOCX; ⚠️ no chunk failure logging |
| RAG pipeline | ✅ End-to-end working (search → retrieve → prompt → answer with sources) |
| LLM/Embedding | ⚠️ Uses Google Gemini + fastembed, NOT AWS Bedrock |
| CI/CD | ✅ All 32 tests pass, lint clean, builds succeed (after my fixes) |
| Git workflow | ✅ Fixes committed on `feature/fix-test-and-ci-failures`, ready for PR to `develop` |

**Bottom line**: The codebase builds, lints, and passes all 32 tests. The Docker stack runs locally. The main open question is whether the team's Google Gemini + fastembed choice is acceptable or if you need to swap to AWS Bedrock as your architecture specifies. The chunk-level failure logging also needs to be added to meet your stated requirement.

---

## How to resume

```bash
cd knowledge-management-platform
git checkout feature/fix-test-and-ci-failures

# Start the Docker stack
docker compose up -d --build

# Run migrations + seed data
cd backend
python run_migrations.py
set PYTHONPATH=. && set DATABASE_URL=postgresql://kma_user:kma_password@localhost:5432/kma && set JWT_SECRET_KEY=dev-only-secret-key-change-in-production && python scripts/seed_test_data.py

# Run tests
set DATABASE_URL=postgresql://kma_user:kma_password@localhost:5432/kma && set JWT_SECRET_KEY=dev-only-secret-key-change-in-production && python -m pytest tests/ -v

# Push and open PR
git push origin feature/fix-test-and-ci-failures
# Then open PR with base=develop on GitHub
```
