"""End-to-end orchestration: retrieve, generate, decompose, verify, aggregate."""

import time
from concurrent.futures import ThreadPoolExecutor

from .settings import TOP_K
from .decomposition import decompose_llm
from .generation import generate_answer
from .retrieval import retrieve
from .verification import verify_claim

# Groq's free tier caps this org at ~8000 input tokens/minute, shared across all 3 configured
# keys (confirmed via the 429 error's org id -- they're the same org, so multi-key failover
# doesn't help against this specific limit). Each judge() call costs ~1100-1500 tokens; an answer
# that decomposes into many claims (eligibility/document-list questions commonly hit 10+) blows
# the budget even at n_samples=1 and 4-way concurrency, since the calls still all land in the
# same rolling minute. Capping how many claims actually get verified is the only bound that holds
# regardless of how many claims decomposition produces -- a disclosed demo-specific tradeoff
# (completeness for latency), not applied to the scored pipeline in ../../src.
MAX_VERIFIED_CLAIMS = 4


def answer_question(question, index, passages, verify=True):
    t0 = time.time()
    context_passages = retrieve(question, index, passages, top_k=TOP_K)
    print(f"[timing] retrieve: {time.time() - t0:.1f}s")

    t1 = time.time()
    answer = generate_answer(question, context_passages)
    print(f"[timing] generate_answer: {time.time() - t1:.1f}s")

    result = {
        "question": question,
        "answer": answer,
        "context_passages": context_passages,
    }

    if verify:
        t2 = time.time()
        all_claims = decompose_llm(answer)
        claims = all_claims[:MAX_VERIFIED_CLAIMS]
        print(
            f"[timing] decompose_llm: {time.time() - t2:.1f}s -> {len(all_claims)} claims "
            f"(verifying first {len(claims)})"
        )

        t3 = time.time()
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
        result["claims_truncated"] = len(all_claims) > len(claims)
        print(f"[timing] verify all claims: {time.time() - t3:.1f}s")

    print(f"[timing] TOTAL: {time.time() - t0:.1f}s")
    return result
