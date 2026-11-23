from datetime import datetime, timezone

from bson import ObjectId
from pymongo import DESCENDING, ReturnDocument

from .schemas import AnalysisResponse, SavedAnalysis, SavedAnalysisSummary


class AnalysisRepository:
    def __init__(self, collection):
        self.collection = collection

    async def create_index(self):
        await self.collection.create_index([("created_at", DESCENDING)])

    @staticmethod
    def object_id(value: str) -> ObjectId:
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid analysis id.")
        return ObjectId(value)

    @staticmethod
    def summary(document: dict) -> SavedAnalysisSummary:
        analysis = document["analysis"]
        return SavedAnalysisSummary(
            id=str(document["_id"]),
            title=document["title"],
            chat_name=analysis["chat_name"],
            participants=analysis["participants"],
            score=analysis["romantic_score"]["score"],
            model_version=analysis.get("model", {}).get("version", "legacy-1.0"),
            created_at=document["created_at"],
        )

    @staticmethod
    def detail(document: dict) -> SavedAnalysis:
        return SavedAnalysis(
            id=str(document["_id"]),
            title=document["title"],
            created_at=document["created_at"],
            analysis=document["analysis"],
        )

    async def save(self, analysis: AnalysisResponse) -> SavedAnalysis:
        stored = analysis.model_copy(deep=True)
        stored.flirting.examples = []
        document = {
            "title": f"{stored.chat_name} — {' & '.join(stored.participants)}",
            "created_at": datetime.now(timezone.utc),
            "analysis": stored.model_dump(mode="python"),
        }
        document["_id"] = (await self.collection.insert_one(document)).inserted_id
        return self.detail(document)

    async def list(self) -> list[SavedAnalysisSummary]:
        cursor = self.collection.find().sort("created_at", DESCENDING)
        return [self.summary(document) async for document in cursor]

    async def get(self, analysis_id: str) -> SavedAnalysis | None:
        document = await self.collection.find_one({"_id": self.object_id(analysis_id)})
        return self.detail(document) if document else None

    async def rename(self, analysis_id: str, title: str) -> SavedAnalysisSummary | None:
        document = await self.collection.find_one_and_update(
            {"_id": self.object_id(analysis_id)},
            {"$set": {"title": title.strip()}},
            return_document=ReturnDocument.AFTER,
        )
        return self.summary(document) if document else None

    async def delete(self, analysis_id: str) -> bool:
        result = await self.collection.delete_one({"_id": self.object_id(analysis_id)})
        return result.deleted_count == 1
