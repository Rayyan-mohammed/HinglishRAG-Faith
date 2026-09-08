# Evaluation Methodology and Results

Track B's sections of the final report — pairs with Track A's architecture and implementation
sections (A4). Written from `docs/problems_and_decisions.md`, `docs/error_analysis.md`, and
`results/metrics.md`; those are the source of truth if anything here needs updating.

## Evaluation Methodology

**Dataset.** 60 hand-written Hinglish questions across 4 government schemes (PM-KISAN, Ayushman
Bharat, Post-Matric Scholarship, PM Awas Yojana), 15 per scheme, evenly split across four
categories: eligibility, deadline, amount, documents (`eval/questions.csv`). The knowledge base
is 183 atomic facts extracted from official `.gov.in` sources per scheme (`data/schemes/*.csv`),
fetched live and reproducible by re-running `scripts/fetch_scheme_data.py` (originally 172 —
grew to 183 after ADR-015 split one oversized, multi-topic row into 12 atomic facts).

**Ground truth.** Two levels, both derived from the same underlying review process and both
disclosed as AI-drafted, pending human review — this is stated plainly because it materially
affects how these results should be read:

- *Answer-level* (`eval/labels.csv`, ADR-012): each of the 60 generated answers read against the
  source facts and labelled fully_correct / partially_hallucinated / fully_hallucinated. This
  matches the blueprint's Section 14 protocol exactly. 42 fully_correct, 12 partially_hallucinated,
  6 fully_hallucinated.
- *Claim-level* (`eval/claim_ground_truth.csv`, ADR-014): the 60 claims decomposed from the 18
  non-fully_correct answers re-checked individually against the source facts, since Section 13.2's
  precision/recall metrics need claim-level ground truth that answer-level labels can't provide
  directly. 24 of 212 total claims are ground-truth hallucinated.

The blueprint (ADR-006) frames ground-truth labelling as done by the project's human author
alone — the point of an independent ground truth is that it isn't produced by the same kind of
system (an LLM) as the verifier being measured against it. Both files here were drafted by
Claude and are marked `reviewed_by_human=FALSE` per row; treat every number in this section as
provisional until that review happens, and disclose the AI-assisted origin in any presentation
of these results — see ADR-012 for the full reasoning.

**Protocol.** Followed Section 14 exactly: (1) build the retrieval index over the 172 facts, (2)
generate plain-RAG answers for all 60 questions (`results/generated_answers.csv`, A2), (3) label
ground truth against the source facts, (4) run the full verified pipeline — decomposition,
per-claim retrieval, LLM-judge — over the same 60 answers (`scripts/verify_answers.py`, B3,
`results/verifier_results.csv`), (5) compute precision/recall against ground truth
(`scripts/compute_metrics.py`), (6) review a sample of the verifier's mistakes
(`docs/error_analysis.md`, B4).

One deliberate deviation from a literal reading of Section 13.1's plain-vs-verified comparison:
the verifier runs against the *same* 60 generated answers rather than a separately re-generated
"verified" batch — see ADR-013 for why re-generating a second time would confound the comparison
with generation randomness rather than isolating the effect of verification.

## Results

These are the final, reported numbers — after six fixes across three rounds (ADR-015, then
ADR-018's repair of a regression ADR-017 diagnosed in between, then ADR-019/020's extended
data-granularity fix and majority-vote judging), measured end-to-end on a fresh 209-claim
verification run against the corrected data and prompt.

| Metric | Value |
|---|---|
| Precision on flagged claims | 0.25 |
| Recall on hallucinated claims | 0.67 |
| Answer-level catch rate (strict) | 0.44 |
| Answer-level catch rate (loose) | 0.72 |
| False-alarm rate on correct answers | 0.48 |

Full breakdown (TP/FP/FN counts) in `results/metrics.md`.

**Reading these numbers honestly — including the detour.** Before any of these fixes, the
pipeline measured precision 0.21 / recall 0.71. The first round of fixes (ADR-015) regressed
recall to 0.42 — a real mistake, diagnosed rather than hidden (ADR-017): an explicit prompt
instruction for claims describing an *absence* of information was correct in isolation but
confidently validated false claims whenever retrieval fed it evidence from the wrong scheme,
since wrong-scheme evidence always looks silent on the claim's real topic. Rather than reverting
that fix — which would have erased the regression but also its real benefit, without touching the
underlying retrieval problem — it was repaired: the same instruction now checks whether the
evidence is even about the claim's scheme before trusting its silence (ADR-018), verified
directly against the actual failing case before the full re-run. That round landed at precision
0.24 and false-alarm rate 0.50, both beating the original pre-fix numbers, false positives dropped
from 65 to 50, and recall recovered to 0.67 — within 4 points of where the project started.

**A second round (ADR-019/020) landed roughly flat, not a further win.** Extending the
row-splitting fix to PM-KISAN's and PM Awas Yojana's remaining oversized rows, then measuring it,
surfaced a more important finding: the LLM judge isn't fully deterministic even at
`temperature=0` — direct proof came from finding that 12 of 20 verdict changes between two runs
had byte-identical evidence text. Majority-vote judging (3 judge calls per claim, majority wins)
was added to address that noise. The combined result: precision 0.25 and false-alarm rate 0.48
(both marginally better), recall unchanged at 0.67, but answer-level catch rate slightly *worse*
(strict 0.50→0.44) despite an identical true/false-negative count — the same total catches landed
on one fewer unique answer. Reported as a wash, kept for the underlying engineering soundness
(better data granularity, less reliance on a single judge sample) rather than a demonstrated score
gain — see `docs/problems_and_decisions.md` ADR-019/ADR-020 for the full mechanism.

**What's still open, named rather than hand-waved:** false negatives now trace mostly to
retrieval picking an ambiguous or wrong scheme's evidence for claims that don't name a scheme
explicitly (Q2/Q3/Q43/Q44 — extending row-splitting further didn't reach these, since none trace
to an oversized row), decomposition bundling or dropping qualifiers (Q10/Q51), and one confirmed
case (Q42) where the LLM-judge had the fully correct evidence and still ruled wrong — a genuine
reliability limit of the method itself, not an engineering gap.

**Comparison to the plain (unverified) baseline still holds regardless:** every one of the 18
non-fully_correct answers would reach the user completely unflagged under the plain pipeline — a
0% catch rate on anything, by definition. The verified pipeline still catches a substantial share
of those answers (0.44 strict catch rate) while remaining more precise and less prone to false
alarms than where this project started.

## Limitations

- Single annotator (an AI first pass, not yet human-reviewed) for both ground-truth files —
  disclosed per ADR-006, ADR-012, ADR-014.
- 60-question evaluation set is appropriate for a course project's indicative result, not a
  statistically powered or publication-scale claim (blueprint Section 11).
- Generator and verifier share one model (`openai/gpt-oss-120b`) — the self-verification bias
  risk flagged in ADR-001 was never separately measured.
- Retrieval quality (wrong-scheme contamination, P-004/P-006) is still entangled with
  verification quality for the *right-scheme-but-incomplete* case — ADR-018's relevance check
  only resolves the *clearly-wrong-scheme* subset. A genuine fix would mean better retrieval
  (larger `top_k`, reranking, or extending the row-splitting from ADR-015 to more of
  `data/schemes/*.csv`), not attempted here.
- One confirmed genuine LLM-judge misjudgment (Q42, correct evidence, wrong verdict) — a
  disclosed reliability ceiling on the LLM-as-judge method, not something a prompt fix resolved.
