# CodeSwitch-Verify

Faithfulness-checked RAG for Hinglish government-scheme Q&A.

## Problem

RAG chatbots answering Hinglish (Hindi-English mixed) questions about Indian government schemes
generate fluent answers, but nothing checks whether every individual claim in the answer is
actually supported by the retrieved source document. An unsupported claim — a wrong eligibility
condition, a wrong deadline, a wrong amount — can pass through to the user undetected, in a domain
where being wrong has real consequences. This project adds a claim-level verification layer after
generation: every answer is broken into atomic claims, each claim is checked against retrieved
evidence, and unsupported claims are flagged instead of trusted blindly.

## Architecture

```mermaid
flowchart TD
    Docs[("Scheme documents<br/>(.gov.in sources)")] --> Embed["bge-m3 embedder"]
    Embed --> Index[("FAISS index")]

    Q(["User question (Hinglish)"]) --> S1["1. Retrieval"]
    Index --> S1
    S1 --> S2["2. Generation<br/>(Groq LLM)"]
    S2 --> S3["3. Claim decomposition"]
    S3 --> S4["4. Per-claim retrieval"]
    Index --> S4
    S4 --> S5["5. Verification<br/>(Groq LLM-as-judge)"]
    S5 --> S6["6. Aggregation"]
    S2 --> S6
    S6 --> Out(["Answer with claims tagged<br/>supported / contradicted / unverifiable"])
```

## How it works

| Component | What it does | Implementation |
|---|---|---|
| Retrieval | Embeds the question and finds the closest passages in the scheme documents | `src/retrieval.py` — bge-m3 + FAISS flat index |
| Generation | Answers the question in Hinglish, grounded only in retrieved passages | `src/generation.py` — Groq `openai/gpt-oss-120b` (see P-003) |
| Claim decomposition | Splits the generated answer into atomic, independently-checkable claims | `src/decomposition.py` — sentence + connector-word rules |
| Per-claim retrieval | Re-retrieves evidence specific to each individual claim | `src/retrieval.py`, called per claim in `src/verification.py` |
| Verification | Judges each claim against its evidence: supported / contradicted / unverifiable, with a confidence score | `src/verification.py` — Groq `openai/gpt-oss-120b` as LLM-as-judge, JSON output |
| Aggregation | Combines per-claim verdicts back into the answer for display | `src/pipeline.py` |

See [`docs/contracts.md`](docs/contracts.md) for exact function signatures and data formats.

## Setup

```
uv sync
cp .env.example .env   # add your Groq API key
```

Fetch the scheme facts dataset live from official `.gov.in` sources (writes one CSV per scheme
to `data/schemes/`):

```
uv run scripts/fetch_scheme_data.py
```

Then build the index:

```
uv run scripts/build_index.py
```

Run tests:

```
uv run python -m pytest
```
(`uv run pytest` invokes `pytest.exe` directly, which is blocked by an Application Control
policy on this machine — use `python -m pytest` instead.)

## Project layout

```
config/         settings (model names, paths, API key loading)
src/            pipeline code (retrieval, generation, decomposition, verification, evaluation)
scripts/        CLI entry points
tests/          unit tests
data/schemes/   one CSV per scheme, structured facts fetched live from official .gov.in sources
eval/           hand-labelled evaluation set (input questions + ground-truth labels)
results/        pipeline outputs (generated answers, verifier results, computed metrics)
demo/           working demo (Objective O6)
notebooks/      exploratory/prototyping work
docs/           planning docs, decision log, contracts, per-phase notes, error analysis, figures
```

## Results

60 questions, 212 decomposed claims, 24 ground-truth hallucinated (claim-level). Every one of
the 18 non-fully_correct answers reaches the plain (unverified) baseline unflagged — the verified
pipeline's whole value is in the columns below. Ground truth is an AI-drafted first pass, pending
human review (ADR-012, ADR-014) — read `docs/report_evaluation_and_results.md` before quoting
these numbers anywhere. Numbers below are from the P-008 re-run against the corrected knowledge
base (see P-007); P-008 also found real run-to-run non-determinism even at `temperature=0`, so
read these as one sample, not an exactly reproducible fixed measurement.

| Metric | Value |
|---|---|
| Recall on hallucinated claims | 0.71 |
| Precision on flagged claims | 0.21 |
| Answer-level catch rate (strict) | 0.50 |
| Answer-level catch rate (loose) | 0.78 |
| False-alarm rate on correct answers | 0.57 |

![Results chart](docs/figures/results_chart.png)

Full breakdown in [`results/metrics.md`](results/metrics.md); why precision is weak and what
specifically got missed or over-flagged is in [`docs/error_analysis.md`](docs/error_analysis.md).

## Final report

- [`docs/report_architecture_and_implementation.md`](docs/report_architecture_and_implementation.md)
  — system architecture, implementation notes per pipeline stage, tech stack (A4)
- [`docs/report_evaluation_and_results.md`](docs/report_evaluation_and_results.md) — evaluation
  methodology, results, limitations (B4)
- [`docs/error_analysis.md`](docs/error_analysis.md) — verifier mistakes reviewed in detail (B4)
- [`docs/slides.md`](docs/slides.md) — presentation slides (A4)

## Project status

**All 24 tasks across both tracks and all 4 weeks are done.** Verified, not assumed: full test
suite passes (`uv run python -m pytest`, 14 tests), and the complete pipeline was run live
end-to-end (retrieval → Hinglish generation → decomposition → per-claim verification) as a final
check — see the week-by-week log below and `docs/problems_and_decisions.md` for what "done"
actually involved (three memory-constrained index rebuilds, a Groq model deprecation mid-project,
a corrupted source PDF, non-deterministic verifier outputs, and two rounds of self-correction on
the error analysis, among other things).

**One item is deliberately not marked done, and isn't something this session can complete:**
`eval/labels.csv` and `eval/claim_ground_truth.csv` — the ground truth every precision/recall
number in this project rests on — are an AI-drafted first pass, `reviewed_by_human=FALSE` on
every row (ADR-012, ADR-014). This was an explicit choice, not an oversight: the blueprint's own
design (ADR-006) requires ground truth to come from a human specifically *because* the verifier
being measured is also an LLM — if the ground truth were AI-written too, the precision/recall
numbers would just measure two LLMs agreeing with each other, not real hallucination-catching
ability. That review is the one piece of this project that has to happen outside this session.
The 18 flagged answers (`label != fully_correct` in `eval/labels.csv`) are the highest-value
subset to check first, since they drive every downstream metric.

## Status

Week 1 done, both tracks. Track B: 60-question Hinglish evaluation set (`eval/questions.csv`)
across 4 fixed schemes, claim decomposition tested against hand-written Hinglish samples, verifier
prompt tested on 5 sample claim/evidence pairs (`scripts/test_verifier_samples.py`, 5/5 matched
expected verdict). Track A: structured scheme facts dataset — one CSV per scheme in
`data/schemes/`, 172 facts total across multiple official sources per scheme, fetched live by
`scripts/fetch_scheme_data.py` (PM-KISAN 43, Ayushman Bharat 37, PM Awas Yojana 58, Post-Matric
Scholarship 34), bge-m3 + FAISS index builds and returns sensible passages for Hinglish queries,
Groq API key confirmed working with a live chat completion call.

Week 2: Track A done — `scripts/generate_answers.py` runs the plain retrieve-then-generate
pipeline over every question in `eval/questions.csv` and writes `results/generated_answers.csv`.
All 60 answers generated, all consistently in Hinglish, no prompt tuning needed. Generation hit
Groq's free-tier 100k-tokens/day limit twice along the way (see P-001 in
`docs/problems_and_decisions.md`) — the script is resumable, so re-running it after each reset
picked up where it left off until all 60 were done.

Week 3: Track A done. Plain-RAG baseline confirmed — the 60 `pipeline == "plain"` rows in
`results/generated_answers.csv` from Week 2 are the unverified comparison condition, no separate
build needed. Demo skeleton done: `demo/app.py` (Streamlit) takes a Hinglish question, retrieves,
generates, and shows the answer plus retrieved sources — claim tags come later once B wires the
verifier in. Support/integration fixes: tested claim decomposition against all 60 real answers
and found 2 mis-split cases (P-002) — fixed the unambiguous one (an "Rs." abbreviation was
mistaken for a sentence boundary) directly with a regression test added, left the other (a
compound-subject "aur" split) alone since it's an intentionally-documented limitation owned by
B3. Along the way, found Groq had removed `llama-3.3-70b-versatile` from its catalog entirely,
breaking generation and verification for the whole team; swapped `GENERATOR_MODEL`/
`VERIFIER_MODEL` to `openai/gpt-oss-120b` (see P-003).

Week 4: Track B done. Verifier wired into the full pipeline (`scripts/verify_answers.py`) and run
on all 60 answers — 212 claims verified, resumable through a Groq TPM rate limit (P-005).
Claim-level ground truth derived (`eval/claim_ground_truth.csv`, ADR-014) since the blueprint's
answer-level labels can't compute Section 13.2's claim-level metrics directly. Precision/recall
computed (`results/metrics.md`, see Results above). Error analysis done
(`docs/error_analysis.md`) — traced the false positives to five causes across two rounds of
correction (each pass found the previous one had generalized from too small a sample — see
P-006 in `docs/problems_and_decisions.md`), then added full evidence-text logging and re-ran
verification against the P-007-corrected knowledge base to actually diagnose the previously-
"unexplained" cases (P-008): wrong-scheme retrieval (~33), decomposition damage/fragments (~13),
oversized multi-topic fact rows losing the retrieval race (part of ~12), genuine LLM-judge
misjudgment on complete correct evidence (the other part of that ~12 — a real reliability limit,
not a bug), "no info" claim mishandling (~7), plus one now-fixed stale-data artifact — and
reviewed all 7 false negatives individually. P-008 also found real run-to-run non-determinism
even at `temperature=0`. Evaluation methodology and results report sections written
(`docs/report_evaluation_and_results.md`). Results chart generated
(`docs/figures/results_chart.png`).

Track A done. Demo finished: `demo/app.py` now runs the full verified pipeline and shows each
claim colour-tagged (🟢 SUPPORTED / 🔴 CONTRADICTED / 🟡 UNVERIFIABLE) with its confidence score,
beside the plain untagged answer. Manually testing it surfaced a real data-quality bug — two
rupee amounts corrupted during PDF extraction (`Rs.6000` → `Rs.60001`) in
`data/schemes/PM-KISAN.csv` — fixed directly and documented (P-007), since a "supported, high
confidence" verdict only means a claim matches its evidence, not that the evidence is correct.
Architecture and implementation report sections written
(`docs/report_architecture_and_implementation.md`), pairing with Track B's evaluation/results
sections. Presentation slides prepared (`docs/slides.md`).

See [`docs/problems_and_decisions.md`](docs/problems_and_decisions.md) for the running decision
log.
