# Problems and Decisions Log

Running log. Append new entries at the bottom of each section, don't rewrite history.

## Architecture Decisions

### ADR-001: Same model (Groq llama-3.3-70b-versatile) for both generation and verification
**Decision:** Use one Groq-hosted model for both answering the question and judging claims against evidence, with separate prompts for each role.
**Why:** Free tier, no GPU, one API key to manage, fast enough to run 50-80 questions in minutes.
**Impact:** Open risk — a model may be more likely to rate its own generation style as supported (self-verification bias). Not corrected for; worth checking during error analysis (Week 4) whether missed hallucinations cluster around a particular phrasing style.

### ADR-002: BAAI/bge-m3 as the sole embedding model, run locally
**Decision:** One pretrained multilingual embedding model for all retrieval (question-level and per-claim), no fine-tuning.
**Why:** Handles Hindi-English mixed text out of the box; free; no training budget or GPU in scope.
**Impact:** Retrieval quality is whatever bge-m3 gives on Hinglish — not tunable within the project. A retrieval failure and a verification failure will look identical from the outside unless logged separately.

### ADR-003: Rule-based claim decomposition (sentence boundaries + connector-word list)
**Decision:** Split generated answers into atomic claims with regex sentence splitting plus a fixed connector-word list (aur, lekin, but, however, ...), not a trained parser.
**Why:** Transparent, debuggable, sufficient at this scale; a full parser is unnecessary engineering for a 4-week course project.
**Impact:** Known failure mode — will mis-split some code-mixed sentences. Mitigation is manual review of decomposition output during Week 3 (see B3) and adjusting the connector list, not a general fix.

### ADR-004: FAISS flat index (in-memory, local), no vector DB server
**Decision:** `IndexFlatIP` over normalized embeddings, rebuilt from scratch by `scripts/build_index.py`.
**Why:** 3-5 documents means brute-force cosine similarity is instant; a server-backed vector DB would be pure overhead.
**Impact:** Doesn't scale past course-project size — fine here, would need revisiting for more documents.

### ADR-005: Per-claim retrieval, not reuse of the question-level retrieval
**Decision:** Stage 4 re-queries the index with each individual claim rather than reusing the passages retrieved for the original question.
**Why:** The passage that best supports the whole answer isn't always the passage that supports any one claim inside it.
**Impact:** Doubles retrieval calls per question (cheap, local) but adds a second retrieval failure mode to account for during error analysis — a claim can be correct but get flagged wrong because per-claim retrieval missed the right passage.

### ADR-006: Single annotator for the 50-80 question ground-truth set
**Decision:** Partner B hand-labels every generated answer (fully correct / partially hallucinated / fully hallucinated) alone.
**Why:** Team of 2 at course-project scale; coordinating a second labeller for inter-annotator agreement isn't in the 4-week budget.
**Impact:** No inter-annotator agreement number. Disclosed as a limitation in the final report rather than hidden. Consider re-reviewing a random sample of labels a second time before finalizing (see risk table in blueprint Section 17).

### ADR-007: uv + pyproject.toml for dependency management
**Decision:** Project dependencies declared in `pyproject.toml`, resolved and locked with `uv` (`uv.lock`), no `requirements.txt`.
**Why:** Reproducible lockfile, faster installs than pip, single tool for venv + deps + running scripts.
**Impact:** Contributors need `uv` installed. `uv run pytest` doesn't work on this machine due to a Windows Application Control policy blocking `pytest.exe` — use `uv run python -m pytest` instead.

### ADR-008: `config/` package separated from `src/` pipeline code
**Decision:** All settings (model names, paths, API key loading) live in `config/settings.py`, imported by `src/*.py`, not inlined.
**Why:** Keeps model/version choices and paths in one place instead of scattered across pipeline modules.
**Impact:** One extra import line per module; negligible cost for the clarity.

### ADR-009: Fixed scheme list — PM-KISAN, Ayushman Bharat, Post-Matric Scholarship, PM Awas Yojana
**Decision:** These 4 schemes, chosen upfront so Track B could start writing evaluation questions in Week 1 without waiting on Track A's document collection.
**Why:** All well-known, high-traffic .gov.in schemes with clear eligibility/deadline/amount/document facts to ask about; matches the blueprint's example set in Section 12. 4 schemes keeps the 60-question set balanced at 15 questions each.
**Impact:** Track A's Week 1 document collection (A1) should target exactly these 4, using these names, so `eval/questions.csv`'s `scheme` column joins cleanly to `data/schemes/` once built.

### ADR-010: `judge()` split out from `verify_claim()` in `src/verification.py`
**Decision:** The LLM-as-judge prompt call now takes `(claim, evidence_text)` directly, with `verify_claim()` doing retrieval and then calling `judge()`.
**Why:** B1 needs to test the verifier prompt on 5 hand-written claim/evidence pairs before any retrieval index exists. Splitting the functions means that test doesn't need a fake index or fake passages.
**Impact:** None to existing behavior — `verify_claim()`'s output is unchanged, just calls through `judge()` now.

### ADR-011: `data/schemes/` is one structured facts CSV per scheme, fetched live from source, not free-text documents
**Decision:** Replaced the earlier plain-text scheme documents in `data/schemes/` with one CSV per scheme (`PM-KISAN.csv`, `Ayushman Bharat.csv`, `PM Awas Yojana.csv`, `Post-Matric Scholarship.csv`; columns: `category`, `fact`, `source_url`). Each row is one atomic fact extracted directly from an official `.gov.in` source. These files are generated by `scripts/fetch_scheme_data.py`, which fetches multiple real source documents per scheme over HTTP (operational guideline PDFs, FAQ PDFs/pages, benefit-summary pages) and parses each with one of five heuristics — `faq` (numbered Q&A), `sections` (lettered/roman-numeral clause headers), `clauses` (decimal-numbered clauses like `5.1.6`), `numbered` (plain numbered statements), `bullets` (one fact per line) — rather than being hand-copied. Re-running the script re-derives the dataset from the current live sources. Final counts: PM-KISAN 43 rows (Operational Guidelines + Revised FAQ + Additional FAQ), Ayushman Bharat 37 (FAQ + Benefits page), PM Awas Yojana 58 (FAQ + PMAY-U 2.0 Operational Guidelines, capped at 40 clauses), Post-Matric Scholarship 34 (national guidelines PDF + Maharashtra state page) — 172 facts total. `src/retrieval.py`'s `build_index()` reads every `*.csv` in `data/schemes/`, using each file's name as `passage["source"]`, and embeds each row's `fact` as its own passage. The old `chunk_text()` word-splitting step was removed since rows are already short enough to embed without chunking.
**Why:** Partner A wanted a structured, auditable, per-scheme dataset (one row per fact, with its source URL, reproducible by re-fetching) rather than prose documents or a single merged file, so every fact fed to the pipeline can be traced back to its official source and regenerated on demand.
**Impact:** Retrieval quality trade-off, flagged before implementing: bge-m3 embeddings of short atomic facts about the same scheme are more similar to each other than embeddings of full prose paragraphs, so at low `top_k` (e.g. `verify_claim()`'s default of 2) the single most relevant fact can occasionally rank below other facts about the same scheme. At the project's default `TOP_K=4` this wasn't observed to be a problem in spot checks, but it's worth watching during Week 3 error analysis — if per-claim verification (`top_k=2`) starts missing evidence that's clearly present in the dataset, raising that default is the first thing to try. A second risk: the fetch script's HTML/PDF parsing is heuristic (marker-text slicing, regex section/question splitting) and can silently miss or garble a section if a source page's structure changes — anyone re-running it should spot-check row counts and a few sample rows per scheme before trusting a refresh.

## Problems Encountered

Running log, in this format:

### [id]: [short title]
**Week:**
**Problem:**
**Fix:**
**Lesson:**

### P-001: Groq free-tier daily token limit hit mid-generation-run
**Week:** 2
**Problem:** Running `scripts/generate_answers.py` (A2) against all 60 eval questions hit Groq's free/on-demand tier limit of 100,000 tokens per day (TPD) partway through — the run stopped at question 56/60 with a `RateLimitError`, then again at 57/60 and 59/60 on subsequent attempts as newly-freed tokens got used up by the next call. This is a rolling-window daily quota, not a short-term rate limit, so retrying every 30s for 6 minutes didn't help — but the error message's "try again in Nm" countdown was accurate: it's a rolling 24h window that frees up tokens gradually, so waiting the full countdown (each attempt needed anywhere from ~5 to ~25 minutes) did eventually work.
**Fix:** Made `scripts/generate_answers.py` resumable — it now reads any existing `results/generated_answers.csv`, skips `question_id`s already present, and only generates the missing ones. This let completed answers be committed as progress instead of being discarded or re-generated (re-spending tokens) on every retry, and meant each retry only needed enough freed-up quota for the handful of questions still missing, not the full batch. All 60 answers were completed this way across roughly three rate-limit windows.
**Lesson:** For any future full-batch run against the Groq free tier (e.g. B3's per-claim verification pass in Week 3, which will multiply the number of calls by the average claims-per-answer), budget for hitting this same 100k-tokens/day ceiling more than once and design the driving script to be resumable from the start, not after the first failure. Trust the error message's countdown — it's a real rolling-window estimate, not a fixed daily reset.

### P-002: `src/decomposition.py` mis-splits on abbreviation periods and "aur"-joined compound subjects
**Week:** 3
**Problem:** While proactively testing `decompose()` against all 60 real generated answers (in support of B3, which finalizes decomposition against real output), 2 of 60 answers produced very short, meaningless claim fragments — `'EWS'` and `'Rs'` on their own. Root causes: (1) `split_sentences()`'s regex (`(?<=[.!?])\s+`) treats the period in an abbreviation like "Rs." as a sentence boundary whenever it's followed by whitespace, so "Rs. 3.00 lakhs" gets split into "Rs" + "3.00 lakhs"; (2) `split_on_connectors()` splits on every occurrence of "aur", including when it joins a compound subject rather than two independent claims (e.g. "EWS aur LIG category ke liye income criteria hai" → "EWS" + "LIG category ke liye income criteria hai").
**Fix:** Not fixed here — flagged for B3 (owned by Track B) rather than editing `decomposition.py` directly, since finalizing this function against real generated answers is explicitly a Track B task this week and I didn't want to collide with that work. Left as a documented, reproducible finding: run `decompose()` over `results/generated_answers.csv` question_ids 48 and 55 to see both cases.
**Lesson:** The abbreviation-period case is a general, fixable bug (a short list of known abbreviations like "Rs.", "Dr.", "Mr." could be excluded from sentence-boundary detection). The "aur"-as-compound-subject case is closer to the fundamentally ambiguous limitation ADR-003 already calls out and may not have a clean general fix — worth deciding case by case during B3's manual review rather than trying to solve it with more regex.

### P-003: Groq removed `llama-3.3-70b-versatile` entirely — GENERATOR_MODEL/VERIFIER_MODEL were broken for the whole team
**Week:** 3
**Problem:** While testing the Week 3 demo skeleton, every Groq call started failing with `NotFoundError: Error code: 404 - The model 'llama-3.3-70b-versatile' does not exist or you do not have access to it`, even though this exact model had generated all 60 Week 2 answers successfully earlier. Calling `client.models.list()` confirmed it: the model is gone from Groq's catalog entirely, along with every other Llama chat model — the current active list is `allam-2-7b`, `groq/compound`, `groq/compound-mini`, `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `openai/gpt-oss-safeguard-20b`, `qwen/qwen3.6-27b`, plus audio-only and guard-only models. This broke `GENERATOR_MODEL` and `VERIFIER_MODEL` in `config/settings.py` (ADR-001) for every team member, not just one script.
**Fix:** Tested the two most plausible replacements on both the generation prompt and the verifier's JSON-output prompt: `qwen/qwen3.6-27b` is a reasoning model that prepends a huge `<think>...</think>` block to every response (including the verifier's supposed-to-be-JSON-only output) — unusable without adding a strip step, and would burn through the daily token budget from P-001 far faster given how verbose the reasoning traces are. `openai/gpt-oss-120b` and `openai/gpt-oss-20b` both gave clean, correct Hinglish answers and clean, strict JSON verdicts (`{"verdict": "SUPPORTED", "confidence": 0.99}`) with no extra wrapping. Set both `GENERATOR_MODEL` and `VERIFIER_MODEL` to `openai/gpt-oss-120b`, keeping ADR-001's "same model for both roles" decision intact.
**Lesson:** Don't assume a model name that worked earlier in the same project still works later — Groq's free-tier catalog can change without warning, and unlike a rate limit this fails every single call with no retry that helps. If Groq calls start failing with a 404 `model_not_found` (not a 429), check `client.models.list()` before assuming it's a config or code bug. The already-generated `results/generated_answers.csv` content from Week 2 is unaffected (it's just text, sourced from the old model at the time), but anyone re-running generation or starting verification needs this model swap.
