# Results

Pipeline outputs, as opposed to `eval/` which holds the input question set and ground-truth
labels. Formats are defined in [`../docs/contracts.md`](../docs/contracts.md):

- generated answers (plain pipeline) — `generated_answers.csv`, built in A2, all 60 rows with
  `pipeline == "plain"`. This is also the plain-RAG baseline (unverified) comparison condition
  for Week 3 (A5) — no separate baseline file needed, it's the same data.
- generated answers (verified pipeline) — same file, `pipeline == "verified"` rows appended once
  B3/B4 wire the verifier in and re-run generation with verification on.
- verifier results (per-claim verdicts) — built in B3
- computed precision/recall/answer-level catch rate — built in B4

These are deliverables, not scratch output — commit them once they're produced, don't gitignore.
