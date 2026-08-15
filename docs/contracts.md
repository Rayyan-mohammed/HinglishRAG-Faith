# Interface Contracts

Shapes and formats every component agrees on. Update this when a signature or format
changes — it's the source of truth for how A's and B's code plug together.

## Environment variables

| Var | Required | Used by |
|---|---|---|
| `GROQ_API_KEY` | yes | `src/generation.py`, `src/verification.py` |

## Passage format

Returned by retrieval, consumed by generation and verification.

```python
{"source": str, "text": str, "score": float}  # score only present on retrieve() output
```

## Function contracts (current, as implemented)

### `src/retrieval.py`
- `build_index(data_dir, index_dir) -> (faiss.Index, list[passage])` — reads all files in `data_dir`, chunks them, embeds with bge-m3, writes index + passages to `index_dir`.
- `load_index(index_dir) -> (faiss.Index, list[passage])`
- `retrieve(query: str, index, passages, top_k: int) -> list[passage]`

### `src/generation.py`
- `generate_answer(question: str, passages: list[passage]) -> str` — Hinglish answer, grounded only in given passages.

### `src/decomposition.py`
- `decompose(answer: str) -> list[str]` — atomic claims, order preserved.

### `src/verification.py`
- `verify_claim(claim: str, index, passages, top_k=2) -> dict`
  ```python
  {"verdict": "SUPPORTED" | "CONTRADICTED" | "UNVERIFIABLE",
   "confidence": float,        # 0.0-1.0
   "claim": str,
   "evidence": list[passage]}
  ```

### `src/pipeline.py`
- `answer_question(question: str, index, passages, verify=True) -> dict`
  ```python
  {"question": str,
   "answer": str,
   "context_passages": list[passage],
   "claims": list[verify_claim result]}   # only present if verify=True
  ```

### `src/evaluate.py`
- `precision_recall(predicted_flags: list[bool], true_flags: list[bool]) -> dict`
  `{"precision": float, "recall": float, "tp": int, "fp": int, "fn": int}`
- `answer_level_catch_rate(answers: list[{"has_hallucination": bool, "flagged": bool}]) -> float`

## Data formats (proposed, not yet built — confirm before B1/B2 lock these in)

Input test set lives in `eval/`. Pipeline outputs (generated answers, verifier results,
computed metrics) live in `results/` — see `results/README.md`.

### `eval/questions.csv`
| column | type | notes |
|---|---|---|
| `id` | int | stable across the whole project |
| `scheme` | str | which scheme document this targets |
| `category` | str | eligibility / deadline / amount / documents |
| `question` | str | Hinglish |

### `eval/labels.csv` (ground truth, built in B2)
| column | type | notes |
|---|---|---|
| `question_id` | int | joins to `questions.csv` |
| `label` | str | `fully_correct` / `partially_hallucinated` / `fully_hallucinated` |
| `notes` | str | optional, why this label |

### `results/generated_answers.csv` (built in A2, one row per question, per pipeline variant)
| column | type | notes |
|---|---|---|
| `question_id` | int | |
| `pipeline` | str | `plain` or `verified` |
| `answer` | str | raw generated text |

### `results/verifier_results.csv` (built in B3)
| column | type | notes |
|---|---|---|
| `question_id` | int | |
| `claim` | str | |
| `verdict` | str | SUPPORTED / CONTRADICTED / UNVERIFIABLE |
| `confidence` | float | |
| `evidence_source` | str | which scheme doc the evidence came from |

Once A2/B2/B3 actually produce these files, update this section to match reality if the
implementation diverges from the plan above.
