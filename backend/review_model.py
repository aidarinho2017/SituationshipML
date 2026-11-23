import argparse
from pathlib import Path

import pandas as pd

from app.config import MODEL_PATH
from app.ml import FlirtingClassifier
from app.telegram import parse_export


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DATA = ROOT / "data" / "private"
BANDS = ((0, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.01))


def build_review(texts: list[str], scores, limit: int) -> pd.DataFrame:
    candidates = pd.DataFrame({"text": [text.strip() for text in texts], "score": scores}).drop_duplicates("text")
    quota = max(1, limit // len(BANDS))
    samples = []
    for lower, upper in BANDS:
        band = candidates[(candidates["score"] >= lower) & (candidates["score"] < upper)]
        samples.append(band.sample(min(quota, len(band)), random_state=42))
    review = pd.concat(samples).drop_duplicates("text")
    if len(review) < limit:
        remaining = candidates.drop(review.index).sample(
            min(limit - len(review), len(candidates) - len(review)), random_state=42
        )
        review = pd.concat([review, remaining])
    review = review.sort_values("score", ascending=False).head(limit)
    review["score"] = review["score"].round(4)
    review["label"] = ""
    return review


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a private CSV for reviewing classifier labels.")
    parser.add_argument("export", type=Path, help="Telegram result.json export")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=MODEL_PATH)
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()
    output = args.output.resolve()
    if PRIVATE_DATA.resolve() not in output.parents:
        parser.error(f"--output must be inside {PRIVATE_DATA} so private text stays gitignored.")
    if args.limit < 40:
        parser.error("--limit must be at least 40.")

    chat = parse_export(args.export.read_bytes())
    texts = list(dict.fromkeys(message.text.strip() for message in chat.messages))
    classifier = FlirtingClassifier(args.model)
    scores = classifier.predict_scores(texts)
    review = build_review(texts, scores, args.limit)
    output.parent.mkdir(parents=True, exist_ok=True)
    review.to_csv(output, index=False)
    print(f"Wrote {len(review)} private review rows to {output}. Fill every label with 0 or 1.")


if __name__ == "__main__":
    main()
