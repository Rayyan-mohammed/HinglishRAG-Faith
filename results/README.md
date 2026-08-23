# Results

Pipeline outputs, as opposed to `eval/` which holds the input question set and ground-truth
labels. Formats are defined in [`../docs/contracts.md`](../docs/contracts.md):

- generated answers (plain pipeline) — `generated_answers.csv`, built in A2, all 60 rows with
  `pipeline == "plain"`. This is also the plain-RAG baseline (unverified) comparison condition
  for Week 3 (A5) — no separate baseline file needed, it's the same data.
- verifier results (per-claim verdicts) — `verifier_results.csv`, built in B3. Verifies the
  existing 60 `pipeline == "plain"` answers directly, does not re-generate them. See ADR-013 in
  `docs/problems_and_decisions.md` for why this replaced the original plan of re-running
  generation with verification "on" to get separate `pipeline == "verified"` rows.
- computed precision/recall/answer-level catch rate — `metrics.md`, built in B3/B4 by
  `scripts/compute_metrics.py`, using `eval/claim_ground_truth.csv` (claim-level ground truth,
  ADR-014) alongside `eval/labels.csv`

These are deliverables, not scratch output — commit them once they're produced, don't gitignore.
