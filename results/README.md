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
- `verifier_results.pre-adr021.csv.bak` — the complete Groq/majority-vote ADR-020 result (209 rows,
  precision 0.25/recall 0.67), kept from before ADR-021's switch to Claude, LLM decomposition, and
  hybrid evidence retrieval. What ADR-021's before/after comparison used.

**Current state of `verifier_results.csv` (see ADR-021): complete.** 244 claims (decomposed by
`decompose_llm()`, judged by Claude with `n_samples=3` majority vote against a hybrid evidence pool
— generation's context passages merged with a fresh per-claim retrieval). Final numbers (precision
0.27, recall 0.71, false positives 32, false negatives 5) are the best precision and recall
simultaneously recorded anywhere in this project's history, and are reported throughout the docs.

**`metrics.md`'s answer-level numbers (strict/loose catch rate, false-alarm rate) reflect
human-reviewed ground truth (ADR-022)** — the 18 answer-level labels driving those numbers were
reviewed by the user, correcting 2 of 18 and moving strict catch rate 0.39→0.44, loose 0.50→0.56,
false-alarm rate 0.40→0.39. Claim-level precision/recall are unaffected by that review.

These are deliverables, not scratch output — commit them once they're produced, don't gitignore.
