"""Week 2 (A2): runs the plain retrieve->generate pipeline on every question in
eval/questions.csv and writes results/generated_answers.csv. Resumable: re-running only
fills in question_ids missing from the existing output (e.g. after a rate limit)."""

import csv
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config.settings import EVAL_DIR, TOP_K
from src.generation import generate_answer
from src.retrieval import load_index, retrieve

RESULTS_DIR = Path("results")

if __name__ == "__main__":
    index, passages = load_index()
    questions = pd.read_csv(Path(EVAL_DIR) / "questions.csv")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / "generated_answers.csv"

    done_ids = set()
    if out_path.exists():
        done_ids = set(pd.read_csv(out_path)["question_id"])

    remaining = questions[~questions["id"].isin(done_ids)]
    print(f"{len(done_ids)} already done, {len(remaining)} remaining")

    with open(out_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["question_id", "pipeline", "answer"])
        if not done_ids:
            writer.writeheader()

        for row in remaining.itertuples():
            context = retrieve(row.question, index, passages, top_k=TOP_K)
            answer = generate_answer(row.question, context)
            writer.writerow({"question_id": row.id, "pipeline": "plain", "answer": answer})
            f.flush()
            print(f"[{row.id}/{len(questions)}] {row.scheme}: {answer[:70]}...")

    print(f"\nDone. {out_path} now has {len(done_ids) + len(remaining)} answers.")
