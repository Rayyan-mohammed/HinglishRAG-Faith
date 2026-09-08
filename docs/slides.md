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
2. **Generation** — answer in Hinglish, grounded only in retrieved passages (Claude)
3. **Claim decomposition** — split the answer into atomic, checkable claims (Claude, regex fallback)
4. **Per-claim retrieval** — evidence pool = generation's context passages + a fresh per-claim lookup
5. **Verification** — LLM-as-judge: supported / contradicted / unverifiable + confidence, majority of 3
6. **Aggregation** — combine verdicts back into the answer, shown next to the plain answer

Every component is pretrained and reused as-is — no model trained or fine-tuned.

---

## Knowledge base

**196 atomic facts**, scraped live from official `.gov.in` sources — not hand-written

| Scheme | Facts | Sources |
|---|---|---|
| PM-KISAN | 51 | Operational Guidelines + Revised FAQ + Additional FAQ (PDFs); grew from 43 as oversized rows were split into atomic facts (ADR-019) and a corrupted row was fixed (ADR-021) |
| Ayushman Bharat | 37 | Official FAQ + Benefits page |
| PM Awas Yojana | 63 | FAQ + PMAY-U 2.0 Operational Guidelines (PDF); grew from 58 as an oversized row was split (ADR-019) |
| Post-Matric Scholarship | 45 | National guidelines PDF + Maharashtra state page (originally 34 rows — one oversized row later split into 12 atomic facts, ADR-015) |

Re-fetchable and reproducible: `scripts/fetch_scheme_data.py` re-derives every file from its live
source on demand.

---

## Tech stack

| Component | Choice |
|---|---|
| Generator + decomposer + verifier | Anthropic API — `claude-haiku-4-5` (switched from Groq, ADR-021) |
| Embeddings | `BAAI/bge-m3`, local, multilingual |
| Vector store | FAISS, in-memory, local |
| Claim decomposition | LLM-based (Claude), rule-based Python as fallback |
| Demo | Streamlit |
| Dependencies | `uv` + `pyproject.toml`, 16 `pytest` tests |

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

- **Precision 0.27, recall 0.71** — the final, reported numbers, after three detours (next slides)
- **Best precision AND recall recorded simultaneously anywhere in this project** — beats every
  earlier state, including the very first pre-fix baseline (0.21/0.71)
- **The baseline has a 0% catch rate by definition** — the plain pipeline would let every one of
  the 18 non-fully-correct answers through completely unflagged
- Answer-level strict catch rate is 0.39 in the final measured run — *lower* than earlier rounds
  despite better precision/recall — see the third detour below for why
- Numbers are samples, not fixed measurements — re-running verification on identical claim text
  still moved individual verdicts run to run (confirmed directly on Groq, not just suspected), and
  even claim decomposition itself isn't perfectly stable run to run on identical input

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

## We shipped four fixes. Three worked outright. One broke, then got repaired

| Fix | Result |
|---|---|
| Split the oversized, multi-topic knowledge-base row into 12 atomic facts | ✅ Confirmed: the retrieval misses it targeted are gone |
| Drop degenerate decomposition fragments before verification | ✅ Confirmed: fragments no longer reach the judge |
| Add explicit prompt handling for "absence" claims | ⚠️ Correct in isolation, **regressed the full pipeline** — see next slide |
| Make that same instruction check topical relevance first | ✅ Repaired the regression, net-positive overall |

Round 1 → round 2: **precision 0.18 → 0.24, recall 0.42 → 0.67.**
Original → final: **precision 0.21 → 0.24, recall 0.71 → 0.67, false positives 65 → 50.**

---

## Why the third fix backfired

The absence-claim fix told the judge: *"if the evidence doesn't discuss this, an 'it's not
mentioned' claim is accurate — say SUPPORTED."* Verified correct with hand-written test cases
before shipping.

The problem: wrong-scheme retrieval was **deliberately left unfixed** (a real user's question
isn't pre-labeled with its scheme). When retrieval pulls evidence from the wrong scheme, that
evidence genuinely doesn't discuss the claim's real topic — so the instruction told the judge to
trust that absence. **9 of 14 new false negatives (64%) had wrong-scheme evidence.**

Before the fix, bad evidence more often produced a hedge (UNVERIFIABLE — still counted as
flagged). After the fix, the same bad evidence produced confident SUPPORTED. The fix made the
judge more decisive; decisiveness on bad evidence is worse than a hedge.

**We tried to measure the isolated effect** with an eval-only, scheme-filtered retrieval
diagnostic (never wired into the real pipeline) — it got 53 of 209 claims through before hitting
a persistent Windows security policy blocking native library DLLs, unrelated to the logic. That
diagnostic turned out not to be necessary — see next slide.

---

## The fix for the fix, not a reversion

Reverting would have erased the regression but also the fix's real, verified benefit, and
wouldn't have touched the actual problem (wrong-scheme retrieval) — just hidden it behind a less
decisive judge again.

**Instead: added one precondition to the same instruction.** Before trusting an "it's not
mentioned" reading, the judge now checks whether the evidence is even about the claim's
scheme/subject at all — schemes are named explicitly in almost every passage, so an LLM can
notice this directly from the text, no retrieval score or scheme-filter needed.

Verified against the exact real case that caused a false negative (evidence entirely about a
different scheme) before re-running everything: flipped SUPPORTED → UNVERIFIABLE, as intended. No
regression on the cases that already worked.

**Result: precision 0.24, recall 0.67** — better than where the project started on precision,
false positives, and false-alarm rate; recall recovered to within 4 points of the original.

---

## Second detour: extending the data fix surfaced a bigger problem

Extended row-splitting to PM-KISAN's and PM Awas Yojana's remaining oversized rows (183 → 197
facts) — the same fix that worked for Post-Matric Scholarship. Measuring it looked like a
regression (precision 0.24 → 0.22, recall 0.67 → 0.62).

**It wasn't really a regression — it was proof the judge is noisy.** Diffing the two runs found
20 verdict changes; **12 of them had byte-identical evidence text.** Same claim, same evidence,
different verdict, purely from re-running the judge — confirming what P-008 only suspected.

**Fix: majority-vote judging.** `verify_claim()` now takes 3 independent judge calls and returns
the majority verdict. Combined with the data fix: precision 0.25, recall 0.67 — essentially flat
versus the ADR-018 state, not a further win. Answer-level catch rate dipped slightly (0.50 → 0.44)
despite identical true/false-negative counts — the same catches landed on a different, one-fewer
unique answer. Reported as a wash, kept for sound engineering reasons, not a score claim.

---

## Third detour: switched Groq → Claude, and it actually moved the needle

Groq's daily quota kept blocking full runs — sometimes for days. Switched `generation.py`/
`decomposition.py`/`verification.py` to Claude (Haiku 4.5), and while doing so: replaced regex
claim decomposition with an LLM-based version, and redesigned `verify_claim()`'s evidence pool.

First tried evidence pool = *only* the passages that generated the answer (avoids wrong-scheme
evidence a short claim's own retrieval pulls in). It worked for that — false-alarm rate improved —
but **recall dropped (0.67 → 0.50)**. Reading evidence text directly explained why: verification
now shared generation's blind spots. If generation's retrieval missed a fact, verification saw the
exact same gap and confirmed a false "context doesn't say this" claim as SUPPORTED.

**Fix: merge, don't choose.** Evidence pool = context passages **+** a fresh per-claim retrieval,
deduplicated. While diagnosing the regression, also found and fixed a real data-corruption bug — a
`PM-KISAN.csv` row titled "exclusion criteria" had a body that duplicated an unrelated fact,
traced to the same malformed source PDF as an earlier data bug (P-007).

**Result: precision 0.27, recall 0.71, false positives 32, false negatives 5** — better than every
prior state on both axes at once. Answer-level catch rate went the other way (0.44 → 0.39) — an
expected side effect: fewer false positives means fewer answers get a claim flagged "by accident."

---

## What's still open — named, not hand-waved

- **Decomposition still occasionally bundles claims it correctly splits elsewhere** (Q10) —
  switching to an LLM decomposer reduced this but didn't eliminate it, and the LLM decomposer
  isn't perfectly stable run-to-run on identical input either (a negation was dropped on one claim
  between two runs, flipping its truth value).
- **True-content-wrong-scheme attribution** (Q30): a real fact presented as belonging to the wrong
  scheme's answer. No version of this verifier checks claim-vs-question-scheme, only
  claim-vs-evidence — would need a structurally different check.
- **A document-structure scope mismatch** (Q49): "the scheme has two models" is true of one
  vertical, not the whole scheme — the verifier has no way to represent that distinction.
- **Genuine LLM-judge misjudgment**: Q42's caste-certificate claim — correct evidence, wrong
  verdict anyway. A real reliability limit on the method, not an engineering bug (found on Groq,
  not re-tested against Claude).
- **Non-determinism, at two layers now**: the judge (confirmed directly — 12 of 20 verdict changes
  on identical evidence across two Groq runs; majority voting reduces but doesn't eliminate this)
  and, newly found, the LLM-based decomposer itself.

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
- Retrieval and verification quality are still entangled for the right-scheme-but-incomplete
  case — the relevance fix only resolves the clearly-wrong-scheme subset
- One confirmed genuine LLM-judge misjudgment (Q42) — a reliability ceiling on the method itself,
  not something any prompt change fixed

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
