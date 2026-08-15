# Results

Pipeline outputs, as opposed to `eval/` which holds the input question set and ground-truth
labels. Formats are defined in [`../docs/contracts.md`](../docs/contracts.md):

- generated answers (plain + verified pipeline) — built in A2
- verifier results (per-claim verdicts) — built in B3
- computed precision/recall/answer-level catch rate — built in B4, also recorded in
  [`../docs/objective5_result.md`](../docs/objective5_result.md)

These are deliverables, not scratch output — commit them once they're produced, don't gitignore.
