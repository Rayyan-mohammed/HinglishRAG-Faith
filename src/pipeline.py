"""End-to-end orchestration: retrieve, generate, decompose, verify, aggregate."""

from src.config import TOP_K
from src.decomposition import decompose
from src.generation import generate_answer
from src.retrieval import retrieve
from src.verification import verify_claim


def answer_question(question, index, passages, verify=True):
    context_passages = retrieve(question, index, passages, top_k=TOP_K)
    answer = generate_answer(question, context_passages)

    result = {
        "question": question,
        "answer": answer,
        "context_passages": context_passages,
    }

    if verify:
        claims = decompose(answer)
        result["claims"] = [verify_claim(claim, index, passages) for claim in claims]

    return result
