import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = Path(
    os.getenv(
        "MODEL_PATH",
        ROOT / "backend" / "model" / "flirting_pipeline.joblib",
    )
)
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", 20 * 1024 * 1024))
MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", 100_000))
MONGODB_URL = os.getenv("MONGODB_URL")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "situationship")
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]

