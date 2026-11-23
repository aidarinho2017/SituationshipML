import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .config import MAX_MESSAGES, MAX_UPLOAD_BYTES


class TelegramExportError(ValueError):
    pass


@dataclass(frozen=True)
class Message:
    sender_id: str
    sender_name: str
    date: datetime
    text: str


@dataclass(frozen=True)
class ParsedChat:
    name: str
    chat_type: str
    messages: list[Message]
    skipped_messages: int


def flatten_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if not isinstance(value, list):
        return ""
    parts = []
    for item in value:
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, dict) and isinstance(item.get("text"), str):
            parts.append(item["text"])
    return "".join(parts).strip()


def parse_export(content: bytes) -> ParsedChat:
    if not content:
        raise TelegramExportError("The uploaded file is empty.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise TelegramExportError(
            f"The export exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit."
        )
    try:
        payload = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TelegramExportError("This is not valid UTF-8 Telegram JSON.") from error
    if not isinstance(payload, dict) or not isinstance(payload.get("messages"), list):
        raise TelegramExportError("Expected a Telegram export with a messages array.")
    if len(payload["messages"]) > MAX_MESSAGES:
        raise TelegramExportError(f"Exports are limited to {MAX_MESSAGES:,} messages.")

    messages: list[Message] = []
    skipped = 0
    for raw in payload["messages"]:
        if not isinstance(raw, dict) or raw.get("type") != "message":
            skipped += 1
            continue
        text = flatten_text(raw.get("text"))
        sender = raw.get("from")
        sender_id = raw.get("from_id")
        if not text or not isinstance(sender, str) or sender_id is None:
            skipped += 1
            continue
        try:
            date = datetime.fromisoformat(str(raw["date"]).replace("Z", "+00:00"))
            if date.tzinfo is not None:
                date = date.astimezone(timezone.utc).replace(tzinfo=None)
        except (KeyError, ValueError):
            skipped += 1
            continue
        messages.append(Message(str(sender_id), sender, date, text))

    if not messages:
        raise TelegramExportError("No usable text messages were found.")
    messages.sort(key=lambda message: message.date)
    return ParsedChat(
        name=str(payload.get("name") or "Telegram conversation"),
        chat_type=str(payload.get("type") or "unknown"),
        messages=messages,
        skipped_messages=skipped,
    )


def select_participants(chat: ParsedChat, participant_ids: tuple[str, str]) -> list[Message]:
    if participant_ids[0] == participant_ids[1]:
        raise TelegramExportError("Select two different participants.")
    available = {message.sender_id for message in chat.messages}
    missing = set(participant_ids) - available
    if missing:
        raise TelegramExportError("A selected participant is not present in this export.")
    selected = [message for message in chat.messages if message.sender_id in participant_ids]
    if not selected:
        raise TelegramExportError("No messages remain for the selected participants.")
    return selected

