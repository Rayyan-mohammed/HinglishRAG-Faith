---
marp: true
theme: default
paginate: true
size: 16:9
---

# CodeSwitch-Verify

**Faithfulness-Checked RAG for Hinglish Government-Scheme Q&A**

Claim-level hallucination detection for a Hindi-English mixed chatbot

Team of 2 — A: Rishikesh (retrieval, generation, demo, report) · B: Rayyan (evaluation, labelling, verifier pipeline, error analysis, report)

---

## The problem

RAG chatbots answering Hinglish questions about government schemes generate fluent answers —
but nothing checks whether every claim in the answer is actually supported by the retrieved
source document.

> "Aapka application 15 din mein process ho jayega, but aapko Aadhaar copy submit karni hogi."

A wrong eligibility condition, a wrong deadline, a wrong amount can pass through **undetected** —
in a domain where being wrong has real consequences.

---

## The approach

Add a claim-level verification layer *after* generation:

1. Break the generated answer into **atomic claims**
2. Check **each claim** against retrieved evidence — not the whole answer at once
3. Tag every claim **supported / contradicted / unverifiable**
4. Show the user, don't trust blindly

Standard technique in RAG evaluation research (FActScore, RAGTruth, ARES) — the project's focus
is applying and *measuring* it specifically on Hinglish output, not inventing a new algorithm.

---

## System architecture — 6 stages

1. **Retrieval** — embed the question, find closest passages (bge-m3 + FAISS)
2. **Generation** — answer in Hinglish, grounded only in retrieved passages (Groq)
3. **Claim decomposition** — split the answer into atomic, checkable claims
4. **Per-claim retrieval** — re-query the index with *each individual claim*
5. **Verification** — LLM-as-judge: supported / contradicted / unverifiable + confidence
6. **Aggregation** — combine verdicts back into the answer, shown next to the plain answer

Every component is pretrained and reused as-is — no model trained or fine-tuned.

---

## Knowledge base

**172 atomic facts**, scraped live from official `.gov.in` sources — not hand-written

| Scheme | Facts | Sources |
|---|---|---|
| PM-KISAN | 43 | Operational Guidelines + Revised FAQ + Additional FAQ (PDFs) |
| Ayushman Bharat | 37 | Official FAQ + Benefits page |
| PM Awas Yojana | 58 | FAQ + PMAY-U 2.0 Operational Guidelines (PDF) |
| Post-Matric Scholarship | 34 | National guidelines PDF + Maharashtra state page |

Re-fetchable and reproducible: `scripts/fetch_scheme_data.py` re-derives every file from its live
source on demand.

---

## Tech stack

| Component | Choice |
|---|---|
| Generator + verifier | Groq API — `openai/gpt-oss-120b` (free tier) |
| Embeddings | `BAAI/bge-m3`, local, multilingual |
| Vector store | FAISS, in-memory, local |
| Claim decomposition | Rule-based Python (sentence + connector-word rules) |
| Demo | Streamlit |
| Dependencies | `uv` + `pyproject.toml`, 14 `pytest` tests |

Runs entirely on free tools — no GPU, no paid API, no institutional compute.

---

## Evaluation methodology

- **60 hand-written Hinglish questions**, 15 per scheme, 4 categories each (eligibility, deadline,
  amount, documents)
- **Two-level ground truth**: answer-level (fully correct / partially / fully hallucinated) and
  claim-level (212 decomposed claims, 24 ground-truth hallucinated)
- **Protocol**: build index → generate plain-RAG answers → label ground truth → run full verified
  pipeline → compute precision/recall → review a sample of mistakes

Ground truth is an **AI-drafted first pass, disclosed as pending human review** — treated as
provisional throughout.

---

## Results

![w:900](figures/results_chart.png)

---

## Reading the results honestly

- **Recall is strong**: catches 3 of every 4 genuine hallucinated claims
- **Precision is weak**: only 1 in 5 flagged claims is an actual hallucination
- **The baseline has a 0% catch rate by definition** — the plain pipeline would let every one of
  the 18 non-fully-correct answers through completely unflagged
- Even at today's precision: moving half of hallucinated answers from *silently wrong* to
  *flagged for review* is the entire point of the project

---

## Why precision is weak — three distinct causes

**66 false positives:**

1. **Wrong-scheme evidence (33, 50%)** — short, generic claims don't carry enough scheme-specific
   vocabulary for retrieval to anchor correctly
2. **Decomposition fragments that aren't real claims (26, 39% — the biggest single cause)** —
   bare entities ("EWS"), clauses that lost their antecedent when split on "aur" — nothing to
   verify, so UNVERIFIABLE is arguably the correct call on bad input
3. **"Absence" claims mishandled (7, 11%)** — the verifier prompt has no instruction for claims
   that describe evidence being *silent* on something — often true, but still flagged

(#2 was found correcting an earlier estimate that assumed #3 explained all of the "correct-scheme,
still-flagged" cases — it didn't; systematically re-checking all 33 found #2 is 4x bigger.)

**6 false negatives, three separate mechanisms:** bundled claims mixing true facts with
unverifiable generalizations, true-content-wrong-scheme cases, and a decomposition bug that drops
an exhaustiveness qualifier ("only X and Y") when splitting on "aur"

---

## What we'd fix next

1. **Highest value, revised**: tighten decomposition to drop fragments that aren't complete,
   checkable claims before they reach verification — biggest single cause (39% of false positives)
2. Stop treating "absence" claims like ordinary factual claims — smaller than first thought, still
   real
3. Scheme-filtered retrieval for evaluation isolation (not a legitimate deployed-system fix — a
   real user's scheme isn't known in advance)
4. Fix the remaining decomposition edge cases (compound claims, dropped qualifiers)
5. Re-run verification against the post-P-007 corrected knowledge base — one false positive is a
   confirmed artifact of stale, corrupted evidence, not a real weakness

None implemented yet — Week 4 ran out of scope for a re-measurement cycle. Recorded as next steps.

---

## A real bug the demo caught

Manually testing the finished demo surfaced a live example: a PM-KISAN question returned
**"Rs. 60,001 per year"** — confidently marked SUPPORTED at 0.98 confidence.

Not a generator hallucination — the scraped knowledge base itself had a PDF-extraction glitch
(`Rs.6000` → `Rs.60001`) that every downstream stage correctly treated as ground truth.

**Lesson**: "supported, high confidence" only means the claim matches its evidence — it says
nothing about whether the evidence is *correct*. A scraped-not-authored knowledge base needs
verification against its sources, not just internal consistency.

---

## Limitations, disclosed plainly

- Single annotator (AI-drafted, not yet human-reviewed) for both ground-truth files
- 60-question set — indicative for a course project, not a statistically powered benchmark
- Generator and verifier share one model — self-verification bias never separately measured
- Rule-based decomposition has known, documented failure modes on compound sentences
- Retrieval and verification quality are entangled in these numbers, not cleanly isolated

---

## The demo

Interactive walkthrough: Hinglish question in → generated answer → each claim colour-tagged

🟢 SUPPORTED · 🔴 CONTRADICTED · 🟡 UNVERIFIABLE — with confidence score, alongside the plain
untagged answer for direct comparison.

```
uv run streamlit run demo/app.py
```

---

# Thank you

Full report: `docs/report_architecture_and_implementation.md`,
`docs/report_evaluation_and_results.md`, `docs/error_analysis.md`

Repository: CodeSwitch-Verify
