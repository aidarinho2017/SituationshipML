from datetime import datetime
from pathlib import Path

import joblib
import numpy as np

from app.ml import FlirtingClassifier
from app.score import calculate_score
from app.statistics import calculate_flirting, calculate_statistics
from app.telegram import Message, parse_export


ROOT = Path(__file__).parents[2]


def test_response_times_exclude_overnight_gaps():
    messages = [
        Message("a", "A", datetime(2025, 1, 1, 10), "hello"),
        Message("b", "B", datetime(2025, 1, 1, 10, 5), "hi"),
        Message("a", "A", datetime(2025, 1, 2, 10), "morning"),
        Message("b", "B", datetime(2025, 1, 2, 10, 10), "hello"),
    ]
    overview, dynamics = calculate_statistics(messages, ["a", "b"], ["A", "B"], 8)
    assert overview.total_messages == 4
    assert dynamics.sessions == 2
    assert [item.value for item in dynamics.median_response_minutes] == [0.0, 7.5]


def test_model_batches_messages_and_score_stays_bounded():
    chat = parse_export((ROOT / "frontend" / "public" / "demo.json").read_bytes())
    model = FlirtingClassifier(ROOT / "backend" / "model" / "flirting_pipeline.joblib")
    scores = model.predict_scores([message.text for message in chat.messages])
    assert len(scores) == len(chat.messages)
    assert ((scores >= 0) & (scores <= 1)).all()
    ids, names = ["user1", "user2"], ["Mira", "Alex"]
    overview, dynamics = calculate_statistics(chat.messages, ids, names, 8)
    flirting = calculate_flirting(chat.messages, ids, names, scores)
    result = calculate_score(overview, dynamics, flirting)
    assert result.sufficient_evidence
    assert 0 <= result.score <= 100


def test_insufficient_evidence_has_no_score():
    messages = [
        Message("a", "A", datetime(2025, 1, 1, 10), "hello"),
        Message("b", "B", datetime(2025, 1, 1, 10, 5), "hi"),
    ]
    overview, dynamics = calculate_statistics(messages, ["a", "b"], ["A", "B"], 8)
    flirting = calculate_flirting(messages, ["a", "b"], ["A", "B"], __import__("numpy").array([0.2, 0.3]))
    result = calculate_score(overview, dynamics, flirting)
    assert result.score is None
    assert not result.sufficient_evidence


def test_short_messages_are_excluded_from_flirting_metrics():
    messages = [
        Message("a", "A", datetime(2025, 1, 1, 10), ";)"),
        Message("a", "A", datetime(2025, 1, 1, 10, 1), "kiss me"),
        Message("b", "B", datetime(2025, 1, 1, 10, 2), "сен"),
        Message("b", "B", datetime(2025, 1, 1, 10, 3), "hello there"),
    ]
    flirting = calculate_flirting(
        messages, ["a", "b"], ["A", "B"], np.array([0.99, 0.8, 0.99, 0.8]), 0.75, 4
    )
    assert [item.value for item in flirting.eligible_count] == [1, 1]
    assert [item.value for item in flirting.signal_count] == [1, 1]
    assert [example.text for example in flirting.examples] == ["kiss me", "hello there"]


def test_short_messages_do_not_satisfy_score_evidence():
    messages = [
        Message(str(index % 2), "A" if index % 2 == 0 else "B", datetime(2025, 1, 1, 10, index), "ok")
        for index in range(40)
    ]
    ids, names = ["0", "1"], ["A", "B"]
    overview, dynamics = calculate_statistics(messages, ids, names, 8)
    flirting = calculate_flirting(messages, ids, names, np.full(40, 0.99), 0.75, 4)
    result = calculate_score(overview, dynamics, flirting)
    assert not result.sufficient_evidence
    assert result.score is None


def test_classifier_loads_versioned_and_legacy_artifacts(tmp_path):
    bundled = FlirtingClassifier(ROOT / "backend" / "model" / "flirting_pipeline.joblib")
    legacy_path = tmp_path / "legacy.joblib"
    joblib.dump(bundled.pipeline, legacy_path)
    legacy = FlirtingClassifier(legacy_path)
    assert legacy.version == "legacy-1.0"
    artifact = tmp_path / "model.joblib"
    joblib.dump(
        {
            "pipeline": legacy.pipeline,
            "version": "local-test",
            "threshold": 0.77,
            "minimum_alphanumeric": 4,
        },
        artifact,
    )
    versioned = FlirtingClassifier(artifact)
    assert (versioned.version, versioned.threshold, versioned.minimum_alphanumeric) == (
        "local-test",
        0.77,
        4,
    )

