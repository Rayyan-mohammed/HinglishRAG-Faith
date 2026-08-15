"""Dense retrieval over the government scheme facts dataset using bge-m3 + FAISS."""

import os
import pickle

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

from config.settings import EMBEDDING_MODEL, INDEX_DIR, SCHEMES_CSV, TOP_K

_model = None


def get_embedder():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def build_index(csv_path=SCHEMES_CSV, index_dir=INDEX_DIR):
    embedder = get_embedder()
    df = pd.read_csv(csv_path)

    passages = [{"source": row.scheme, "text": row.fact} for row in df.itertuples()]

    if not passages:
        raise ValueError(f"No facts found in {csv_path}")

    embeddings = embedder.encode([p["text"] for p in passages], normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype="float32")

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    os.makedirs(index_dir, exist_ok=True)
    faiss.write_index(index, os.path.join(index_dir, "scheme_docs.faiss"))
    with open(os.path.join(index_dir, "passages.pkl"), "wb") as f:
        pickle.dump(passages, f)

    return index, passages


def load_index(index_dir=INDEX_DIR):
    index = faiss.read_index(os.path.join(index_dir, "scheme_docs.faiss"))
    with open(os.path.join(index_dir, "passages.pkl"), "rb") as f:
        passages = pickle.load(f)
    return index, passages


def retrieve(query, index, passages, top_k=TOP_K):
    embedder = get_embedder()
    query_vec = embedder.encode([query], normalize_embeddings=True)
    query_vec = np.array(query_vec, dtype="float32")

    scores, ids = index.search(query_vec, top_k)
    results = []
    for score, idx in zip(scores[0], ids[0]):
        if idx == -1:
            continue
        results.append({**passages[idx], "score": float(score)})
    return results
