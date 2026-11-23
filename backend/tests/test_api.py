from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


DEMO = Path(__file__).parents[2] / "frontend" / "public" / "demo.json"


def test_demo_uses_real_parse_and_analysis_endpoints():
    with TestClient(app) as client:
        with DEMO.open("rb") as file:
            preview = client.post("/api/chat/parse", files={"file": ("demo.json", file, "application/json")})
        assert preview.status_code == 200
        assert len(preview.json()["participants"]) == 2
        with DEMO.open("rb") as file:
            analysis = client.post(
                "/api/chat/analyze",
                files={"file": ("demo.json", file, "application/json")},
                data={"participant_a": "user1", "participant_b": "user2", "session_gap_hours": 8},
            )
        assert analysis.status_code == 200
        body = analysis.json()
        assert body["overview"]["total_messages"] == 47
        assert body["romantic_score"]["score"] is not None

