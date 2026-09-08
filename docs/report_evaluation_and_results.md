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

These are the final, reported numbers — after nine fixes across four rounds (ADR-015, then
ADR-018's repair of a regression ADR-017 diagnosed in between, ADR-019/020's extended
data-granularity fix and majority-vote judging, then ADR-021's switch to Claude with LLM
decomposition and hybrid evidence retrieval), measured end-to-end on a fresh 244-claim
verification run against the corrected data and prompt.

| Metric | Value |
|---|---|
| Precision on flagged claims | 0.27 |
| Recall on hallucinated claims | 0.71 |
| Answer-level catch rate (strict) | 0.39 |
| Answer-level catch rate (loose) | 0.50 |
| False-alarm rate on correct answers | 0.40 |

Full breakdown (TP/FP/FN counts) in `results/metrics.md`.

**Reading these numbers honestly — including the detour.** Before any of these fixes, the
pipeline measured precision 0.21 / recall 0.71. The first round of fixes (ADR-015) regressed
recall to 0.42 — a real mistake, diagnosed rather than hidden (ADR-017): an explicit prompt
instruction for claims describing an *absence* of information was correct in isolation but
confidently validated false claims whenever retrieval fed it evidence from the wrong scheme,
since wrong-scheme evidence always looks silent on the claim's real topic. Rather than reverting
that fix — which would have erased the regression but also its real benefit, without touching the
underlying retrieval problem — it was repaired: the same instruction now checks whether the
evidence is even about the claim's scheme before trusting its silence (ADR-018), verified
directly against the actual failing case before the full re-run. That round landed at precision
0.24 and false-alarm rate 0.50, both beating the original pre-fix numbers, false positives dropped
from 65 to 50, and recall recovered to 0.67 — within 4 points of where the project started.

**A second round (ADR-019/020) landed roughly flat, not a further win.** Extending the
row-splitting fix to PM-KISAN's and PM Awas Yojana's remaining oversized rows, then measuring it,
surfaced a more important finding: the LLM judge isn't fully deterministic even at
`temperature=0` — direct proof came from finding that 12 of 20 verdict changes between two runs
had byte-identical evidence text. Majority-vote judging (3 judge calls per claim, majority wins)
was added to address that noise. The combined result: precision 0.25 and false-alarm rate 0.48
(both marginally better), recall unchanged at 0.67, but answer-level catch rate slightly *worse*
(strict 0.50→0.44) despite an identical true/false-negative count — the same total catches landed
on one fewer unique answer. Reported as a wash, kept for the underlying engineering soundness
(better data granularity, less reliance on a single judge sample) rather than a demonstrated score
gain — see `docs/problems_and_decisions.md` ADR-019/ADR-020 for the full mechanism.

**A third round (ADR-021) is the first to move precision and recall together.** Groq's daily
token quota had repeatedly paused full evaluation runs across several days, so the pipeline
switched to Claude (Haiku 4.5) for generation, decomposition, and verification. Two further
changes came with it: LLM-based claim decomposition (fixing qualifier-dropping and claim-bundling
bugs the regex splitter couldn't), and a redesigned evidence pool for `verify_claim()`. The
evidence-pool redesign went through two versions: context-passages-only (verify each claim
against exactly what generation retrieved) improved the false-alarm rate but regressed recall
(0.67→0.50) — confirmed by reading evidence text directly, it ties verification's blind spots to
generation's, so a fact generation's retrieval missed was invisible to verification too, even when
it existed elsewhere in the corpus. Fixed by merging context passages with a fresh per-claim
retrieval instead of choosing one or the other. While diagnosing the regression, a genuine data
corruption bug also surfaced and was fixed: a `PM-KISAN.csv` row titled "exclusion criteria" had a
mismatched body duplicating an unrelated fact, from the same malformed source PDF already flagged
in P-007. **Final result: precision 0.27, recall 0.71, false positives 32, false negatives 5** —
the best precision and recall recorded simultaneously anywhere in this project, beating both the
prior best (0.25/0.67) and the original pre-fix baseline (0.21/0.71) on precision while matching
it on recall. Answer-level catch rate moved the other way (strict 0.44→0.39, loose 0.72→0.50) — an
expected side effect of fewer false positives, not a new problem: catch rate rewards any claim in
an answer getting flagged, and a more precise verifier flags fewer claims "by accident."

**What's still open, named rather than hand-waved:** a still-inconsistent LLM decomposer on
bundled claims (Q10 — the same pattern it correctly splits elsewhere), true-content-wrong-scheme
attribution that needs a structurally different claim-vs-question-scheme check the verifier was
never designed to do (Q30), a document-structure scope mismatch it has no way to represent (Q49),
two retrieval-completeness gaps of the same shape the hybrid evidence pool fixed elsewhere but
didn't reach for these specific phrasings (Q24, Q51), and one confirmed case (Q42, from the
pre-switch Groq run, not re-tested against Claude) where the LLM-judge had the fully correct
evidence and still ruled wrong — a genuine reliability limit of the method itself, not an
engineering gap.

**Comparison to the plain (unverified) baseline still holds regardless:** every one of the 18
non-fully_correct answers would reach the user completely unflagged under the plain pipeline — a
0% catch rate on anything, by definition. The verified pipeline still catches a substantial share
of those answers (0.39 strict catch rate) while being more precise and less prone to false alarms
than at any earlier point in the project.

## Limitations

- Single annotator (an AI first pass, not yet human-reviewed) for both ground-truth files —
  disclosed per ADR-006, ADR-012, ADR-014.
- 60-question evaluation set is appropriate for a course project's indicative result, not a
  statistically powered or publication-scale claim (blueprint Section 11).
- Generator, decomposer, and verifier share one model (`claude-haiku-4-5`, switched from Groq's
  `openai/gpt-oss-120b` in ADR-021) — the self-verification bias risk flagged in ADR-001 was never
  separately measured, and the switch means both the Q42 misjudgment finding and the
  `temperature=0` non-determinism findings below were made on Groq, not re-tested against Claude.
- Retrieval quality (wrong-scheme contamination, P-004/P-006) is substantially, but not fully,
  disentangled from verification quality after ADR-021's hybrid evidence pool — it fixed most of
  the *right-scheme-but-incomplete* false negatives (Q2/Q3/Q43) but not all (Q24/Q51 remain), and
  doesn't address true-content-attributed-to-the-wrong-scheme cases (Q30) at all, which would need
  a structurally different claim-vs-question-scheme check.
- One confirmed genuine LLM-judge misjudgment (Q42, correct evidence, wrong verdict, found on the
  pre-switch Groq run) — a disclosed reliability ceiling on the LLM-as-judge method, not something
  a prompt fix resolved.
- `decompose_llm()` (Claude, replacing the regex splitter as of ADR-021) is not perfectly stable
  run-to-run on identical input — a negation was dropped on one claim between two runs on the same
  source answer, flipping its truth value. Ground truth is re-derived against the claim text as
  actually produced each run, but this means the *set* of claims a given answer decomposes into
  isn't perfectly reproducible across runs, unlike the deterministic regex fallback.
