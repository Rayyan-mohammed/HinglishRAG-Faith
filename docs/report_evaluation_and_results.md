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

These are the final, reported numbers — from the ADR-015 fixes (decomposition fragment filter,
absence-claim prompt, knowledge-base granularity split), measured end-to-end (ADR-017) on a fresh
209-claim verification run against the corrected data. Reported as-is, including a regression that
wasn't the intended outcome — see below.

| Metric | Value |
|---|---|
| Precision on flagged claims | 0.18 |
| Recall on hallucinated claims | 0.42 |
| Answer-level catch rate (strict) | 0.50 |
| Answer-level catch rate (loose) | 0.72 |
| False-alarm rate on correct answers | 0.52 |

Full breakdown (TP/FP/FN counts) in `results/metrics.md`.

**Reading these numbers honestly — including the regression.** Before these fixes, the pipeline
measured precision 0.21 / recall 0.71. After: precision 0.18, recall 0.42. Two of the three fixes
worked exactly as intended (confirmed directly — the knowledge-base split fixed the specific
retrieval misses it targeted; the fragment filter removed degenerate non-claims from
verification). The third — an explicit prompt instruction for claims that describe an *absence*
of information — was also verified correct in isolation before shipping, but interacts badly with
a problem left deliberately unfixed: wrong-scheme retrieval. 9 of the 14 false negatives (64%,
up from 6 before) have evidence from the wrong scheme; when that happens, the new prompt
instruction tells the judge to trust the absence it sees (since the wrong evidence genuinely
doesn't discuss the claim's real topic) rather than hedge to UNVERIFIABLE as it more often did
before. The fix made the judge *more decisive* — and decisiveness on bad evidence is worse than a
hedge. Full mechanism and the diagnostic that was attempted (and blocked by an unrelated
environment issue) to measure the isolated effect are in ADR-017 and `docs/error_analysis.md`.

**Why this is reported rather than silently reverted:** reverting the prompt fix would remove the
regression but also remove its real, verified benefit whenever retrieval happens to be correct —
it wouldn't fix the underlying problem (wrong-scheme retrieval), just hide it behind a less
decisive judge again. The actual prerequisite — scoping retrieval correctly — is identified but
not completed in this pass. This is disclosed as the project's one open, unresolved finding
rather than smoothed over: a locally-verified-correct fix with a measured negative system-level
effect, understood well enough to say exactly why, not well enough to say it's fully fixed.

**Comparison to the plain (unverified) baseline still holds regardless:** every one of the 18
non-fully_correct answers would reach the user completely unflagged under the plain pipeline — a
0% catch rate on anything, by definition. The verified pipeline still catches half of those
answers (0.50 strict catch rate, unchanged by the regression above, since it's driven by
answer-level rather than claim-level flagging). Whether today's precision/recall trade is worth
shipping as-is, or whether retrieval needs fixing first, is the judgment call this report hands
off rather than settles.

## Limitations

- Single annotator (an AI first pass, not yet human-reviewed) for both ground-truth files —
  disclosed per ADR-006, ADR-012, ADR-014.
- 60-question evaluation set is appropriate for a course project's indicative result, not a
  statistically powered or publication-scale claim (blueprint Section 11).
- Generator and verifier share one model (`openai/gpt-oss-120b`) — the self-verification bias
  risk flagged in ADR-001 was never separately measured.
- Retrieval quality (wrong-scheme contamination, P-004/P-006) is entangled with verification
  quality in these numbers, confirmed concretely by ADR-017: a verifier-prompt fix that is
  correct in isolation produced a net-negative system result because retrieval quality wasn't
  fixed alongside it. An eval-only scheme-filtered diagnostic was built to isolate the two but
  didn't finish (blocked by an environment issue, not a logic one) — see ADR-017.
- The absence-claim prompt fix (ADR-015) is shipped with a known, measured recall regression
  (0.71→0.42) for a well-understood reason (above). This is the project's clearest example of a
  fix that needed a prerequisite (correct retrieval scoping) that wasn't in scope to complete.
