"""End-to-end orchestration: retrieve, generate, decompose, verify, aggregate."""

from concurrent.futures import ThreadPoolExecutor

from .settings import TOP_K
from .decomposition import decompose_llm
from .generation import generate_answer
from .retrieval import retrieve
from .verification import verify_claim


def answer_question(question, index, passages, verify=True):
    context_passages = retrieve(question, index, passages, top_k=TOP_K)
    answer = generate_answer(question, context_passages)

    result = {
        "question": question,
        "answer": answer,
        "context_passages": context_passages,
    }

    if verify:
        claims = decompose_llm(answer)
        # Claims are verified independently -- running them concurrently (each already fans out
        # into its own thread pool for its n_samples judge() calls, see verify_claim) is the
        # other half of keeping a multi-claim verified request under CloudFront's 60s timeout.
        with ThreadPoolExecutor(max_workers=max(len(claims), 1)) as pool:
            result["claims"] = list(
                pool.map(
                    lambda c: verify_claim(c, index, passages, context_passages=context_passages),
                    claims,
                )
            )

    return result
