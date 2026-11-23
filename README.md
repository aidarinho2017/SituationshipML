# Situationship AI

[![CI](https://github.com/aidarinho2017/SituationshipML/actions/workflows/ci.yml/badge.svg)](https://github.com/aidarinho2017/SituationshipML/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-pink.svg)](LICENSE)

Situationship AI is a self-hosted Telegram conversation analyzer. It turns a Telegram Desktop JSON export into communication statistics, flirting-signal analysis, evidence-based observations, and a transparent experimental score.

The project is deliberately not a relationship oracle. It measures patterns visible in the messages and never claims to know what either person secretly feels.

## What it includes

- Editorial, responsive Next.js interface with Recharts visualizations
- Telegram JSON validation, entity parsing, participant selection, and demo mode
- Character TF–IDF + Logistic Regression model trained on English and synthetic Russian/Kazakh data
- Batch ML inference and per-participant flirting-signal metrics
- Session initiation, eligible response times, message balance, hourly and weekday activity
- Deterministic Romantic Potential Score with a visible component breakdown
- Optional MongoDB history for metric-only analysis snapshots
- No user accounts, analytics, external LLMs, or paid APIs

## Architecture

```text
Telegram JSON
    │
    ▼
FastAPI parser ── validation + participant filtering
    │
    ├── conversation statistics
    ├── batch scikit-learn inference
    └── deterministic score + insights
    │
    ├── optional metric snapshot ── MongoDB
    ▼
Next.js dashboard ── Recharts visualizations + saved history
```

`POST /api/chat/parse` returns export metadata only. The browser retains the selected file and sends it again to `POST /api/chat/analyze`. The API processes each request in memory and never persists the conversation. Saving is a separate, explicit action that stores the computed result after removing message examples.

## Requirements

- Python 3.11+
- Node.js 20+
- npm

## Local setup

### One-command Docker setup

With Docker Desktop running, start the complete application with:

```bash
docker compose up --build
```

Open [http://localhost:3000](http://localhost:3000). The first build installs dependencies and may take a few minutes; later starts reuse Docker's cache. Stop the application with `Ctrl+C`, followed by:

```bash
docker compose down
```

No local Python or Node.js installation is required for this option. The API is also available at [http://localhost:8000](http://localhost:8000).

MongoDB is available at `mongodb://localhost:27017` for tools such as MongoDB Compass. For this local educational setup, use username `situationship`, password `situationship`, authentication database `admin`, and database `situationship`. These development credentials must not be used for a public deployment.

### Native development setup

```bash
git clone https://github.com/aidarinho2017/SituationshipML.git
cd SituationshipML
make install
```

Start the API:

```bash
make api
```

In another terminal, start the frontend:

```bash
make web
```

Open [http://localhost:3000](http://localhost:3000). Choose **Try demo** to explore the full product without uploading a personal chat.

For saved history during native development, start only MongoDB with `docker compose up -d mongo`, then set:

```bash
export MONGODB_URL='mongodb://situationship:situationship@localhost:27017/?authSource=admin'
export MONGODB_DATABASE='situationship'
```

Without these variables, parsing and analysis still work; history endpoints return `503`.

The repository includes the inference model, so downloading training data or retraining is not required. For manual setup, install `backend/requirements-dev.txt`, run Uvicorn from the repository root, and install the frontend with `npm install` inside `frontend/`.

## Exporting a Telegram chat

In Telegram Desktop:

1. Open **Settings → Advanced → Export Telegram data**.
2. Select personal chats and choose **Machine-readable JSON**.
3. Upload the resulting `result.json` locally in Situationship AI.

The application ignores service events, media-only entries, and records without usable text. For group exports, select exactly two participants before analysis.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Service and model readiness |
| `POST` | `/api/chat/parse` | Validate a JSON upload and preview participants |
| `POST` | `/api/chat/analyze` | Analyze two selected participants |
| `POST` | `/api/analyses` | Save a metric-only snapshot |
| `GET` | `/api/analyses` | List saved snapshots, newest first |
| `GET` | `/api/analyses/{id}` | Reopen a saved snapshot |
| `PATCH` | `/api/analyses/{id}` | Rename a saved snapshot |
| `DELETE` | `/api/analyses/{id}` | Permanently delete a snapshot |

Interactive API documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs) while the backend is running.

## Model

The bundled `public-2.0` artifact uses:

- character-boundary TF–IDF n-grams from 3 to 5 characters;
- minimum document frequency of 2;
- sublinear term frequency;
- Logistic Regression with a fixed random seed.

This representation handles spelling variation, slang, Cyrillic text, and mixtures of the supported training languages without language detection. Messages with fewer than four Unicode letters or digits are treated as insufficient evidence.

The model was trained on the public English dataset, machine-translated Russian/Kazakh examples, and 200 locally reviewed examples. The local messages and annotation files are not distributed. The binary artifact contains character n-gram features and coefficients, not the original rows, so the exact artifact is intentionally not reproducible from this repository alone.

The decision threshold (`0.44`) was selected by maximum F1 on the public validation split. The public test split was used once for final reporting:

| Split | Precision | Recall | F1 |
|---|---:|---:|---:|
| Validation | 69.8% | 77.0% | 73.2% |
| Test — overall | 68.8% | 74.4% | 71.5% |
| Test — English | 70.6% | 78.6% | 74.4% |
| Test — Kazakh | 65.4% | 74.8% | 69.8% |
| Test — Russian | 70.7% | 69.8% | 70.3% |

Classifier scores are pattern scores, not calibrated probabilities of attraction. The data is small, context-free, and partly machine-translated, so the model should be treated as an educational baseline.

### Recreate the public training data

Dataset files are not redistributed because the upstream dataset does not declare redistribution terms. To download and translate them locally:

```bash
.venv/bin/pip install -r requirements.txt
.venv/bin/python download_data.py
.venv/bin/python translate_data.py
```

Source: [ieuniversity/flirty_or_not](https://huggingface.co/datasets/ieuniversity/flirty_or_not). Review its current terms before downloading or redistributing it.

### Train a conservative local model

To adapt the bundled model without saving private messages in MongoDB, create two private review sets from different chats after recreating the public data:

```bash
.venv/bin/python backend/review_model.py /path/to/first/result.json \
  --output data/private/train_review.csv
.venv/bin/python backend/review_model.py /path/to/second/result.json \
  --output data/private/evaluation_review.csv
```

Open both CSV files and fill every `label` with `0` for neutral or `1` for explicitly flirty. Each file needs at least 20 examples of each label. The script samples messages from low, uncertain, and high score ranges; it does not include sender names or dates.

Train the personalized artifact:

```bash
.venv/bin/python backend/train_model.py \
  --train-review data/private/train_review.csv \
  --evaluation data/private/evaluation_review.csv
```

Training chooses the threshold with the best F1 score on the public validation split. It reports the private evaluation separately, then reports precision, recall, F1, and confusion matrices on the untouched public test split.

Use the local artifact natively:

```bash
MODEL_PATH=backend/model/flirting_pipeline.local.joblib make api
```

Or with Docker Compose:

```bash
MODEL_PATH=/workspace/backend/model/flirting_pipeline.local.joblib docker compose up -d api
```

`data/private/` and `*.local.joblib` are gitignored. A local artifact is derived from private examples and should not be published without understanding that its n-gram vocabulary may contain short fragments from those examples.

## Romantic Potential Score

The score is an unvalidated, deterministic index:

| Component | Weight |
|---|---:|
| Mutual flirting signals | 40% |
| Signal reciprocity | 25% |
| Conversation-initiation balance | 20% |
| Engagement and message balance | 15% |

The dashboard withholds the score unless the conversation contains at least 30 classifier-eligible messages, including 10 from each participant. Communication statistics still use all messages. It must not be interpreted as a probability of romantic feelings, consent, compatibility, or a future relationship.

## Privacy and limits

- Uploaded files reach the local FastAPI backend; processing is not browser-only.
- Conversation files and raw messages are never stored in the database.
- An explicit save stores participant names, dates, computed metrics, scores, charts, and insights in MongoDB; classifier-selected message examples are removed first.
- Saved history is shared by everyone who can reach the self-hosted API and remains until manually deleted.
- Message text is not logged by the application.
- The default upload limit is 20 MB and 100,000 message records.
- Example messages returned to the dashboard are limited to four classifier-relevant excerpts.
- Local review CSVs contain message text but remain outside MongoDB and are gitignored; delete them when no longer needed.
- Configure allowed frontend origins and resource limits through `.env.example` values.

Anyone exposing the API beyond localhost is responsible for transport security, access control, and deployment hardening.

MongoDB data survives normal container restarts in the `mongo_data` volume. `docker compose down` keeps it; `docker compose down -v` permanently removes all saved analyses.

## Tests and production build

```bash
make test
make build
```

The tests cover Telegram parsing, mixed text entities, invalid files, participant selection, session and response-time rules, model artifact compatibility, evidence filtering, review validation, threshold selection, score boundaries, MongoDB history, and the end-to-end demo flow.

## Repository layout

```text
backend/             FastAPI application, model export, and tests
frontend/            Next.js application and synthetic demo fixture
data/                instructions and locally generated training data
data/private/        gitignored local review CSVs
data.ipynb           exploratory analysis and baseline experiment
download_data.py     source dataset download
translate_data.py    reproducible Russian/Kazakh augmentation
```

## License

Application code is available under the MIT License. Third-party training data is not distributed by this repository and remains subject to its upstream terms.

