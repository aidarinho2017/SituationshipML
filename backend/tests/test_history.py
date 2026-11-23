from pathlib import Path
from types import SimpleNamespace

from bson import ObjectId
from fastapi.testclient import TestClient

from app.main import analysis_repository, app
from app.storage import AnalysisRepository


DEMO = Path(__file__).parents[2] / "frontend" / "public" / "demo.json"


class Cursor:
    def __init__(self, documents):
        self.documents = documents

    def sort(self, field, direction):
        self.documents.sort(key=lambda item: item[field], reverse=direction < 0)
        return self

    def __aiter__(self):
        self.iterator = iter(self.documents)
        return self

    async def __anext__(self):
        try:
            return next(self.iterator)
        except StopIteration as error:
            raise StopAsyncIteration from error


class Collection:
    def __init__(self):
        self.documents = []

    async def insert_one(self, document):
        document["_id"] = ObjectId()
        self.documents.append(document.copy())
        return SimpleNamespace(inserted_id=document["_id"])

    def find(self):
        return Cursor([document.copy() for document in self.documents])

    async def find_one(self, query):
        return next((document.copy() for document in self.documents if document["_id"] == query["_id"]), None)

    async def find_one_and_update(self, query, update, return_document):
        for document in self.documents:
            if document["_id"] == query["_id"]:
                document.update(update["$set"])
                return document.copy()
        return None

    async def delete_one(self, query):
        before = len(self.documents)
        self.documents = [document for document in self.documents if document["_id"] != query["_id"]]
        return SimpleNamespace(deleted_count=before - len(self.documents))


def analyze_demo(client):
    with DEMO.open("rb") as file:
        response = client.post(
            "/api/chat/analyze",
            files={"file": ("demo.json", file, "application/json")},
            data={"participant_a": "user1", "participant_b": "user2", "session_gap_hours": 8},
        )
    assert response.status_code == 200
    return response.json()


def test_saved_analysis_crud_strips_message_examples():
    repository = AnalysisRepository(Collection())
    app.dependency_overrides[analysis_repository] = lambda: repository
    try:
        with TestClient(app) as client:
            analysis = analyze_demo(client)
            assert analysis["flirting"]["examples"]

            created = client.post("/api/analyses", json=analysis)
            assert created.status_code == 201
            saved = created.json()
            assert saved["analysis"]["flirting"]["examples"] == []

            listed = client.get("/api/analyses").json()
            assert [item["id"] for item in listed] == [saved["id"]]

            renamed = client.patch(f"/api/analyses/{saved['id']}", json={"title": "  Demo result  "})
            assert renamed.status_code == 200
            assert renamed.json()["title"] == "Demo result"

            reopened = client.get(f"/api/analyses/{saved['id']}")
            assert reopened.json()["analysis"] == saved["analysis"]

            assert client.delete(f"/api/analyses/{saved['id']}").status_code == 204
            assert client.get(f"/api/analyses/{saved['id']}").status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_history_requires_mongodb_configuration():
    with TestClient(app) as client:
        response = client.get("/api/analyses")
    assert response.status_code == 503


def test_history_rejects_invalid_id_and_blank_title():
    app.dependency_overrides[analysis_repository] = lambda: AnalysisRepository(Collection())
    try:
        with TestClient(app) as client:
            assert client.get("/api/analyses/not-an-id").status_code == 422
            assert client.patch(f"/api/analyses/{ObjectId()}", json={"title": "   "}).status_code == 422
    finally:
        app.dependency_overrides.clear()
