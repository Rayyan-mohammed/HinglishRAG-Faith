"""Computes precision/recall of the verification layer against hand-labelled ground truth."""


def precision_recall(predicted_flags, true_flags):
    """predicted_flags / true_flags: lists of bool, same length, one entry per claim.
    True means "hallucinated" (contradicted or unverifiable / actually wrong)."""
    tp = sum(p and t for p, t in zip(predicted_flags, true_flags))
    fp = sum(p and not t for p, t in zip(predicted_flags, true_flags))
    fn = sum(not p and t for p, t in zip(predicted_flags, true_flags))

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return {"precision": precision, "recall": recall, "tp": tp, "fp": fp, "fn": fn}


def answer_level_catch_rate(answers):
    """answers: list of dicts with 'has_hallucination' (bool) and 'flagged' (bool)."""
    hallucinated = [a for a in answers if a["has_hallucination"]]
    if not hallucinated:
        return 0.0
    caught = sum(1 for a in hallucinated if a["flagged"])
    return caught / len(hallucinated)
