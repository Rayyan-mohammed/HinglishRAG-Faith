"""Dense retrieval over the government scheme documents using bge-m3 + FAISS."""

import os
import pickle

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from config.settings import DATA_DIR, EMBEDDING_MODEL, INDEX_DIR, TOP_K

_model = None


def get_embedder():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def chunk_text(text, chunk_size=500, overlap=100):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks


def build_index(data_dir=DATA_DIR, index_dir=INDEX_DIR):
    embedder = get_embedder()
    passages = []

    for fname in sorted(os.listdir(data_dir)):
        path = os.path.join(data_dir, fname)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as f:
            text = f.read()
        for chunk in chunk_text(text):
            passages.append({"source": fname, "text": chunk})

    if not passages:
        raise ValueError(f"No documents found in {data_dir}")

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
