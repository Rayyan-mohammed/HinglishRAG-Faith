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

**183 atomic facts**, scraped live from official `.gov.in` sources — not hand-written

| Scheme | Facts | Sources |
|---|---|---|
| PM-KISAN | 43 | Operational Guidelines + Revised FAQ + Additional FAQ (PDFs) |
| Ayushman Bharat | 37 | Official FAQ + Benefits page |
| PM Awas Yojana | 58 | FAQ + PMAY-U 2.0 Operational Guidelines (PDF) |
| Post-Matric Scholarship | 45 | National guidelines PDF + Maharashtra state page (originally 34 rows — one oversized row later split into 12 atomic facts, ADR-015) |

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
  claim-level (209 decomposed claims, 24 ground-truth hallucinated)
- **Protocol**: build index → generate plain-RAG answers → label ground truth → run full verified
  pipeline → compute precision/recall → review a sample of mistakes

Ground truth is an **AI-drafted first pass, disclosed as pending human review** — treated as
provisional throughout.

---

## Results

![w:900](figures/results_chart.png)

---

## Reading the results honestly

- **Precision is weak**: about 1 in 5-6 flagged claims is an actual hallucination
- **Recall is the number to watch — it dropped**: 0.71 → 0.42 after our own fixes (next slides
  explain why, in full)
- **The baseline has a 0% catch rate by definition** — the plain pipeline would let every one of
  the 18 non-fully-correct answers through completely unflagged
- The answer-level strict catch rate held steady at 0.50 despite the claim-level recall drop —
  the answers that got caught are still caught, driven by different claims within them
- Numbers are samples, not fixed measurements — re-running on identical claim text at
  `temperature=0` still moves individual verdicts run to run

---

## Why precision is weak — five causes, found over three rounds of investigation

1. **Wrong-scheme evidence (~50%)** — short, generic claims don't carry enough scheme-specific
   vocabulary for retrieval to anchor correctly
2. **Decomposition damage (~20%)** — bare fragments ("EWS"), clauses that lost their antecedent
   when split on "aur" — nothing complete to verify
3. **Oversized, multi-topic fact rows losing the retrieval race** — some knowledge-base rows
   cram a dozen sub-facts into one, diluting the embedding until a short but wrong fact wins
   instead — confirmed reproducible across two separate runs
4. **Genuine LLM-judge misjudgment on complete, correct evidence** — the judge had the right
   answer directly in front of it and still got it wrong; a real reliability limit on the method,
   not an engineering bug
5. **"Absence" claims mishandled (~10%)** — and found to run in *both* directions: the judge both
   over-flags true "silent on this" claims and accepts false ones

(#1 and #2 found correcting an initial estimate built from a handful of examples. #3 and #4 used
to be one lumped "unexplained" bucket — resolved only after adding full evidence-text logging and
re-running verification specifically to find out what the judge actually saw.)

**7 false negatives, four separate mechanisms:** bundled claims mixing true facts with
unverifiable generalizations, true-content-wrong-scheme cases, a decomposition bug that drops an
exhaustiveness qualifier ("only X and Y") when splitting on "aur", and the judge accepting false
absence-claims at face value

---

## We shipped three fixes. Two worked. One made things worse — on purpose, we found out why

| Fix | Result |
|---|---|
| Split the oversized, multi-topic knowledge-base row into 12 atomic facts | ✅ Confirmed: the retrieval misses it targeted are gone |
| Drop degenerate decomposition fragments before verification | ✅ Confirmed: fragments no longer reach the judge |
| Add explicit prompt handling for "absence" claims | ⚠️ Correct in isolation, **net-negative on the full pipeline** |

Before → after: **precision 0.21 → 0.18, recall 0.71 → 0.42.**

---

## Why the third fix backfired

The absence-claim fix tells the judge: *"if the evidence doesn't discuss this, an 'it's not
mentioned' claim is accurate — say SUPPORTED."* Verified correct with hand-written test cases
before shipping.

The problem: wrong-scheme retrieval was **deliberately left unfixed** (a real user's question
isn't pre-labeled with its scheme). When retrieval pulls evidence from the wrong scheme, that
evidence genuinely doesn't discuss the claim's real topic — so the new instruction tells the judge
to trust that absence. **9 of 14 new false negatives (64%) have wrong-scheme evidence.**

Before the fix, bad evidence more often produced a hedge (UNVERIFIABLE — still counted as
flagged). After the fix, the same bad evidence produces confident SUPPORTED. The fix made the
judge more decisive; decisiveness on bad evidence is worse than a hedge.

**We tried to measure the isolated effect** with an eval-only, scheme-filtered retrieval
diagnostic (never wired into the real pipeline) — it got 53 of 209 claims through before hitting
a persistent Windows security policy blocking native library DLLs, unrelated to the logic.
Deprioritized rather than fought further.

---

## The honest call we're leaving open

Reverting the prompt fix would erase the regression — but also erase its real, verified benefit,
and wouldn't fix the actual problem (wrong-scheme retrieval), just hide it behind a less decisive
judge again.

**Kept as-is, disclosed plainly**, because the real prerequisite — scoping retrieval correctly —
is identified but not completed. This is the project's one open, unresolved finding: a
locally-correct fix with a measured negative system effect, understood well enough to explain
exactly why, not well enough to call fixed.

---

## Everything else that's still true

- **Genuine LLM-judge misjudgment**: Q42's caste-certificate claim — correct evidence, wrong
  verdict anyway. A real reliability limit on the method, not an engineering bug.
- **Non-determinism**: re-verifying identical claim text at `temperature=0` still moves individual
  verdicts run to run — any single reported number is a sample, not a fixed measurement.
- **Wrong-scheme retrieval** remains the single largest identified cause of false positives
  (~50%) and, now, a driver of false negatives too — the real next step for this project.

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
- Retrieval and verification quality are entangled — confirmed concretely: a verifier fix that's
  correct in isolation regressed recall because retrieval quality wasn't fixed alongside it
- The absence-claim prompt fix ships with a known, measured recall regression (0.71→0.42), kept
  rather than reverted because reverting hides the real problem instead of fixing it

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
