# Evaluation Methodology and Results

Track B's sections of the final report — pairs with Track A's architecture and implementation
sections (A4). Written from `docs/problems_and_decisions.md`, `docs/error_analysis.md`, and
`results/metrics.md`; those are the source of truth if anything here needs updating.

## Evaluation Methodology

**Dataset.** 60 hand-written Hinglish questions across 4 government schemes (PM-KISAN, Ayushman
Bharat, Post-Matric Scholarship, PM Awas Yojana), 15 per scheme, evenly split across four
categories: eligibility, deadline, amount, documents (`eval/questions.csv`). The knowledge base
is 172 atomic facts extracted from official `.gov.in` sources per scheme (`data/schemes/*.csv`),
fetched live and reproducible by re-running `scripts/fetch_scheme_data.py`.

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

| Metric | Value |
|---|---|
| Precision on flagged claims | 0.21 |
| Recall on hallucinated claims | 0.75 |
| Answer-level catch rate (strict) | 0.50 |
| Answer-level catch rate (loose) | 0.78 |
| False-alarm rate on correct answers | 0.62 |

Full breakdown (TP/FP/FN counts) in `results/metrics.md`.

**Reading these numbers honestly:** recall is the strong number here — the verifier catches 3 of
every 4 genuine hallucinated claims, and 50% of answers containing a real hallucination have it
correctly flagged. Precision is weak: only 1 in 5 flagged claims is an actual hallucination. This
is not a small-sample artifact with an obvious single cause — `docs/error_analysis.md` traces the
66 false positives to two distinct, roughly equal-sized mechanisms (wrong-scheme evidence
retrieval, and the verifier mishandling claims that describe an *absence* of information), and
the 6 false negatives to three further distinct causes (bundled claims, true-content-wrong-scheme
cases the verifier structurally can't judge, and a decomposition qualifier-dropping bug). The
"strict" vs "loose" catch-rate gap (0.50 vs 0.78) exists because 7 of the 18 flagged answers
turned out, on claim-by-claim re-check, to have no individually-false claim at all — their
problem was relevance or completeness, which a claim-level supported/contradicted check cannot
catch by construction, independent of how well any single component performs.

**Comparison to the plain (unverified) baseline:** every one of the 18 non-fully_correct answers
would have reached the user completely unflagged under the plain pipeline — the baseline has, by
definition, a 0% catch rate on anything. Even at today's precision, the verified pipeline moving
half of those hallucinated answers from "silently wrong" to "flagged for review" is the entire
point of the project. Whether that trade — catching half of the problem at the cost of also
flagging most correct answers unnecessarily — is worth shipping as-is, or whether the precision
problem needs fixing first, is exactly the kind of judgment call the error analysis exists to
inform rather than settle.

## Limitations

- Single annotator (an AI first pass, not yet human-reviewed) for both ground-truth files —
  disclosed per ADR-006, ADR-012, ADR-014.
- 60-question evaluation set is appropriate for a course project's indicative result, not a
  statistically powered or publication-scale claim (blueprint Section 11).
- Generator and verifier share one model (`openai/gpt-oss-120b`) — the self-verification bias
  risk flagged in ADR-001 was never separately measured.
- Retrieval quality (wrong-scheme contamination, P-004/P-006) is entangled with verification
  quality in these numbers; the error analysis attributes failures to a specific stage where
  possible, but a cleaner experiment would isolate them (e.g. by re-running verification against
  scheme-filtered retrieval, as suggested but not implemented in `docs/error_analysis.md`).
