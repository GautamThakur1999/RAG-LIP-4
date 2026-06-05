# Mutual Fund FAQ Assistant — Facts-Only Q&A

> **Project context document.** Stores the full problem statement for the RAG-based mutual fund FAQ assistant.

## Product Selection

**Chosen product:** Groww (from the list: INDMoney, Groww, PowerUp Money, Wealth Monitor, Kuvera).

> **Note:** The next LIP challenge will use this same product.

### Selected Scope (locked)

| Item | Value |
|------|-------|
| **AMC** | ICICI Prudential Mutual Fund — [`icicipruamc.com`](https://www.icicipruamc.com) (largest Indian AMC; per-scheme pages + Downloads hub for SID/KIM/factsheet; NAV/expense data updated daily) |
| **Scheme — large-cap** | [ICICI Prudential Bluechip Fund](https://www.icicipruamc.com/mutual-fund/equity-funds/icici-prudential-bluechip-fund) |
| **Scheme — flexi-cap** | ICICI Prudential Flexicap Fund |
| **Scheme — ELSS** | ICICI Prudential ELSS Tax Saver Fund (3-year lock-in) · slug `icici-prudential-long-term-equity-fund-tax-saving` |
| **Plan type to index** | **Direct – Growth** (lower expense ratio, no distributor commission, profits stay invested; one unambiguous figure set per scheme) |
| **Sourcing rule** | Corpus URLs from official AMC site + AMFI/SEBI only — not Groww/aggregator pages |

---

## 1. Overview

The objective of this project is to build a facts-only FAQ assistant for mutual fund schemes, using Groww as the reference product context and **ICICI Prudential Mutual Fund** as the chosen AMC for the corpus. The assistant answers objective, verifiable queries related to mutual funds by retrieving information exclusively from official public sources such as AMC (Asset Management Company) websites, AMFI, and SEBI.

The system must strictly avoid providing investment advice, opinions, or recommendations. Every response must include a single, clear source link and adhere to defined constraints around clarity, accuracy, and compliance.

The milestone is to build a small FAQ assistant that answers facts about mutual fund schemes — e.g., expense ratio, exit load, minimum SIP, lock-in (ELSS), riskometer, benchmark, fund management details (fund manager, fund house, category, inception date), and how to download statements — using only official public pages. Every answer must include one source link. No advice.

---

## 2. Objective

Design and implement a lightweight Retrieval-Augmented Generation (RAG)-based assistant that:

- Answers factual queries about mutual fund schemes
- Uses a curated corpus of official documents
- Provides concise, source-backed responses

---

## 3. Target Users

- Retail investors comparing mutual fund schemes
- Customer support and content teams handling repetitive mutual fund queries

---

## 4. Scope of Work

### 4.1 Corpus Definition

> **SELECTED SCOPE (locked):**
> **AMC:** ICICI Prudential Mutual Fund — official site `https://www.icicipruamc.com` (largest Indian AMC; per-scheme pages + Downloads hub for SID/KIM/factsheet; NAV/expense data updated daily).
> **Schemes (3):**
> - Large-cap — **ICICI Prudential Bluechip Fund** · `https://www.icicipruamc.com/mutual-fund/equity-funds/icici-prudential-bluechip-fund`
> - Flexi-cap — **ICICI Prudential Flexicap Fund**
> - ELSS — **ICICI Prudential ELSS Tax Saver Fund** (3-year lock-in) · slug `icici-prudential-long-term-equity-fund-tax-saving`
>
> **Plan type to index:** `<TBD — Direct or Regular>` (expense ratios differ; pick one for consistency).
> Corpus URLs come from the **official AMC site + AMFI/SEBI only** — not Groww/aggregator pages.

- Select one Asset Management Company (AMC).
- Pick 3–5 schemes under it (e.g., one large-cap, one flexi-cap, one ELSS).
- Collect 15–25 official public URLs, including:
  - Scheme factsheets
  - KIM (Key Information Memorandum)
  - SID (Scheme Information Document)
  - AMC FAQ / help pages
  - Fee / charges pages
  - Riskometer / benchmark notes
  - AMFI / SEBI guidance pages
  - Statement and tax-document download guides

### 4.2 FAQ Assistant Requirements (Working Prototype)

The assistant must answer facts-only queries, such as:

- Expense ratio of a scheme
- Exit load details
- Minimum SIP amount
- ELSS lock-in period
- Riskometer classification
- Benchmark index
- Fund management details — fund manager name(s), "managing since" date, fund house / AMC, scheme category, inception / launch date (factual identity data only; **no performance**)
- Process to download statements or capital-gains reports

The assistant must ensure that:

- Each response is limited to a maximum of 3 sentences
- Each response includes exactly one citation link
- Each response includes a footer: `Last updated from sources: <date>`

### 4.3 Refusal Handling

The assistant must refuse non-factual or advisory queries, such as:

- "Should I invest in this fund?"
- "Which fund is better?"
- "Should I buy / sell?"

Refusal responses should:

- Be polite and clearly worded
- Reinforce the facts-only limitation
- Provide a relevant educational link (e.g., AMFI or SEBI resource)

### 4.4 User Interface (Minimal)

The solution should include a simple interface with:

- A welcome message / welcome line
- Three example questions
- A visible disclaimer: **"Facts-only. No investment advice."**

---

## 5. Constraints

### 5.1 Data and Sources

- Use only official public sources (AMC, AMFI, SEBI).
- No screenshots of the app back-end.
- Do not use third-party blogs or aggregator websites as sources.

### 5.2 Privacy and Security (No PII)

Do not accept, collect, store, or process:

- PAN or Aadhaar numbers
- Account numbers
- OTPs
- Email addresses or phone numbers

### 5.3 Content Restrictions

- No investment advice or recommendations.
- No performance claims.
- No performance comparisons or return calculations.
- For performance-related queries, provide a link to the official factsheet only.

### 5.4 Transparency and Clarity

- Responses must be short, factual, and verifiable.
- Keep answers ≤ 3 sentences.
- Every answer must include a source link and a last-updated date (`Last updated from sources: <date>`).

---

## 6. Expected Deliverables

1. Working prototype link (app / notebook), or a ≤ 3-minute demo video if hosting isn't possible.
2. Source list (CSV / MD) of the 15–25 URLs used.
3. README Document, including:
   - Setup instructions / steps
   - Scope: selected AMC and schemes
   - Architecture overview (RAG approach)
   - Known limitations
4. Sample Q&A file (5–10 queries with the assistant's answers + links).
5. Disclaimer snippet used in the UI: **"Facts-only. No investment advice."**

---

## 7. Skills Being Tested

- **W1 — Thinking Like a Model:** identify the exact fact asked; decide answer vs. refuse.
- **W2 — LLMs & Prompting:** instruction style, concise phrasing, polite safe-refusals, citation wording.
- **W3 — RAGs (only):** small-corpus retrieval with accurate citations from AMC / SEBI / AMFI pages.

---

## 8. Success Criteria

- Accurate retrieval of factual mutual fund information.
- Strict adherence to facts-only responses.
- Consistent inclusion of valid source citations.
- Proper refusal of advisory queries.
- Clean, minimal, and user-friendly interface.

---

## 9. Summary

The goal is to build a trustworthy, transparent, and compliant mutual fund FAQ assistant that prioritizes accuracy over intelligence. The system should ensure that users receive only verified, source-backed financial information, without any advisory bias or speculative content. Built on a small-corpus RAG approach over official AMC / AMFI / SEBI pages, every answer is concise (≤ 3 sentences), carries exactly one citation link, and shows the date it was last updated from sources — while politely refusing any advisory, opinionated, or performance-comparison request.

---

## 10. Reference — AMC Shortlist (Groww directory)

Candidate AMCs, browsed via the Groww directory. **One** AMC will be selected for the corpus.

- Directory of all AMCs: https://groww.in/mutual-funds/amc
- Groww Mutual Funds: https://groww.in/mutual-funds/amc/groww-mutual-funds
- HDFC Mutual Funds: https://groww.in/mutual-funds/amc/hdfc-mutual-funds
- ICICI Prudential Mutual Funds: https://groww.in/mutual-funds/amc/icici-prudential-mutual-funds
- SBI Mutual Funds: https://groww.in/mutual-funds/amc/sbi-mutual-funds
- Axis Mutual Funds: https://groww.in/mutual-funds/amc/axis-mutual-funds
- Kotak Mahindra Mutual Funds: https://groww.in/mutual-funds/amc/kotak-mahindra-mutual-funds
- Nippon India Mutual Funds: https://groww.in/mutual-funds/amc/nippon-india-mutual-funds
- Aditya Birla Sun Life Mutual Funds: https://groww.in/mutual-funds/amc/aditya-birla-sun-life-mutual-funds
- UTI Mutual Funds: https://groww.in/mutual-funds/amc/uti-mutual-funds
- Mirae Asset Mutual Funds: https://groww.in/mutual-funds/amc/mirae-asset-mutual-funds
- Tata Mutual Funds: https://groww.in/mutual-funds/amc/tata-mutual-funds
- DSP Mutual Funds: https://groww.in/mutual-funds/amc/dsp-mutual-funds
- Edelweiss Mutual Funds: https://groww.in/mutual-funds/amc/edelweiss-mutual-funds
- Quant Mutual Funds: https://groww.in/mutual-funds/amc/quant-mutual-funds

> **Sourcing caveat (important):** These `groww.in` pages are an **aggregator/directory** — use them only to navigate and shortlist the AMC. The corpus constraint requires **official sources only** (the AMC's own website, plus AMFI/SEBI), with no third-party aggregator pages as citations. Once the AMC is chosen, collect the 15–25 corpus URLs (factsheet, KIM, SID, FAQ, fee/charges, riskometer/benchmark, statement/tax guides) from that AMC's **official site** and from AMFI/SEBI — not from Groww.
>
> Exception: if **Groww Mutual Funds** is the chosen AMC, its official AMC site (`growwmf.in` / the official Groww AMC pages) — not the Groww app's aggregator listings — is the valid source.
