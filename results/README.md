# Results

Pipeline outputs, as opposed to `eval/` which holds the input question set and ground-truth
labels. Formats are defined in [`../docs/contracts.md`](../docs/contracts.md):

- generated answers (plain pipeline) — `generated_answers.csv`, built in A2
- verifier results (per-claim verdicts) — built in B3
- computed precision/recall/answer-level catch rate — built in B4

These are deliverables, not scratch output — commit them once they're produced, don't gitignore.
