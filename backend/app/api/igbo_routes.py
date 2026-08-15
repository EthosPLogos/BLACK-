"""
Igbo language management endpoints.

GET  /api/igbo/stats          — knowledge base stats (seed + learned counts)
POST /api/igbo/learn          — teach Mr. Black a word from conversation
POST /api/igbo/sync           — re-sync from We Speak Igbo seed.ts
POST /api/igbo/gloss          — fill missing glosses from new_words.csv
POST /api/igbo/sweep          — run a research sweep for new vocabulary
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/igbo", tags=["Igbo Learning"])


class LearnWordRequest(BaseModel):
    igbo: str
    english: str
    part_of_speech: str = ""
    example_sentence: str = ""
    cultural_note: str = ""


@router.get("/stats")
def igbo_stats():
    from app.services.igbo_learning import get_stats
    return get_stats()


@router.post("/learn")
def igbo_learn(request: LearnWordRequest):
    from app.services.igbo_learning import learn_word
    return learn_word(
        igbo=request.igbo,
        english=request.english,
        part_of_speech=request.part_of_speech,
        example_sentence=request.example_sentence,
        cultural_note=request.cultural_note,
        source="conversation",
    )


@router.post("/sync")
def igbo_sync():
    from app.services.igbo_learning import sync_from_seed
    return sync_from_seed()


@router.post("/gloss")
def igbo_gloss():
    from app.services.igbo_learning import gloss_unverified
    return gloss_unverified()


@router.post("/sweep")
def igbo_sweep():
    from app.services.igbo_learning import research_sweep
    return research_sweep()
