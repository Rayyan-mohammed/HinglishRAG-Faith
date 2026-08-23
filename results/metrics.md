# Verification Layer Results

Computed from `results/verifier_results.csv` (212 claim verdicts) against two ground truths:
`eval/claim_ground_truth.csv` (claim-level, derived per ADR-014) and `eval/labels.csv`
(answer-level, ADR-012 — both are AI-drafted, pending human review).

## Claim-level precision/recall (Section 13.2, metrics 1-2)

| Metric | Value |
|---|---|
| Precision on flagged claims | 0.21 |
| Recall on hallucinated claims | 0.75 |
| True positives | 18 |
| False positives | 66 |
| False negatives | 6 |

Of 212 total claims, 24 were ground-truth hallucinated (a false or unsupported individual
statement), 188 were not.

## Answer-level catch rate (Section 13.2, metric 3)

| Definition | Value |
|---|---|
| Strict — verifier flagged a claim that IS a true hallucination | 0.50 |
| Loose — verifier flagged *any* claim in the answer, correct or not | 0.78 |

18 of 60 answers are ground-truth not-fully-correct (partially or fully hallucinated, per
`eval/labels.csv`). The gap between strict and loose above matters: loose counts an answer as
"caught" even if the verifier flagged an unrelated claim for the wrong reason while missing the
actual problem — see ADR-014 for why 7 of the 18 flagged answers have zero individually-false
claims at all (the problem was relevance/completeness, not a false statement), which the strict
number correctly treats as *not* catchable by a claim-level verifier.

## False alarm rate on correct answers

26 of 42 fully_correct answers had at least one claim flagged (CONTRADICTED or
UNVERIFIABLE) despite the answer being ground-truth correct — a false-alarm rate of
0.62. Not one of the blueprint's named metrics, but relevant to precision: it's
the direct source of false positives.
