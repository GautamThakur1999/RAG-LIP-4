# Implementation Plan — Mutual Fund FAQ Assistant (Facts-Only RAG)

> Phase-wise, build-from-zero plan for the assistant defined in [`context.md`](./context.md) and [`architecture.md`](./architecture.md).
> Written to be executed inside an **AI coding IDE (Cursor or Antigravity)** — each phase lists the files to create, the exact steps, a ready-to-paste **agent prompt**, and **acceptance criteria** (the "done" test).
>
> **Locked scope:** AMC = ICICI Prudential Mutual Fund · Schemes = Bluechip (large-cap), Flexicap, ELSS Tax Saver · Plan = **Direct – Growth** · Sources = official AMC site + AMFI/SEBI only.

---

## 0. Tech Stack (locked defaults)

| Concern | Choice | Why |
|---------|--------|-----|
| Language | **Python 3.11** | ecosystem for RAG |
| HTML parsing | `requests` + `beautifulsoup4` | static AMC pages |
| PDF parsing | `pdfplumber` (tables) + `PyMuPDF`/`fitz` (text) | KIM/SID/factsheet PDFs |
| Chunking | `langchain-text-splitters` (or custom) | section + token aware |
| Embeddings | `sentence-transformers` → **`BAAI/bge-small-en-v1.5`** (512-token, local, free) | matches ~400-tok chunks; offline |
| Vector store | **ChromaDB** (persistent) | built-in metadata filtering for scheme/plan |
| Keyword search | `rank-bm25` | hybrid retrieval (RRF fusion) |
| LLM | **Groq** (via groq python client) | incredibly fast inference, free tier available |
| UI | **Streamlit** | fast, single-file, satisfies welcome/examples/disclaimer |
| Tests | `pytest` + a JSON eval set | factual + refusal regression |
| Config | `.env` + `config.py` (pydantic-settings) | keys, model names, thresholds |

> Swap any row later; the architecture holds. If you have no LLM API key, use Ollama (e.g. `llama3.1:8b`) — the plan notes where.
>
> **Why ChromaDB instead of FAISS?** While FAISS is incredibly fast for pure vector math at massive scale, it lacks native metadata filtering. Our implementation strictly requires scheme-level metadata filtering (e.g., locking search to *only* Bluechip documents before doing vector math) to prevent hallucinating an expense ratio from a different fund. ChromaDB supports this natively, making it strictly superior for our specific RAG architecture.

---

## 1. Repository Layout (target)

```
mf-faq-rag/
├─ README.md
├─ requirements.txt
├─ .env.example                # keys + config (no secrets committed)
├─ .gitignore
├─ config.py                   # central settings (models, k, thresholds, paths)
├─ data/
│  ├─ sources.csv              # 15–25 official URLs (deliverable)
│  ├─ raw/                     # downloaded html/pdf cache
│  └─ processed/               # cleaned text + chunks.jsonl
├─ src/
│  ├─ ingest/
│  │  ├─ fetch.py              # download + cache raw pages/PDFs
│  │  ├─ parse.py              # html/pdf → clean text + tables
│  │  ├─ chunk.py              # chunking (token-aware + table/identity rules)
│  │  └─ build_index.py        # embed + write to Chroma + BM25 corpus
│  ├─ guardrails/
│  │  ├─ pii.py                # PII detect/block
│  │  └─ intent.py             # factual vs advisory vs out-of-scope
│  ├─ retrieve/
│  │  ├─ retriever.py          # hybrid search + scheme/plan filter + threshold
│  │  └─ scheme_match.py       # detect scheme name in query
│  └─ llm/
│     ├─ client.py             # Groq LLM call wrapper
│     ├─ prompt.py             # system prompt + answer contract
│     └─ answer.py             # orchestrates guardrail→retrieve→generate
├─ app/
│  └─ streamlit_app.py         # the UI
├─ eval/
│  ├─ testset.json             # factual + refusal cases
│  └─ run_eval.py              # pytest-style runner / report
└─ deliverables/
   ├─ sample_qa.md             # 5–10 Q&A with answers + links
   └─ disclaimer.md            # facts-only snippet
```

---

## 2. How to Drive Cursor / Antigravity (read first)

The plan is split into small phases so the AI agent stays accurate. Working method:

1. **Seed the IDE with context.** Put `context.md` + `architecture.md` in the repo and, at the start of each session, reference them: *"Follow context.md and architecture.md. Do not invent facts; the assistant answers only from the corpus."*
2. **Add a rules file** so the agent doesn't drift (Phase 0 creates it). Cursor: `.cursor/rules/rag.mdc`. Antigravity: its rules/memory panel — paste the same content.
3. **One phase per prompt.** Paste the phase's **agent prompt**, let it generate, then run the **acceptance check** before moving on. Don't batch phases.
4. **Always run the file before continuing.** Each phase has a runnable smoke test. Red → fix before next phase.
5. **Never let the model fabricate fund numbers.** All figures come from the corpus at runtime; code/tests must not hardcode an expense ratio as "truth."

**Global rules file content** (create in Phase 0):

```
- This is a facts-only mutual fund FAQ RAG. No investment advice, ever.
- Answers come ONLY from retrieved corpus chunks. If not retrieved, refuse.
- Every factual answer: <=3 sentences, exactly ONE source URL, footer
  "Last updated from sources: <date>".
- Never compute/compare returns. Redirect performance questions to the factsheet.
- Block PII (PAN, Aadhaar, account/folio, OTP, email, phone); never store it.
- Corpus = ICICI Prudential official site + AMFI/SEBI only. Plan = Direct-Growth.
- Prefer small, testable functions. Add a runnable __main__ smoke test per module.
```

---

## 3. Phase 0 — Project Setup & Skeleton

**Goal:** runnable empty project, config, deps, rules file.

**Steps**

1. Create the repo layout (§1) with empty modules and `if __name__ == "__main__":` stubs.
2. `requirements.txt`:

   ```
   requests
   beautifulsoup4
   pdfplumber
   pymupdf
   langchain-text-splitters
   sentence-transformers
   chromadb
   rank-bm25
   pydantic-settings
   python-dotenv
   streamlit
   pytest
   tqdm
   # LLM (pick one): openai  OR  anthropic  OR  ollama
   ```

3. `.env.example` → keys (`LLM_API_KEY`, `LLM_MODEL`), and tunables (`EMBED_MODEL=BAAI/bge-small-en-v1.5`, `TOP_K=5`, `SCORE_THRESHOLD=0.35`, `MAX_SENTENCES=3`).
4. `config.py` loads `.env` via pydantic-settings; expose typed settings.
5. Create the rules file (§2) and `.gitignore` (`.env`, `data/raw/`, `__pycache__/`, `*.sqlite3`, Chroma dir).
6. `python -m venv .venv` → activate → `pip install -r requirements.txt`.

**Agent prompt**
> Create the repository skeleton exactly as in implementation_plan.md §1, with empty modules that each have a `__main__` smoke-test stub printing the module name. Add requirements.txt, .env.example, config.py (pydantic-settings reading the listed env vars with sensible defaults), .gitignore, and the Cursor rules file from §2. Don't implement logic yet.

**Acceptance:** `pip install -r requirements.txt` succeeds; `python config.py` prints loaded settings; repo matches §1.

---

## 4. Phase 1 — Corpus Collection (`data/sources.csv`)

**Goal:** the 15–25 official URLs that define the corpus. **This is a graded deliverable** and gates everything downstream.

**Steps**

1. Collect official ICICI Prudential pages for the 3 schemes (Direct–Growth) + cross-cutting docs. Target mix:
   - Scheme **overview/snapshot** page ×3 (fund manager, category, inception, expense ratio, min SIP) — Bluechip, Flexicap, ELSS Tax Saver.
   - **Factsheet** (monthly) PDF — covers all 3 (1–2 URLs).
   - **KIM** and **SID** PDFs for the schemes (2–4 URLs).
   - **Fees/expense** and **exit load** pages/sections.
   - **Riskometer / benchmark** notes.
   - **Statement / capital-gains / tax** download guides (AMC + CAMS/KFintech if official).
   - **AMFI** and **SEBI** investor-education pages (for refusal fallbacks + general facts like ELSS lock-in).
2. Verify each URL is official (icicipruamc.com, amfiindia.com, sebi.gov.in). **No Groww/aggregator/blog links.**
3. Write `sources.csv`: `url, source_type, scheme, title, fetched_date`. `source_type` ∈ {overview, factsheet, kim, sid, fees, riskometer, statement_guide, amfi, sebi}. `scheme` = bluechip/flexicap/elss/common.

**Agent prompt**
> Help me assemble data/sources.csv with 15–25 official URLs per implementation_plan.md §4 for ICICI Prudential Bluechip, Flexicap, and ELSS Tax Saver (Direct–Growth), plus AMFI/SEBI education pages. Only icicipruamc.com, amfiindia.com, sebi.gov.in. Output CSV with columns url, source_type, scheme, title, fetched_date. Flag any URL you are unsure is official so I can verify.

**Acceptance:** 15–25 rows; every URL opens and is official; all three schemes + statement/tax + AMFI/SEBI represented. (You/I verify URLs manually — don't trust generated links blindly.)

---

## 5. Phase 2 — Ingestion Pipeline (corpus → index)

**Goal:** turn `sources.csv` into a persisted vector index + BM25 corpus with clean, well-chunked, metadata-rich text.

### 5a. `fetch.py`

- Read `sources.csv`; download each URL to `data/raw/` (hash filename). Respect `robots.txt`, set a User-Agent, add a small delay, cache (skip if already downloaded). Record `fetched_date`.

### 5b. `parse.py`

- HTML → text via BeautifulSoup (strip nav/script/footer). PDF → text via PyMuPDF; **tables via pdfplumber `extract_tables`**.
- Extract `doc_as_on_date` when present ("Data as on DD Mon YYYY"). Output normalized text + table blocks per source to `data/processed/`.

### 5c. `chunk.py`

- **Token-Aware Sizing:** Use `RecursiveCharacterTextSplitter` aiming for ~400 tokens (~1600 characters) with 15% overlap to safely fit `BAAI/bge-small-en-v1.5`'s 512-token limit.
- **Table Serialization Rule:** Serialize each table row explicitly into a strict `"Label: Value"` text block (e.g., `"Exit Load: 1%"`) so the LLM doesn't lose context between header and data.
- **Identity Injection Rule:** Parse the document for Fund Manager, Category, and Inception Date. Explicitly create an "Identity Block" chunk for that scheme, and prepend `Scheme: <Name>` to table chunks.
- **Strict Metadata Tagging:** Every chunk must be tagged with a dictionary of metadata: `source_url, source_type, scheme_name, plan_type='Direct-Growth', fetched_date, doc_as_on_date`. Write `data/processed/chunks.jsonl`.

### 5d. `build_index.py`

- Embed each chunk with bge-small (remember bge needs the query prefix at search time, not for passages). Upsert vectors + metadata into a **persistent Chroma collection**. Build and pickle a **BM25** index over the same chunk texts (store chunk ids aligned).
- Persist a manifest: embedding model name + dim + `corpus_build_date` (assert model match at query time).

**Agent prompt (run sub-phases one at a time)**
> Implement src/ingest/fetch.py per §5a (cache, robots, UA, delay). Add a **main** that fetches everything in data/sources.csv and reports counts. Then stop — I'll run it before we do parse.py.

*(repeat similarly for parse.py, chunk.py, build_index.py)*

**Acceptance:**

- `python -m src.ingest.fetch` caches all sources, no crashes.
- `chunks.jsonl` exists; spot-check that a fee table chunk has label+value together and carries scheme metadata; identity chunk has "Fund manager: ...".
- `build_index.py` creates a persistent Chroma dir + BM25 pickle + manifest; a quick similarity query for "expense ratio bluechip" returns that scheme's chunk in top-3.

---

## 6. Phase 3 — Guardrails

**Goal:** block PII and route advisory queries **before** retrieval.

### 6a. `pii.py`

- Regex with `\b` anchors: PAN `\b[A-Z]{5}[0-9]{4}[A-Z]\b`, Aadhaar `\b\d{4}\s?\d{4}\s?\d{4}\b`, phone `(\+91[\-\s]?)?[6-9]\d{9}\b`, email. Keyword-gate account/folio/OTP.
- **Do not flag** short numbers/amounts/ratios/years. Return `(blocked: bool, refusal_msg)`; never log the matched value.

### 6b. `intent.py`

- Stage 1: keyword pre-filter for advisory triggers ("should I", "better", "buy/sell", "recommend", "worth it", "which fund").
- Stage 2: LLM classifier (few-shot) → `factual | advisory | out_of_scope`. Cheap model, temperature 0.
- Return label + (for advisory) the educational fallback link (AMFI/SEBI).

**Agent prompt**
> Implement src/guardrails/pii.py and intent.py per §6 and architecture.md §4.1–4.2. Include unit tests: PII must block PAN/Aadhaar/phone/email but must NOT block "minimum SIP 500", "expense ratio 1.5", "launched in 2008". Intent must route "Should I buy ICICI Bluechip?" → advisory and "What is the exit load?" → factual.

**Acceptance:** the listed unit cases pass; no false-positive PII block on numeric facts.

---

## 7. Phase 4 — Retrieval

**Goal:** precise, scheme-correct retrieval with a refusal floor.

**Steps (`scheme_match.py`, `retriever.py`)**

1. **Pre-Retrieval Scheme Detection:** Map query mentions/aliases ("bluechip", "flexicap", "elss"/"tax saver") to `scheme_name`. If no scheme is named, immediately return a `need_clarification` flag so the UI can ask the user which scheme they mean.
2. **Strict Metadata Pre-filtering:** Restrict ChromaDB's search area using the detected `scheme_name` (and `plan_type='Direct-Growth'`). This prevents hallucinating an expense ratio from a different fund.
3. **Hybrid Search (Dense + Sparse):** Execute dense semantic search (`bge-small` via Chroma) for intent matching, and sparse keyword search (BM25) for exact terminology.
4. **Reciprocal Rank Fusion (RRF):** Combine the Top N results from both ChromaDB and BM25 to get perfectly ranked chunks.
5. **Confidence Thresholding:** If the highest fused score < `SCORE_THRESHOLD`, return `no_hit` -> "not in official sources" refusal to avoid hallucination.

**Agent prompt**
> Implement src/retrieve/scheme_match.py and retriever.py per §7 and architecture.md §4.3: hybrid dense+BM25 with RRF, scheme/plan metadata filter, similarity threshold, and a need_clarification path when no scheme is named. Add a **main** that runs 5 sample queries and prints retrieved chunk ids + scores + source_url.

**Acceptance:** "expense ratio of flexicap" returns only Flexicap chunks; "minimum SIP?" (no scheme) → need_clarification; a nonsense query → no_hit.

---

## 8. Phase 5 — Generation (answer contract)

**Goal:** compose the final answer that obeys every output rule.

**Steps (`prompt.py`, `answer.py`, `llm/client.py`)**

1. `client.py`: `complete(system, user, temperature=0)`; Use the **Groq** API client; read `GROQ_API_KEY` and model from config.
2. `prompt.py`: the strict system prompt from architecture.md §6.1 — answer only from supplied chunks, ≤3 sentences, **quote numbers verbatim**, exactly one citation, footer `Last updated from sources: <doc_as_on_date|fetched_date>`; refuse if chunks lack the fact.
3. `answer.py` orchestration:

   ```
   query → pii.check → (block?) refuse
         → intent.classify → (advisory?) advisory_refusal+edu_link
                            → (out_of_scope?) refuse
         → retrieve → (need_clarification?) ask which scheme
                    → (no_hit?) not_in_sources refusal
         → generate(chunks) → answer + 1 citation + footer
   ```

4. Pick the single citation = source_url of the top contributing chunk (prefer SID/KIM/factsheet over FAQ on ties).

**Agent prompt**
> Implement src/llm/client.py (provider-agnostic, temperature 0), src/generate/prompt.py (system prompt per architecture.md §6.1), and src/generate/answer.py orchestrating the full pipeline in §8. Return a structured result {answer_text, citation_url, last_updated, kind: factual|refusal}. Add a **main** running the example questions end to end.

**Acceptance:** factual queries return ≤3 sentences + one URL + footer; advisory → polite refusal + edu link; verbatim numbers (no rounding); missing fact → refusal not hallucination.

---

## 9. Phase 6 — UI (Streamlit)

**Goal:** the minimal interface required by the brief.

**Steps (`app/streamlit_app.py`)**

- Welcome line; **three example questions** as clickable buttons (one expense-ratio, one ELSS lock-in, one fund-manager); chat input; render answer with the citation link and footer.
- Persistent visible disclaimer: **"Facts-only. No investment advice."**
- Calls `answer.answer(query)`; shows refusals plainly. No PII fields, no login.

**Agent prompt**
> Build app/streamlit_app.py per §9 and context.md §4.4: welcome line, three example-question buttons wired to the pipeline, a chat box calling src.generate.answer.answer, answer rendering with clickable citation + "Last updated from sources" footer, and a permanent "Facts-only. No investment advice." disclaimer. No PII inputs.

**Acceptance:** `streamlit run app/streamlit_app.py` works; the 3 example buttons return cited answers; disclaimer always visible; an advisory question is refused in-UI.

---

## 10. Phase 7 — Evaluation

**Goal:** prove correctness and produce the Sample Q&A deliverable.

**Steps (`eval/testset.json`, `eval/run_eval.py`)**

1. Build the test set: ~10 factual cases (query → expected fact substring + expected source_url) across all fact types incl. fund manager & inception; ~5 refusal cases (advisory + PII).
2. `run_eval.py` runs each through `answer.answer` and checks: factual → expected fact present, exactly one URL, URL is official, footer present, ≤3 sentences; refusal → no fact leaked, edu link present for advisory.
3. **Calibrate `SCORE_THRESHOLD`** against results (raise until nonsense queries refuse, lower until valid facts pass).
4. Export passing factual cases to `deliverables/sample_qa.md`.

**Agent prompt**
> Create eval/testset.json (10 factual + 5 refusal per §10) and eval/run_eval.py that runs the pipeline and asserts the listed checks, printing a pass/fail table. Then generate deliverables/sample_qa.md from the passing factual cases (query, answer, citation, last-updated).

**Acceptance:** all refusal cases pass (zero advice leakage); ≥8/10 factual cases pass with correct citations; threshold calibrated.

---

## 11. Phase 8 — Deliverables & Packaging

**Goal:** everything the brief asks to submit.

**Steps**

1. **README.md** — setup steps, scope (AMC + 3 schemes + Direct–Growth), architecture overview (link `architecture.md`), how to run ingestion + app, known limits (from architecture §9).
2. **sources.csv** — final 15–25 URLs (already built).
3. **sample_qa.md** — from Phase 7.
4. **disclaimer.md** — "Facts-only. No investment advice." snippet used in UI.
5. **Demo:** host (Streamlit Community Cloud) for a link, or record a ≤3-min screen demo if hosting isn't possible.
6. Tag a release / zip the repo.

**Agent prompt**
> Write README.md per §11 (setup, scope, architecture overview, run commands, known limits) and deliverables/disclaimer.md. Verify all five deliverables exist and the app runs from a clean clone following only the README.

**Acceptance:** a fresh clone + README steps reproduces a working app; all five deliverables present.

---

## 12. End-to-End Build Checklist

- [ ] Phase 0 — skeleton, deps, config, rules file
- [ ] Phase 1 — `sources.csv` (15–25 official URLs, verified)
- [ ] Phase 2 — fetch → parse → chunk → index (Chroma + BM25 + manifest)
- [ ] Phase 3 — PII + intent guardrails (unit-tested)
- [ ] Phase 4 — hybrid retrieval + scheme/plan filter + threshold
- [x] Phase 5 — generation contract (≤3 sentences, 1 citation, footer, verbatim numbers)
- [x] Phase 6 — Streamlit UI (welcome, 3 examples, disclaimer)
- [x] Phase 7 — eval set passing; sample_qa.md generated; threshold calibrated
- [ ] Phase 8 — README + deliverables + demo link/video

---

## 13. Risks & Watch-outs (carry from architecture.md §11)

- Chunk size must stay ≤ embedding limit (bge-small = 512) — don't raise blindly.
- Fee/exit-load values are in tables; verify they survive chunking with their labels.
- Footer date = document "as on" date, not download date, when available.
- PII regex must not block legitimate amounts/ratios/years.
- Dense-only retrieval mixes similar schemes — keep hybrid + metadata filter.
- Only Direct–Growth is indexed; redirect Regular/IDCW queries to the official page.
- Never hardcode a fund figure as truth in code or tests — figures come from the live corpus.
- Verify generated URLs are real and official before trusting them (LLMs invent links).

```
