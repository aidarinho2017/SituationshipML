import argparse
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from sklearn.pipeline import Pipeline

from app.ml import has_minimum_evidence


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_OUTPUT = Path(__file__).parent / "model" / "flirting_pipeline.joblib"
LOCAL_OUTPUT = Path(__file__).parent / "model" / "flirting_pipeline.local.joblib"


def reviewed_rows(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if not {"text", "label"}.issubset(frame.columns):
        raise ValueError(f"{path} must contain text and label columns.")
    if frame[["text", "label"]].isna().any().any():
        raise ValueError(f"Finish every label in {path} before training.")
    frame = frame[["text", "label"]].rename(columns={"text": "texts"})
    frame["texts"] = frame["texts"].astype(str).str.strip()
    frame["label"] = pd.to_numeric(frame["label"], errors="raise").astype(int)
    if not frame["label"].isin([0, 1]).all() or (frame["texts"] == "").any():
        raise ValueError(f"{path} labels must be 0 or 1 and text cannot be blank.")
    frame["key"] = frame["texts"].str.casefold()
    frame = frame.drop_duplicates("key", keep="last")
    counts = frame["label"].value_counts()
    if any(counts.get(label, 0) < 20 for label in (0, 1)):
        raise ValueError(f"{path} needs at least 20 reviewed rows for each label.")
    return frame.drop(columns="key")


def report(name: str, labels, scores, threshold: float, eligible=None) -> None:
    predictions = scores >= threshold
    if eligible is not None:
        predictions &= eligible
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average="binary", zero_division=0
    )
    print(
        f"{name}: precision={precision:.3f} recall={recall:.3f} f1={f1:.3f} "
        f"confusion={confusion_matrix(labels, predictions).tolist()}"
    )


def choose_threshold(labels: np.ndarray, scores: np.ndarray, eligible=None) -> float:
    best = None
    for threshold in np.round(np.arange(0.3, 0.951, 0.01), 2):
        predictions = scores >= threshold
        if eligible is not None:
            predictions &= eligible
        if predictions.sum() < 10:
            continue
        _, _, f1, _ = precision_recall_fscore_support(
            labels, predictions, average="binary", zero_division=0
        )
        if best is None or f1 > best[0]:
            best = (f1, threshold)
    if best is None:
        raise ValueError("No threshold produced at least 10 positive predictions.")
    return round(float(best[1]), 2)


def model_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    min_df=2,
                    sublinear_tf=True,
                ),
            ),
            ("classifier", LogisticRegression(max_iter=1_000, random_state=42)),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the flirting classifier.")
    parser.add_argument("--train-review", type=Path)
    parser.add_argument("--evaluation", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--version")
    args = parser.parse_args()
    if bool(args.train_review) != bool(args.evaluation):
        parser.error("--train-review and --evaluation must be supplied together.")

    train = pd.read_csv(ROOT / "data" / "train.csv")[["texts", "label"]]
    model = model_pipeline()
    if args.train_review:
        review_train = reviewed_rows(args.train_review)
        evaluation = reviewed_rows(args.evaluation)
        train_keys = train["texts"].str.strip().str.casefold()
        review_keys = set(review_train["texts"].str.casefold())
        evaluation_keys = set(evaluation["texts"].str.casefold())
        if review_keys & evaluation_keys:
            raise ValueError("Training and evaluation review files must not contain the same messages.")
        train = pd.concat(
            [train[~train_keys.isin(review_keys)], review_train], ignore_index=True
        )
        model.fit(train["texts"], train["label"])
        evaluation_scores = model.predict_proba(evaluation["texts"])[:, 1]
        minimum_alphanumeric = 4
        evaluation_eligible = np.array(
            [has_minimum_evidence(text, minimum_alphanumeric) for text in evaluation["texts"]]
        )
        version = args.version or datetime.now(timezone.utc).strftime("local-%Y%m%d%H%M%SZ")
        output = args.output or LOCAL_OUTPUT
    else:
        model.fit(train["texts"], train["label"])
        minimum_alphanumeric = 4
        version = args.version or "public-1.0"
        output = args.output or PUBLIC_OUTPUT

    validation = pd.read_csv(ROOT / "data" / "validation.csv")
    validation_scores = model.predict_proba(validation["texts"])[:, 1]
    validation_eligible = np.array(
        [has_minimum_evidence(text, minimum_alphanumeric) for text in validation["texts"]]
    )
    threshold = choose_threshold(
        validation["label"].to_numpy(), validation_scores, validation_eligible
    )
    report(
        "public validation",
        validation["label"],
        validation_scores,
        threshold,
        validation_eligible,
    )
    if args.evaluation:
        report(
            "private evaluation",
            evaluation["label"],
            evaluation_scores,
            threshold,
            evaluation_eligible,
        )

    test = pd.read_csv(ROOT / "data" / "test.csv")
    test_scores = model.predict_proba(test["texts"])[:, 1]
    test_eligible = np.array(
        [has_minimum_evidence(text, minimum_alphanumeric) for text in test["texts"]]
    )
    report("public test", test["label"], test_scores, threshold, test_eligible)
    for language, rows in test.groupby("language"):
        eligible = np.array(
            [has_minimum_evidence(text, minimum_alphanumeric) for text in rows["texts"]]
        )
        report(
            language,
            rows["label"],
            model.predict_proba(rows["texts"])[:, 1],
            threshold,
            eligible,
        )

    artifact = {
        "pipeline": model,
        "version": version,
        "threshold": threshold,
        "minimum_alphanumeric": minimum_alphanumeric,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, output)
    print(f"Saved {version} trained on {len(train):,} rows with threshold {threshold:.2f} to {output}")


if __name__ == "__main__":
    main()
