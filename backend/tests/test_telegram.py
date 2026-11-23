import json
from pathlib import Path

import pytest

from app.telegram import TelegramExportError, flatten_text, parse_export, select_participants


DEMO = Path(__file__).parents[2] / "frontend" / "public" / "demo.json"


def test_mixed_entities_are_flattened():
    assert flatten_text(["hello ", {"type": "bold", "text": "there"}, "!"]) == "hello there!"


def test_demo_parses_service_and_text_messages():
    chat = parse_export(DEMO.read_bytes())
    assert chat.name == "Mira & Alex — demo"
    assert len(chat.messages) == 47
    assert chat.skipped_messages == 1
    assert "excellent luck" in chat.messages[2].text


@pytest.mark.parametrize("content", [b"", b"not-json", json.dumps({"name": "x"}).encode()])
def test_invalid_files_are_rejected(content):
    with pytest.raises(TelegramExportError):
        parse_export(content)


def test_participant_selection_requires_distinct_existing_people():
    chat = parse_export(DEMO.read_bytes())
    with pytest.raises(TelegramExportError):
        select_participants(chat, ("user1", "user1"))
    with pytest.raises(TelegramExportError):
        select_participants(chat, ("user1", "unknown"))
    assert len(select_participants(chat, ("user1", "user2"))) == 47

