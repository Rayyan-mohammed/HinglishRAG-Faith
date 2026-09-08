# Verification Layer Results

Computed from `results/verifier_results.csv` (244 claim verdicts) against two ground
truths: `eval/claim_ground_truth.csv` (claim-level, derived per ADR-014) and `eval/labels.csv`
(answer-level, ADR-012 — both are AI-drafted, pending human review).

## Claim-level precision/recall (Section 13.2, metrics 1-2)

| Metric | Value |
|---|---|
| Precision on flagged claims | 0.27 |
| Recall on hallucinated claims | 0.71 |
| True positives | 12 |
| False positives | 32 |
| False negatives | 5 |

Of 244 total claims, 17 were ground-truth hallucinated (a false or
unsupported individual statement), 227 were not.

## Answer-level catch rate (Section 13.2, metric 3)

| Definition | Value |
|---|---|
| Strict — verifier flagged a claim that IS a true hallucination | 0.44 |
| Loose — verifier flagged *any* claim in the answer, correct or not | 0.56 |

16 of 60 answers are ground-truth not-fully-correct (partially or
fully hallucinated, per `eval/labels.csv`). The gap between strict and loose above matters: loose
counts an answer as "caught" even if the verifier flagged an unrelated claim for the wrong reason
while missing the actual problem — see ADR-014 for why 5 of the
16 flagged answers have zero individually-false claims at all (the problem was
relevance/completeness, not a false statement), which the strict number correctly treats as *not*
catchable by a claim-level verifier.

## False alarm rate on correct answers

17 of 44 fully_correct answers had at least one claim flagged
(CONTRADICTED or UNVERIFIABLE) despite the answer being ground-truth correct — a false-alarm rate
of 0.39. Not one of the blueprint's named metrics, but relevant to
precision: it's the direct source of false positives.
