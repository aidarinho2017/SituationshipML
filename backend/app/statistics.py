from collections import Counter
from datetime import timedelta
from statistics import median

import numpy as np

from .ml import has_minimum_evidence
from .schemas import (
    Dynamics,
    FlirtingAnalysis,
    FlirtingExample,
    MetricByParticipant,
    Overview,
    TimeValue,
)
from .telegram import Message


WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def metric(names: list[str], values: list[float]) -> list[MetricByParticipant]:
    return [MetricByParticipant(participant=name, value=round(float(value), 2)) for name, value in zip(names, values)]


def time_series(messages: list[Message], ids: list[str], period: str) -> list[TimeValue]:
    buckets: dict[str, list[int]] = {}
    for message in messages:
        if period == "day":
            key = message.date.date().isoformat()
        elif period == "month":
            key = message.date.strftime("%Y-%m")
        elif period == "hour":
            key = f"{message.date.hour:02d}:00"
        else:
            key = WEEKDAYS[message.date.weekday()]
        buckets.setdefault(key, [0, 0])
        buckets[key][ids.index(message.sender_id)] += 1
    keys = WEEKDAYS if period == "weekday" else sorted(buckets)
    if period == "hour":
        keys = [f"{hour:02d}:00" for hour in range(24)]
    return [
        TimeValue(
            time=key,
            total=sum(buckets.get(key, [0, 0])),
            participant_a=buckets.get(key, [0, 0])[0],
            participant_b=buckets.get(key, [0, 0])[1],
        )
        for key in keys
    ]


def calculate_statistics(
    messages: list[Message],
    ids: list[str],
    names: list[str],
    session_gap_hours: float,
    response_window_hours: float = 12,
) -> tuple[Overview, Dynamics]:
    counts = Counter(message.sender_id for message in messages)
    lengths = {participant: [] for participant in ids}
    words = Counter()
    for message in messages:
        lengths[message.sender_id].append(len(message.text))
        words[message.sender_id] += len(message.text.split())

    initiations = Counter()
    responses: dict[str, list[float]] = {participant: [] for participant in ids}
    sessions = 0
    previous: Message | None = None
    for message in messages:
        if previous is None or message.date - previous.date > timedelta(hours=session_gap_hours):
            sessions += 1
            initiations[message.sender_id] += 1
        elif message.sender_id != previous.sender_id:
            delay = (message.date - previous.date).total_seconds() / 60
            if delay <= response_window_hours * 60:
                responses[message.sender_id].append(delay)
        previous = message

    total = len(messages)
    count_values = [counts[participant] for participant in ids]
    overview = Overview(
        total_messages=total,
        active_days=len({message.date.date() for message in messages}),
        date_start=messages[0].date,
        date_end=messages[-1].date,
        messages=metric(names, count_values),
        percentages=metric(names, [count / total * 100 for count in count_values]),
        average_length=metric(
            names,
            [np.mean(lengths[participant]) if lengths[participant] else 0 for participant in ids],
        ),
        total_words=metric(names, [words[participant] for participant in ids]),
    )
    dynamics = Dynamics(
        sessions=sessions,
        initiations=metric(names, [initiations[participant] for participant in ids]),
        median_response_minutes=metric(
            names,
            [median(responses[participant]) if responses[participant] else 0 for participant in ids],
        ),
        conversation_balance=round(min(count_values) / max(count_values) * 100, 2),
        messages_per_day=time_series(messages, ids, "day"),
        activity_over_time=time_series(messages, ids, "month"),
        hourly_activity=time_series(messages, ids, "hour"),
        weekday_activity=time_series(messages, ids, "weekday"),
    )
    return overview, dynamics


def calculate_flirting(
    messages: list[Message],
    ids: list[str],
    names: list[str],
    scores: np.ndarray,
    threshold: float = 0.6,
    minimum_alphanumeric: int = 0,
) -> FlirtingAnalysis:
    eligible = np.array(
        [has_minimum_evidence(message.text, minimum_alphanumeric) for message in messages]
    )
    signals = (scores >= threshold) & eligible
    eligible_counts = []
    counts = []
    rates = []
    averages = []
    for participant in ids:
        indexes = [index for index, message in enumerate(messages) if message.sender_id == participant]
        participant_scores = scores[indexes]
        participant_eligible = eligible[indexes]
        participant_signals = signals[indexes]
        eligible_count = int(participant_eligible.sum())
        count = int(participant_signals.sum())
        eligible_counts.append(eligible_count)
        counts.append(count)
        rates.append(count / eligible_count * 100 if eligible_count else 0)
        averages.append(float(participant_scores[participant_eligible].mean()) if eligible_count else 0)

    by_month: dict[str, list[int]] = {}
    for message, signal in zip(messages, signals):
        month = message.date.strftime("%Y-%m")
        by_month.setdefault(month, [0, 0])
        if signal:
            by_month[month][ids.index(message.sender_id)] += 1
    over_time = [
        TimeValue(time=month, total=sum(values), participant_a=values[0], participant_b=values[1])
        for month, values in sorted(by_month.items())
    ]

    ranked = sorted(
        ((float(score), message) for score, message, signal in zip(scores, messages, signals) if signal),
        reverse=True,
        key=lambda item: item[0],
    )
    examples = []
    used = Counter()
    for score, message in ranked:
        name = names[ids.index(message.sender_id)]
        if used[name] >= 2:
            continue
        examples.append(FlirtingExample(participant=name, text=message.text[:240], score=round(score, 3)))
        used[name] += 1
        if len(examples) == 4:
            break
    return FlirtingAnalysis(
        eligible_count=metric(names, eligible_counts),
        signal_count=metric(names, counts),
        signal_rate=metric(names, rates),
        average_score=metric(names, [value * 100 for value in averages]),
        over_time=over_time,
        mutual=all(count >= 2 for count in counts),
        examples=examples,
    )

