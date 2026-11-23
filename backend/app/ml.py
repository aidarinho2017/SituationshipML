from pathlib import Path

import joblib
import numpy as np


def has_minimum_evidence(text: str, minimum_alphanumeric: int) -> bool:
    return sum(character.isalnum() for character in text) >= minimum_alphanumeric


class FlirtingClassifier:
    def __init__(self, model_path: Path):
        if not model_path.is_file():
            raise RuntimeError(
                f"Model not found at {model_path}. Run: python backend/train_model.py"
            )
        artifact = joblib.load(model_path)
        if isinstance(artifact, dict):
            self.pipeline = artifact["pipeline"]
            self.version = artifact["version"]
            self.threshold = float(artifact["threshold"])
            self.minimum_alphanumeric = int(artifact["minimum_alphanumeric"])
        else:
            self.pipeline = artifact
            self.version = "legacy-1.0"
            self.threshold = 0.6
            self.minimum_alphanumeric = 0

    def is_eligible(self, text: str) -> bool:
        return has_minimum_evidence(text, self.minimum_alphanumeric)

    def predict_scores(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.array([], dtype=float)
        return self.pipeline.predict_proba(texts)[:, 1]

