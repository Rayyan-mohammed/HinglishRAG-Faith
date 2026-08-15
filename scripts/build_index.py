"""Builds the FAISS index from data/schemes/scheme_facts.csv. Run this after updating the dataset."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.retrieval import build_index

if __name__ == "__main__":
    index, passages = build_index()
    print(f"Indexed {len(passages)} facts from data/schemes/scheme_facts.csv")
