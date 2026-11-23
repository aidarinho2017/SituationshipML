from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError

from .config import FRONTEND_ORIGINS, MAX_UPLOAD_BYTES, MODEL_PATH, MONGODB_DATABASE, MONGODB_URL
from .ml import FlirtingClassifier
from .schemas import (
    AnalysisResponse,
    ChatPreview,
    ModelInfo,
    Participant,
    RenameAnalysis,
    SavedAnalysis,
    SavedAnalysisSummary,
)
from .score import build_insights, calculate_score
from .statistics import calculate_flirting, calculate_statistics
from .storage import AnalysisRepository
from .telegram import TelegramExportError, parse_export, select_participants


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.classifier = FlirtingClassifier(MODEL_PATH)
    app.state.analyses = None
    app.state.mongodb = None
    if MONGODB_URL:
        app.state.mongodb = AsyncMongoClient(MONGODB_URL, serverSelectionTimeoutMS=3000)
        await app.state.mongodb.admin.command("ping")
        app.state.analyses = AnalysisRepository(app.state.mongodb[MONGODB_DATABASE]["analyses"])
        await app.state.analyses.create_index()
    yield
    if app.state.mongodb:
        await app.state.mongodb.close()
    app.state.classifier = None


app = FastAPI(title="Situationship AI", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)


async def read_chat(file: UploadFile):
    if file.content_type not in {"application/json", "text/json", "application/octet-stream"}:
        raise HTTPException(415, "Upload a Telegram JSON export.")
    try:
        return parse_export(await file.read(MAX_UPLOAD_BYTES + 1))
    except TelegramExportError as error:
        raise HTTPException(422, str(error)) from error
    finally:
        await file.close()


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "model": "ready",
        "model_version": app.state.classifier.version,
        "database": "ready" if app.state.analyses else "disabled",
    }


def analysis_repository() -> AnalysisRepository:
    if app.state.analyses is None:
        raise HTTPException(503, "Saved history is unavailable because MongoDB is not configured.")
    return app.state.analyses


@app.exception_handler(PyMongoError)
async def database_error(_request, _error):
    return JSONResponse(status_code=503, content={"detail": "Saved history is temporarily unavailable."})


@app.post("/api/chat/parse", response_model=ChatPreview)
async def preview_chat(file: UploadFile = File(...)):
    chat = await read_chat(file)
    counts: dict[str, Participant] = {}
    for message in chat.messages:
        if message.sender_id not in counts:
            counts[message.sender_id] = Participant(id=message.sender_id, name=message.sender_name, messages=0)
        counts[message.sender_id].messages += 1
    participants = sorted(counts.values(), key=lambda item: item.messages, reverse=True)
    return ChatPreview(
        chat_name=chat.name,
        chat_type=chat.chat_type,
        participants=participants,
        text_messages=len(chat.messages),
        skipped_messages=chat.skipped_messages,
        date_start=chat.messages[0].date,
        date_end=chat.messages[-1].date,
    )


@app.post("/api/chat/analyze", response_model=AnalysisResponse)
async def analyze_chat(
    file: UploadFile = File(...),
    participant_a: str = Form(...),
    participant_b: str = Form(...),
    session_gap_hours: float = Form(8, ge=1, le=24),
):
    chat = await read_chat(file)
    try:
        messages = select_participants(chat, (participant_a, participant_b))
    except TelegramExportError as error:
        raise HTTPException(422, str(error)) from error
    ids = [participant_a, participant_b]
    names = [next(message.sender_name for message in messages if message.sender_id == participant) for participant in ids]
    scores = app.state.classifier.predict_scores([message.text for message in messages])
    overview, dynamics = calculate_statistics(messages, ids, names, session_gap_hours)
    flirting = calculate_flirting(
        messages,
        ids,
        names,
        scores,
        app.state.classifier.threshold,
        app.state.classifier.minimum_alphanumeric,
    )
    romantic_score = calculate_score(overview, dynamics, flirting)
    return AnalysisResponse(
        chat_name=chat.name,
        participants=names,
        overview=overview,
        dynamics=dynamics,
        flirting=flirting,
        romantic_score=romantic_score,
        insights=build_insights(overview, dynamics, flirting),
        model=ModelInfo(
            version=app.state.classifier.version,
            threshold=app.state.classifier.threshold,
            minimum_alphanumeric=app.state.classifier.minimum_alphanumeric,
        ),
    )


@app.post("/api/analyses", response_model=SavedAnalysis, status_code=201)
async def save_analysis(
    analysis: AnalysisResponse,
    repository: AnalysisRepository = Depends(analysis_repository),
):
    return await repository.save(analysis)


@app.get("/api/analyses", response_model=list[SavedAnalysisSummary])
async def list_analyses(repository: AnalysisRepository = Depends(analysis_repository)):
    return await repository.list()


@app.get("/api/analyses/{analysis_id}", response_model=SavedAnalysis)
async def get_analysis(analysis_id: str, repository: AnalysisRepository = Depends(analysis_repository)):
    try:
        analysis = await repository.get(analysis_id)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    if analysis is None:
        raise HTTPException(404, "Saved analysis not found.")
    return analysis


@app.patch("/api/analyses/{analysis_id}", response_model=SavedAnalysisSummary)
async def rename_analysis(
    analysis_id: str,
    rename: RenameAnalysis,
    repository: AnalysisRepository = Depends(analysis_repository),
):
    if not rename.title.strip():
        raise HTTPException(422, "Title cannot be blank.")
    try:
        analysis = await repository.rename(analysis_id, rename.title)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    if analysis is None:
        raise HTTPException(404, "Saved analysis not found.")
    return analysis


@app.delete("/api/analyses/{analysis_id}", status_code=204)
async def delete_analysis(
    analysis_id: str,
    repository: AnalysisRepository = Depends(analysis_repository),
):
    try:
        deleted = await repository.delete(analysis_id)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    if not deleted:
        raise HTTPException(404, "Saved analysis not found.")
    return Response(status_code=204)

