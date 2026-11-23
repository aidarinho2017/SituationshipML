import numpy as np
import pandas as pd
import pytest

from review_model import build_review
from train_model import choose_threshold, reviewed_rows


def test_review_sampling_deduplicates_and_covers_score_bands():
    texts = [f"message {index}" for index in range(40)] + ["message 0"]
    scores = np.concatenate([np.linspace(0, 0.99, 40), [0.1]])
    review = build_review(texts, scores, 20)
    assert len(review) == 20
    assert review["text"].is_unique
    assert review["label"].eq("").all()
    assert set(pd.cut(review["score"], [0, 0.4, 0.6, 0.8, 1], include_lowest=True).dropna().astype(str))


def test_reviewed_rows_validate_complete_balanced_labels(tmp_path):
    path = tmp_path / "review.csv"
    pd.DataFrame(
        {"text": [f"text {index}" for index in range(40)], "label": [0] * 20 + [1] * 20}
    ).to_csv(path, index=False)
    assert len(reviewed_rows(path)) == 40
    pd.DataFrame({"text": ["unfinished"], "label": [None]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="Finish every label"):
        reviewed_rows(path)


def test_reviewed_rows_keep_the_last_case_insensitive_label(tmp_path):
    path = tmp_path / "review.csv"
    frame = pd.DataFrame(
        {
            "text": [f"neutral {index}" for index in range(21)]
            + [f"flirty {index}" for index in range(20)]
            + ["NEUTRAL 0"],
            "label": [0] * 21 + [1] * 20 + [1],
        }
    )
    frame.to_csv(path, index=False)
    reviewed = reviewed_rows(path)
    assert reviewed.loc[reviewed["texts"] == "NEUTRAL 0", "label"].item() == 1


def test_threshold_maximizes_f1_with_enough_positive_predictions():
    labels = np.array([1] * 10 + [0] * 10)
    scores = np.array([0.9] * 10 + [0.49] * 10)
    assert choose_threshold(labels, scores) == 0.5
    with pytest.raises(ValueError, match="at least 10"):
        choose_threshold(labels, np.full(20, 0.1))
