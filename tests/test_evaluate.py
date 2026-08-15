from src.evaluate import answer_level_catch_rate, precision_recall


def test_precision_recall_basic():
    predicted = [True, True, False, False]
    true = [True, False, True, False]
    result = precision_recall(predicted, true)
    assert result["tp"] == 1
    assert result["fp"] == 1
    assert result["fn"] == 1
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5


def test_precision_recall_no_predictions():
    result = precision_recall([False, False], [True, False])
    assert result["precision"] == 0.0
    assert result["recall"] == 0.0


def test_answer_level_catch_rate():
    answers = [
        {"has_hallucination": True, "flagged": True},
        {"has_hallucination": True, "flagged": False},
        {"has_hallucination": False, "flagged": False},
    ]
    assert answer_level_catch_rate(answers) == 0.5


def test_answer_level_catch_rate_no_hallucinations():
    answers = [{"has_hallucination": False, "flagged": False}]
    assert answer_level_catch_rate(answers) == 0.0
