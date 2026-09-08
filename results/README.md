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
- `verifier_results.pre-P007.csv.bak` — snapshot of `verifier_results.csv` from before the P-008
  re-run against the P-007-corrected knowledge base. Kept for reference (it's what P-008's
  before/after non-determinism comparison used); not the current results, not read by any script.
- `verifier_results.pre-fixes.csv.bak` — snapshot from before ADR-015's fixes (decomposition
  filter, data split, first version of the absence-claim prompt). What ADR-017's regression
  comparison used.
- `verifier_results.pre-relevance-fix.csv.bak` — snapshot from after ADR-015 but before ADR-018's
  relevance-check repair, i.e. the regressed state itself (precision 0.18, recall 0.42). What
  ADR-018's before/after comparison used.

None of the `.bak` snapshots are the current results or read by any script — they're kept purely
so the before/after numbers quoted in `docs/problems_and_decisions.md` are reproducible from the
repo, not just asserted in prose.

- `verifier_results.pre-adr019.csv.bak` — the complete, single-sample ADR-018 baseline (209 rows,
  precision 0.24/recall 0.67), kept from before ADR-019's data split and ADR-020's majority-vote
  judging. What ADR-019's and ADR-020's before/after comparisons used.

**Current state of `verifier_results.csv` (see ADR-019/ADR-020): complete.** All 209 claims judged
with ADR-020's `n_samples=3` majority vote against the post-ADR-019 index (197 facts). Getting here
took two calendar days and several resume cycles — the run paused once on Groq's daily token quota
(majority voting triples API cost) and again on a low-free-RAM DLL failure loading the embedding
model, both handled by the script's existing resumability, no code changes needed. Final numbers
(precision 0.25, recall 0.67, strict catch rate 0.44) are reported throughout the project's docs.

These are deliverables, not scratch output — commit them once they're produced, don't gitignore.
