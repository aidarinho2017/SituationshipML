from .schemas import Dynamics, FlirtingAnalysis, Overview, RomanticScore, ScoreComponent


def clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def calculate_score(
    overview: Overview, dynamics: Dynamics, flirting: FlirtingAnalysis
) -> RomanticScore:
    message_counts = [item.value for item in flirting.eligible_count] or [item.value for item in overview.messages]
    signal_counts = [item.value for item in flirting.signal_count]
    if min(message_counts) < 10 or sum(message_counts) < 30:
        return RomanticScore(
            sufficient_evidence=False,
            reason="At least 30 eligible messages, including 10 from each participant, are needed.",
            components=[],
        )

    rates = [item.value for item in flirting.signal_rate]
    mutual_flirting = clamp(min(rates) * 5)
    reciprocity = 100 if max(signal_counts) == 0 else clamp(min(signal_counts) / max(signal_counts) * 100)
    initiation_values = [item.value for item in dynamics.initiations]
    initiation_balance = 100 if max(initiation_values) == 0 else clamp(min(initiation_values) / max(initiation_values) * 100)
    engagement = clamp((dynamics.conversation_balance + min(overview.active_days * 5, 100)) / 2)
    components = [
        ScoreComponent(label="Mutual signals", value=mutual_flirting, weight=0.4),
        ScoreComponent(label="Signal reciprocity", value=reciprocity, weight=0.25),
        ScoreComponent(label="Initiation balance", value=initiation_balance, weight=0.2),
        ScoreComponent(label="Engagement", value=engagement, weight=0.15),
    ]
    score = round(sum(component.value * component.weight for component in components))
    return RomanticScore(
        score=score,
        sufficient_evidence=True,
        reason="A transparent heuristic based on observed chat behavior—not a probability of romantic interest.",
        components=components,
    )


def build_insights(
    overview: Overview, dynamics: Dynamics, flirting: FlirtingAnalysis
) -> list[str]:
    names = [item.participant for item in overview.messages]
    insights = []
    if flirting.mutual:
        insights.append("Both participants show repeated flirting signals in the analyzed messages.")
    initiations = [item.value for item in dynamics.initiations]
    if max(initiations) >= max(2, min(initiations) * 1.25):
        insights.append(f"{names[initiations.index(max(initiations))]} initiates conversation sessions more frequently.")
    lengths = [item.value for item in overview.average_length]
    if max(lengths) >= min(lengths) * 1.2:
        insights.append(f"{names[lengths.index(max(lengths))]} tends to send longer messages.")
    activity = dynamics.messages_per_day
    if len(activity) >= 14:
        first = sum(day.total for day in activity[:7])
        last = sum(day.total for day in activity[-7:])
        if last > first * 1.2:
            insights.append("Message activity is higher in the final seven active dates than in the first seven.")
    if dynamics.conversation_balance >= 80:
        insights.append("Message volume is balanced between both participants.")
    if not insights:
        insights.append("The observed patterns are mixed; no single interaction pattern dominates this chat.")
    return insights[:4]

