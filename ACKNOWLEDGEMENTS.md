# Acknowledgements

This project builds on the following freely available tools and research:

- **Groq** — free-tier LLM inference used for both answer generation and claim verification
- **BAAI/bge-m3** — pretrained multilingual embedding model used for dense retrieval
- **FAISS** (Meta AI) — local vector search

The claim-decomposition and per-claim verification approach follows established
RAG evaluation research:

- S. Min et al., "FActScore: Fine-grained Atomic Evaluation of Factual Precision
  in Long Form Text Generation," EMNLP, 2023.
- C. Niu et al., "RAGTruth: A Hallucination Corpus for Developing Trustworthy
  Retrieval-Augmented Language Models," ACL, 2024.
- J. Saad-Falcon et al., "ARES: An Automated Evaluation Framework for
  Retrieval-Augmented Generation Systems," arXiv:2311.09476, 2024.
