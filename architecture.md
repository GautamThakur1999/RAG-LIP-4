# Architecture — Mutual Fund FAQ Assistant (Facts-Only RAG)

> Technical design for the facts-only mutual fund FAQ assistant described in [`context.md`](./context.md). Product context: **Groww**. Sources: AMC / AMFI / SEBI public pages only.
>
> **Locked scope:** AMC = **ICICI Prudential Mutual Fund** (`icicipruamc.com`). Schemes = **Bluechip Fund** (large-cap), **Flexicap Fund**, **ELSS Tax Saver Fund** (3-yr lock-in). Plan type to index: **Direct – Growth**.
>
> Items marked **`<TBD>`** are pending your confirmation (exact stack).

---

## 1. Design Goals & Principles

The architecture is shaped directly by the constraints in the problem statement:

- **Accuracy over intelligence** — the model never answers from parametric knowledge; it answers only from retrieved official text, or it refuses.
- **One citation per answer** — every factual response carries exactly one source URL, traceable to the chunk that produced it.
- **Facts-only, no advice** — advisory/opinionated/performance-comparison queries are refused before or after retrieval.
- **No PII** — PAN, Aadhaar, account numbers, OTPs, email, phone are detected and blocked, never stored.
- **Transparency** — answers ≤ 3 sentences, with a `Last updated from sources: <date>` footer.
- **Small, controlled corpus** — 15–25 vetted official URLs, no third-party content.

---

## 2. High-Level Architecture

```
                        ┌──────────────────────────────────────────┐
                        │                  USER                     │
                        └───────────────────┬──────────────────────┘
                                            │ query
                                            ▼
                        ┌──────────────────────────────────────────┐
                        │              UI LAYER                     │
                        │  welcome line · 3 examples · disclaimer   │
                        └───────────────────┬──────────────────────┘
                                            ▼
                  ┌────────────────────────────────────────────────┐
                  │            GUARDRAIL / ROUTER LAYER             │
                  │  1. PII detector  (block + scrub)               │
                  │  2. Intent classifier (factual vs advisory)     │
                  │       └─ advisory → REFUSAL response            │
                  └───────────────────┬────────────────────────────┘
                                      │ factual query
                                      ▼
                  ┌────────────────────────────────────────────────┐
                  │              RETRIEVAL LAYER                    │
                  │  embed query → vector search (top-k)            │
                  │  apply similarity threshold                     │
                  │       └─ no hit → "not in sources" refusal      │
                  └───────────────────┬────────────────────────────┘
                                      │ relevant chunks + metadata
                                      ▼
                  ┌────────────────────────────────────────────────┐
                  │             GENERATION LAYER                   │
                  │  LLM + strict system prompt                     │
                  │  → ≤3 sentence answer                           │
                  │  → 1 citation (chunk source URL)                │
                  │  → footer: Last updated from sources: <date>    │
                  └───────────────────┬────────────────────────────┘
                                      ▼
                                  ANSWER

        ── OFFLINE / BUILD-TIME PIPELINE (runs before serving) ──
        official URLs → fetch → clean → chunk → embed → vector store
```

The system has two phases: an **offline ingestion pipeline** that builds the index once (re-run when sources change), and an **online query pipeline** that serves each user question.

---

## 3. Offline Ingestion Pipeline (Corpus → Index)

Run once to build the searchable index; re-run when source pages are updated.

### 3.1 Source Collection
- Curated list of **15–25 official URLs** (AMC factsheets, KIM, SID, FAQ/help, fee pages, riskometer/benchmark notes, AMFI/SEBI guidance, statement/tax guides).
- **Include each scheme's official overview/snapshot page** (e.g. `icicipruamc.com/mutual-fund/equity-funds/icici-prudential-bluechip-fund`). This is where **fund management / identity facts** live — fund manager name(s), "managing since" date, fund house/AMC, scheme category, inception/launch date. These are prose fields, not tables, so they need different handling from the tabular fee data (see §3.4).
- Maintained in `sources.csv` with columns: `url`, `source_type`, `scheme`, `title`, `fetched_date`. This file is also a required deliverable.

> **Answerable fact types (scope of the corpus):** expense ratio · exit load · minimum SIP · ELSS lock-in · riskometer · benchmark index · **fund management details (manager, managing-since, fund house, category, inception date — identity data only, no performance)** · how to download statements / capital-gains reports. Every other intent (advice, opinion, returns/comparison) is refused.

### 3.2 Fetch & Extract
- Download each page/PDF.
- HTML → text via a parser (e.g., BeautifulSoup / readability); PDF (KIM/SID/factsheets) → text via a PDF extractor (e.g., pdfplumber / PyMuPDF).
- Strip nav, ads, scripts, boilerplate. Keep tables where fee/expense data lives.

### 3.3 Normalize & Clean
- Collapse whitespace, fix encoding, preserve numbers/units (%, ₹, days).
- Capture per-document metadata: `source_url`, `source_type`, `scheme_name`, `plan_type` (Direct/Regular, Growth/IDCW), `fetched_date`.

### 3.4 Chunking
- Split into retrieval units with metadata carried on every chunk.
- **Chunk size must fit the embedding model's context window.** Many small `sentence-transformers` models truncate input (e.g. `all-MiniLM-L6-v2` = **256 tokens**, `bge-small-en-v1.5` = **512 tokens**). A 500–800-token chunk silently truncates and loses the tail of the text — a real bug. **Set chunk size to the model limit:** ~200 tokens (MiniLM) or ~400 tokens (bge-small / e5), with ~15% overlap. If you want larger chunks, pick a long-context embedding model.
- **Table-aware extraction is critical for this domain.** Expense ratio, exit load, minimum SIP, and riskometer values live in *tables* inside factsheets/KIM/SID. Naive text splitting separates a number from its label/row header. Extract tables separately (e.g. pdfplumber `extract_tables`), serialize each row as `"<column header>: <value>"` or a small markdown table, and keep each label+value pair intact within one chunk. Prepend the scheme name to every table chunk so the value is never orphaned.
- **Fund management / identity facts are prose, not tables.** Fund manager, "managing since", category, and inception date usually appear as label–value text on the scheme overview page or in the SID. Capture them as `"Fund manager: <name>"`-style key–value lines, prepend the scheme name, and keep each scheme's identity block in its own chunk so a query about Scheme A's manager can't surface Scheme B's.
- Prefer semantic/section-aware splitting (by heading) so a chunk doesn't straddle two unrelated facts.
- Each chunk stores: `chunk_text`, `source_url`, `source_type`, `scheme_name`, `plan_type`, `fetched_date`, `doc_as_on_date`. **`source_url` is the citation returned to the user.**

### 3.5 Embedding & Indexing
- Embed each chunk with the chosen embedding model.
- Store vectors + metadata in the vector store.
- Persist the index to disk so serving doesn't re-embed.

---

## 4. Online Query Pipeline (Question → Answer)

### 4.1 PII Guardrail (pre-retrieval, hard block)
- Pattern checks for: PAN (`\b[A-Z]{5}[0-9]{4}[A-Z]\b`), Aadhaar (`\b\d{4}\s?\d{4}\s?\d{4}\b`), phone (`(\+91[\-\s]?)?[6-9]\d{9}`), email (`\b[\w.+-]+@[\w-]+\.[\w.-]+\b`), OTP/account references by keyword ("my OTP", "account no", "folio").
- **Avoid over-blocking real facts.** Mutual-fund queries are full of numbers — amounts (`₹500`, `1000`), expense ratios (`1.25`), years (`2025`), lock-in days (`90`). Do **not** flag short/standalone numbers as PII. Anchor patterns with `\b`, require the exact digit counts above (10/12-digit), and gate ambiguous numeric strings behind keywords ("account", "folio", "card") so "minimum SIP 500" or "expense ratio 1.5" is never mistaken for an account number/OTP.
- If detected: do **not** store or echo the value; return the PII-refusal message (§6.6). If you log queries for eval, scrub matched spans first.

### 4.2 Intent Classification (factual vs advisory)
- Decide whether the query asks for a **fact** (answerable) or **advice/opinion/comparison** (refuse).
- **Two-stage, recommended:** (1) a fast keyword pre-filter for obvious advisory triggers ("should I", "is it good", "better", "buy/sell", "recommend", "worth it", "which fund", return/performance comparisons); (2) for anything not caught, an LLM classifier with a few-shot prompt returning `factual` / `advisory` / `out_of_scope`. Keyword-only is too brittle — "Is the expense ratio good?" mixes a fact with an opinion and must route to advisory.
- Advisory → **refusal response** (§6.2) with educational link. No retrieval performed.

### 4.3 Retrieval
- **Hybrid retrieval is recommended.** Pure dense (semantic) search is weak at exact factual lookup and at distinguishing similarly-named schemes. Combine dense vector search with a keyword/BM25 pass and merge (e.g. Reciprocal Rank Fusion). This sharply improves precision for "expense ratio of <scheme>"-type queries where the right answer is one specific row.
- **Scheme disambiguation:** detect the scheme name in the query and apply it as a **metadata filter** before/with retrieval, so a "minimum SIP?" query for Scheme A never returns Scheme B's chunk. If no scheme is named and the corpus has multiple schemes, ask the user which scheme they mean (don't guess). Likewise filter by `plan_type` (Direct/Regular) when specified, since expense ratios differ. **Note:** the corpus indexes **Direct – Growth** only; if a user explicitly asks about the Regular plan or IDCW option, state that the assistant covers the Direct–Growth plan and point them to the official scheme page rather than returning a Direct-plan figure as if it were Regular.
- Embed the query; retrieve **top-k** (recommended `k = 3–5`) after fusion + filtering.
- Apply a **similarity/score threshold** — if the best chunk is below it, treat as *not in corpus* and return the "not in official sources" refusal (§6.3) rather than guessing. **Calibrate the threshold** against your eval set; don't hardcode blindly.

### 4.4 Generation
- Pass retrieved chunks + the strict system prompt to the LLM. Use **temperature 0** for determinism.
- Output contract:
  - Answer **≤ 3 sentences**, factual, drawn only from supplied chunks.
  - **Quote numbers/values verbatim** from the chunk — never rephrase, round, recompute, or infer a figure. This is the main hallucination risk in a facts assistant.
  - Exactly **one citation.** If the answer spans multiple chunks, cite the single most authoritative/primary source (prefer the SID/KIM/factsheet over a generic FAQ). Best practice: scope each fact to one chunk so a single citation is natural.
  - Footer: `Last updated from sources: <doc_as_on_date or fetched_date>` (see §6.5).
- If chunks don't actually contain the asked fact → refuse ("not available in official sources"), don't fabricate.

---

## 5. Component Choices (recommended defaults — confirm or override)

| Layer | Recommended default | Notes |
|-------|--------------------|-------|
| Language | Python | `<TBD — confirm>` |
| HTML parse | BeautifulSoup / readability-lxml | |
| PDF parse | pdfplumber or PyMuPDF | for KIM/SID/factsheet PDFs |
| Chunking | LangChain `RecursiveCharacterTextSplitter` or custom | ~500–800 tok, 10–15% overlap |
| Embeddings | `sentence-transformers` (e.g. all-MiniLM / bge-small) local, **or** a hosted embedding API | local = free/offline; hosted = higher quality |
| Vector store | FAISS (local, simple) or Chroma (metadata-friendly) | Chroma eases metadata filtering |
| LLM | `<TBD>` — any chat model with a strict system prompt | low temperature (0–0.2) for determinism |
| Orchestration | LangChain / LlamaIndex, or thin custom code | small corpus → custom is fine |
| UI | Streamlit or Gradio (notebook fallback ok) | needs welcome line, 3 examples, disclaimer |

> **Pending your spec:** AMC name, the 3–5 schemes, plan type to index, embedding model, LLM, and UI framework. The architecture holds regardless of these picks.

---

## 6. Behavior Specifications

### 6.1 System Prompt (intent)
> You are a facts-only mutual fund FAQ assistant. Answer only using the provided official source excerpts. Keep answers to at most 3 sentences. Include exactly one citation: the source URL of the excerpt used. Never give investment advice, opinions, recommendations, or performance comparisons. If the excerpts do not contain the answer, say it is not available in the official sources. End every factual answer with: `Last updated from sources: <date>`.

### 6.2 Refusal — advisory query
> I can only share factual information from official sources and can't give investment advice or recommendations. For guidance on choosing funds, see this educational resource: `<AMFI/SEBI educational link>`.

### 6.3 Refusal — not in corpus
> I couldn't find that in my official source set. You may want to check the scheme's official factsheet/SID directly.

### 6.4 Performance/return query
> Redirect to the official factsheet link rather than computing or comparing returns.

### 6.5 Answer footer
- Format: `Last updated from sources: <date>`.
- **Prefer the document's own "as on" date over the fetch date.** Factsheets state "Data as on 31 May 2025" inside the document; that is the true currency of the fact. Citing only the fetch date (when *you* downloaded it) misrepresents how fresh the number is. Extract `doc_as_on_date` during ingestion and use it for the footer; fall back to `fetched_date` only when the document has no stated as-of date.

### 6.6 Refusal — PII detected
> For your security, please don't share personal or financial identifiers (PAN, Aadhaar, account/folio numbers, OTPs, email, or phone). I can answer general factual questions about mutual fund schemes from official sources.

---

## 7. Data Model

**Source record (`sources.csv`):**
`url, source_type, scheme, title, fetched_date`

**Chunk record (vector store):**
`id, chunk_text, embedding, source_url, source_type, scheme_name, plan_type, fetched_date, doc_as_on_date`

**Citation returned to user:** `source_url` of the top contributing chunk.

---

## 8. Evaluation & Acceptance

- **Factual test set (~10):** query → expected fact + expected source URL. Checks retrieval accuracy and correct citation. Doubles as the *Sample Q&A* deliverable. Cover all fact types, including fund management (e.g. "Who manages ICICI Prudential Bluechip Fund?", "When was ICICI Prudential ELSS Tax Saver Fund launched?").
- **Refusal test set (~5):** advisory/PII queries → must refuse, no fact leaked.
- **Citation check:** every factual answer contains exactly one URL, and it's from the official corpus.
- **Length check:** answers ≤ 3 sentences; footer present.
- **PII check:** identifiers are blocked and never appear in logs/output.

---

## 9. Known Limitations

- Answers are only as current as the last corpus fetch; expense ratios/AUM change over time.
- Direct vs Regular plans have different expense ratios — only the indexed plan type is answered.
- Small corpus means out-of-scope questions are common and (correctly) refused.
- No live data; performance/return questions are redirected, not computed.

---

## 10. Build Order (suggested)

1. Lock scope: AMC + 3–5 schemes + plan type → finalize `sources.csv` (15–25 URLs).
2. Build ingestion: fetch → clean → chunk → embed → persist index.
3. Implement guardrails: PII detector + intent classifier.
4. Implement retrieval (top-k + threshold) and generation (system prompt + output contract).
5. Build minimal UI (welcome, 3 examples, disclaimer).
6. Write eval sets; run factual + refusal tests.
7. Package deliverables: prototype/demo, `sources.csv`, README, sample Q&A, disclaimer snippet.

---

## 11. Implementation Review — Issues, Edge Cases & Fixes

Issues found while reviewing this design for a real, codeable build. Each has been folded into the sections above; this is the consolidated checklist.

### 11.1 Bugs / correctness
| # | Issue | Impact | Fix |
|---|-------|--------|-----|
| 1 | **Chunk size (500–800 tok) exceeds small embedding models' input limit** (MiniLM = 256, bge-small = 512). | Chunks silently truncated; tail facts never embedded → missed retrievals. | Match chunk size to the model limit (§3.4), or use a long-context embedder. |
| 2 | **Facts live in tables**; naive text splitting orphans numbers from labels. | "Expense ratio" / "exit load" / "min SIP" return wrong or no value. | Table-aware extraction; keep label+value together; prepend scheme name (§3.4). |
| 3 | **Footer used fetch date**, not the document's "as on" date. | Misrepresents data freshness — bad for a facts/compliance tool. | Extract & cite `doc_as_on_date` (§6.5). |
| 4 | **PII regex could over-block legitimate numeric facts** (amounts, ratios, years). | Valid questions wrongly refused. | Anchor patterns, exact digit counts, keyword-gate ambiguous numbers (§4.1). |
| 5 | **Dense-only retrieval** is weak at exact lookups and similar scheme names. | Returns the wrong scheme's figure. | Hybrid (dense + BM25) + scheme/plan metadata filter (§4.3). |

### 11.2 Edge cases to handle in code
- **No scheme named, multiple schemes in corpus** → ask which scheme; don't guess (§4.3).
- **Direct vs Regular plan** → different expense ratios; filter by `plan_type` and state which plan the answer refers to.
- **Fact genuinely absent from corpus** → "not in official sources" refusal, never fabricate.
- **Mixed fact+opinion** ("Is the expense ratio good?") → route to advisory refusal, optionally state the factual number first only if cleanly separable (safer to refuse the opinion part).
- **Multi-tier exit load** (e.g. 1% if redeemed < 365 days, else nil) → ensure the full tier table is in one chunk so the answer isn't partial.
- **Number formatting** → preserve units/symbols (`%`, `₹`, "days"); quote verbatim, never recompute.
- **Stale numbers** → expense ratio/AUM change; the as-on date in the footer signals this.

### 11.3 Scoping caveat (worth confirming early)
- **"Groww" the platform vs an AMC.** The brief says *use Groww as product context* but also *pick one AMC* and *no aggregator/third-party sources*. Groww-the-app aggregates many AMCs, so Groww scheme pages may count as a third-party aggregator, not an official AMC source. Two clean options: (a) pick **Groww Mutual Fund** (Groww's own AMC) and use its official AMC site + KIM/SID/factsheets — keeps "Groww" as both product and AMC; or (b) pick any AMC's official site for sources and treat Groww only as the framing/product context. **Confirm which before collecting URLs**, since it determines what's a valid source.

### 11.4 Operational notes
- **Robots/politeness** when fetching: respect `robots.txt`, add a delay/User-Agent; cache raw downloads so re-runs don't re-hit servers.
- **Large SID/KIM PDFs** (50–100+ pages) create many noisy chunks — consider section pre-filtering (fees, exit load, riskometer, minimum application) before indexing.
- **Reproducibility**: pin package versions; persist the index + a `corpus_build_date`; record embedding model + dimension so the store isn't queried with a mismatched model.
- **Index/model coupling**: if you change the embedding model, you must re-embed the whole corpus — store the model name alongside the index and assert it at query time.
- **Determinism**: temperature 0 for the generation LLM; fixed seed where supported.

### 11.5 Recommended dependency set (Python, for when you confirm the stack)
`requests`, `beautifulsoup4`, `pdfplumber` (tables) / `PyMuPDF`, `sentence-transformers` (or a hosted embedding API), `faiss-cpu` or `chromadb`, `rank-bm25` (hybrid), an LLM SDK, `streamlit` (UI), `pytest` (eval harness). Confirm before I scaffold.
