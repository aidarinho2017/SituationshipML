from datetime import datetime

from pydantic import BaseModel, Field


class Participant(BaseModel):
    id: str
    name: str
    messages: int


class ChatPreview(BaseModel):
    chat_name: str
    chat_type: str
    participants: list[Participant]
    text_messages: int
    skipped_messages: int
    date_start: datetime | None
    date_end: datetime | None


class MetricByParticipant(BaseModel):
    participant: str
    value: float


class TimeValue(BaseModel):
    time: str
    total: int = 0
    participant_a: int = 0
    participant_b: int = 0


class Overview(BaseModel):
    total_messages: int
    active_days: int
    date_start: datetime
    date_end: datetime
    messages: list[MetricByParticipant]
    percentages: list[MetricByParticipant]
    average_length: list[MetricByParticipant]
    total_words: list[MetricByParticipant]


class Dynamics(BaseModel):
    sessions: int
    initiations: list[MetricByParticipant]
    median_response_minutes: list[MetricByParticipant]
    conversation_balance: float
    messages_per_day: list[TimeValue]
    activity_over_time: list[TimeValue]
    hourly_activity: list[TimeValue]
    weekday_activity: list[TimeValue]


class FlirtingExample(BaseModel):
    participant: str
    text: str
    score: float


class FlirtingAnalysis(BaseModel):
    eligible_count: list[MetricByParticipant] = Field(default_factory=list)
    signal_count: list[MetricByParticipant]
    signal_rate: list[MetricByParticipant]
    average_score: list[MetricByParticipant]
    over_time: list[TimeValue]
    mutual: bool
    examples: list[FlirtingExample]


class ScoreComponent(BaseModel):
    label: str
    value: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)


class RomanticScore(BaseModel):
    score: int | None = Field(default=None, ge=0, le=100)
    sufficient_evidence: bool
    reason: str
    components: list[ScoreComponent]


class ModelInfo(BaseModel):
    version: str = "legacy-1.0"
    threshold: float = 0.6
    minimum_alphanumeric: int = 0


class AnalysisResponse(BaseModel):
    chat_name: str
    participants: list[str]
    overview: Overview
    dynamics: Dynamics
    flirting: FlirtingAnalysis
    romantic_score: RomanticScore
    insights: list[str]
    model: ModelInfo = Field(default_factory=ModelInfo)


class SavedAnalysisSummary(BaseModel):
    id: str
    title: str
    chat_name: str
    participants: list[str]
    score: int | None
    model_version: str = "legacy-1.0"
    created_at: datetime


class SavedAnalysis(BaseModel):
    id: str
    title: str
    created_at: datetime
    analysis: AnalysisResponse


class RenameAnalysis(BaseModel):
    title: str = Field(min_length=1, max_length=120)

