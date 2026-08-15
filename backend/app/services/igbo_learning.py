"""
Igbo continuous learning service.

Three acquisition paths:
  1. sync_from_seed()     — re-extract from We Speak Igbo seed.ts when it changes
  2. gloss_unverified()   — fill missing glosses in new_words.csv via Perplexity
  3. research_sweep()     — weekly Perplexity search for new vocabulary
  4. learn_word()         — save a word taught directly in conversation

All acquired words land in igbo_learned.json (separate from the seed data).
igbo_knowledge.py loads both files at query time.
"""
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from app.audit import logger as audit

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_LEARNED_PATH = _DATA_DIR / "igbo_learned.json"
_SEED_PATH = Path.home() / "Desktop" / "We Speak Igbo" / "src" / "data" / "seed.ts"
_NEW_WORDS_CSV = Path.home() / "Desktop" / "We Speak Igbo" / "content-review" / "new_words.csv"
_VOCAB_PATH = _DATA_DIR / "igbo_vocabulary.json"

_MAX_GLOSS_PER_RUN = 20   # Perplexity calls per gloss run (rate limit friendly)
_MAX_SWEEP_WORDS = 15     # new words per weekly sweep


# ── Learned store ──────────────────────────────────────────────────────────────

def _load_learned() -> dict:
    if not _LEARNED_PATH.exists():
        return {"items": [], "last_updated": None, "total": 0}
    try:
        return json.loads(_LEARNED_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"items": [], "last_updated": None, "total": 0}


def _save_learned(store: dict) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    store["last_updated"] = datetime.now(timezone.utc).isoformat()
    store["total"] = len(store.get("items", []))
    _LEARNED_PATH.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


def _existing_igbo_words() -> set[str]:
    """All Igbo words already in seed vocab or learned store — used to skip duplicates."""
    known: set[str] = set()
    if _VOCAB_PATH.exists():
        data = json.loads(_VOCAB_PATH.read_text(encoding="utf-8"))
        for lesson in data.get("lessons", []):
            for item in lesson.get("items", []):
                if item.get("igbo"):
                    known.add(item["igbo"].lower().strip())
    learned = _load_learned()
    for item in learned.get("items", []):
        if item.get("igbo"):
            known.add(item["igbo"].lower().strip())
    return known


# ── Path 1: Seed sync ──────────────────────────────────────────────────────────

def sync_from_seed() -> dict:
    """
    Re-extract vocabulary from We Speak Igbo seed.ts.
    Only updates igbo_vocabulary.json if the file has changed since last extraction.
    """
    if not _SEED_PATH.exists():
        return {"status": "skipped", "reason": "seed.ts not found"}

    seed_mtime = _SEED_PATH.stat().st_mtime
    vocab_mtime = _VOCAB_PATH.stat().st_mtime if _VOCAB_PATH.exists() else 0

    if seed_mtime <= vocab_mtime:
        return {"status": "skipped", "reason": "seed.ts unchanged since last extraction"}

    # Re-run extraction
    try:
        raw = _SEED_PATH.read_text(encoding="utf-8")
        start_idx = raw.index("export const LESSONS")
        bracket_start = raw.index("[", start_idx)
        bracket_end = raw.index("\n];", bracket_start)
        lessons_raw = raw[bracket_start + 1:bracket_end]

        def get_str(text, key):
            m = re.search(r"(?<![a-zA-Z_])" + re.escape(key) + r":\s*'((?:[^'\\]|\\.)*)'\s*[,}]", text)
            if m:
                return m.group(1)
            m = re.search(r'(?<![a-zA-Z_])' + re.escape(key) + r':\s*"((?:[^"\\]|\\.)*)"\s*[,}]', text)
            return m.group(1) if m else None

        def get_int(text, key):
            m = re.search(r"(?<![a-zA-Z_])" + re.escape(key) + r":\s*(\d+)", text)
            return int(m.group(1)) if m else None

        def get_tags(text):
            m = re.search(r"tags:\s*\[([^\]]*)\]", text)
            return re.findall(r"'([^']+)'", m.group(1)) if m else []

        lesson_pattern = re.compile(
            r"\{\s*id:\s*'(\w+)',\s*level:\s*'([^']+)',\s*title:\s*'([^']+)',\s*igboTitle:\s*'([^']+)'"
        )
        positions = [(m.start(), m) for m in lesson_pattern.finditer(lessons_raw)]
        lessons = []

        for idx, (start, m) in enumerate(positions):
            end = positions[idx + 1][0] if idx + 1 < len(positions) else len(lessons_raw)
            block = lessons_raw[start:end]
            lesson = {
                "id": m.group(1), "level": m.group(2),
                "title": m.group(3), "igboTitle": m.group(4),
                "grammar": get_str(block, "grammar"),
                "objective": get_str(block, "objective"),
                "items": [],
            }
            im_match = re.search(r"items:\s*\[(.*?)(?:\],\s*\}|\]\s*\},)", block, re.DOTALL)
            if im_match:
                ir = im_match.group(1)
                ip = re.compile(r"\{\s*id:\s*'([^']+)'")
                ipos = [(n.start(), n) for n in ip.finditer(ir)]
                for jdx, (istart, im2) in enumerate(ipos):
                    iend = ipos[jdx + 1][0] if jdx + 1 < len(ipos) else len(ir)
                    ib = ir[istart:iend]
                    item = {
                        "id": im2.group(1),
                        "igbo": get_str(ib, "igbo"),
                        "english": get_str(ib, "english"),
                        "part_of_speech": get_str(ib, "part_of_speech"),
                        "difficulty": get_int(ib, "difficulty"),
                        "tags": get_tags(ib),
                        "example_sentence": get_str(ib, "example_sentence"),
                        "cultural_note": get_str(ib, "cultural_note"),
                        "tone_note": get_str(ib, "tone_note"),
                        "note": get_str(ib, "note"),
                    }
                    lesson["items"].append({k: v for k, v in item.items() if v is not None})
            lessons.append({k: v for k, v in lesson.items() if v is not None})

        total = sum(len(l["items"]) for l in lessons)
        out = {
            "source": "We Speak Igbo — seed.ts (auto-synced)",
            "synced_at": datetime.now(timezone.utc).isoformat(),
            "total_lessons": len(lessons),
            "total_items": total,
            "lessons": lessons,
        }
        _VOCAB_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

        # Invalidate the lru_cache in igbo_knowledge so it reloads
        try:
            from app.services.igbo_knowledge import _load
            _load.cache_clear()
        except Exception:
            pass

        audit.log_event("igbo_seed_synced", {"lessons": len(lessons), "items": total})
        return {"status": "updated", "lessons": len(lessons), "items": total}

    except Exception as exc:
        return {"status": "error", "reason": str(exc)}


# ── Path 2: Gloss unverified words from CSV ────────────────────────────────────

def gloss_unverified(limit: int = _MAX_GLOSS_PER_RUN) -> dict:
    """
    Look up English glosses for words in new_words.csv that are missing them.
    Uses Perplexity to find verified definitions. Saves results to igbo_learned.json.
    """
    if not _NEW_WORDS_CSV.exists():
        return {"status": "skipped", "reason": "new_words.csv not found"}

    import csv
    existing = _existing_igbo_words()
    to_gloss = []

    with open(_NEW_WORDS_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            igbo = row.get("igbo", "").strip()
            english = row.get("english", "").strip()
            if igbo and not english and igbo.lower() not in existing:
                to_gloss.append(igbo)
            if len(to_gloss) >= limit:
                break

    if not to_gloss:
        return {"status": "skipped", "reason": "no unglossed words remaining"}

    from app.services.inference import call_inference

    prompt = (
        f"I need accurate English definitions for these Igbo words. "
        f"For each word, provide: igbo word, English meaning, part of speech (noun/verb/adjective/expression), "
        f"and a short example sentence in Igbo with English translation. "
        f"Only include words you are confident about. Skip any you are uncertain of. "
        f"Return as a JSON array:\n"
        f'[{{"igbo": "word", "english": "meaning", "part_of_speech": "noun", '
        f'"example_sentence": "Igbo sentence — English translation"}}]\n\n'
        f"Words to define: {', '.join(to_gloss)}"
    )

    system = (
        "You are an Igbo language expert. Provide accurate, verified definitions only. "
        "Never guess. If uncertain about a word, omit it from the response. "
        "Use proper Igbo diacritics (ọ, ụ, ị). Return only valid JSON."
    )

    try:
        raw, provider = call_inference(prompt=prompt, system=system, tier="research")
        raw = raw.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        if not m:
            return {"status": "error", "reason": "no JSON array in response"}

        new_items = json.loads(m.group())
        store = _load_learned()
        added = 0
        for item in new_items:
            igbo = item.get("igbo", "").strip()
            if not igbo or not item.get("english") or igbo.lower() in existing:
                continue
            store["items"].append({
                **item,
                "source": "perplexity_gloss",
                "acquired_at": datetime.now(timezone.utc).isoformat(),
            })
            existing.add(igbo.lower())
            added += 1

        _save_learned(store)
        audit.log_event("igbo_glossed", {"added": added, "attempted": len(to_gloss), "provider": provider})
        return {"status": "ok", "added": added, "attempted": len(to_gloss)}

    except Exception as exc:
        return {"status": "error", "reason": str(exc)}


# ── Path 3: Weekly research sweep ─────────────────────────────────────────────

def research_sweep() -> dict:
    """
    Use Perplexity to find new Igbo vocabulary not yet in the knowledge base.
    Runs weekly via scheduler. Targets gaps: verbs, proverbs, cultural terms.
    """
    existing = _existing_igbo_words()
    existing_sample = list(existing)[:30]  # show a sample so the LLM avoids duplicates

    from app.services.inference import call_inference

    focus_areas = [
        "common Igbo verbs used in daily life",
        "Igbo words for emotions and feelings",
        "Igbo proverbs (ilu) with their meanings",
        "Igbo words related to Igbo culture and tradition",
        "Igbo greetings and expressions for different times of day",
    ]
    import random
    focus = random.choice(focus_areas)

    prompt = (
        f"Find {_MAX_SWEEP_WORDS} Igbo vocabulary items focused on: {focus}.\n"
        f"Avoid these words already in our database (partial list): {', '.join(existing_sample[:20])}\n\n"
        f"For each word return: igbo, english, part_of_speech, example_sentence, cultural_note (optional).\n"
        f"Only include words you are confident about with correct Igbo diacritics (ọ, ụ, ị).\n"
        f"Return as a JSON array only:\n"
        f'[{{"igbo": "...", "english": "...", "part_of_speech": "...", '
        f'"example_sentence": "...", "cultural_note": "..."}}]'
    )

    system = (
        "You are an Igbo language researcher. Provide only verified, accurate Igbo vocabulary. "
        "Use correct diacritics. Never fabricate words. If uncertain, omit. Return only valid JSON."
    )

    try:
        raw, provider = call_inference(prompt=prompt, system=system, tier="research")
        raw = raw.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        if not m:
            return {"status": "error", "reason": "no JSON array in response"}

        new_items = json.loads(m.group())
        store = _load_learned()
        added = 0
        for item in new_items:
            igbo = item.get("igbo", "").strip()
            if not igbo or not item.get("english") or igbo.lower() in existing:
                continue
            item.pop("cultural_note", None) if not item.get("cultural_note") else None
            store["items"].append({
                **item,
                "source": f"research_sweep:{focus[:40]}",
                "acquired_at": datetime.now(timezone.utc).isoformat(),
            })
            existing.add(igbo.lower())
            added += 1

        _save_learned(store)
        audit.log_event("igbo_sweep", {"added": added, "focus": focus, "provider": provider})
        return {"status": "ok", "added": added, "focus": focus}

    except Exception as exc:
        return {"status": "error", "reason": str(exc)}


# ── Path 4: Learn from conversation ───────────────────────────────────────────

def learn_word(igbo: str, english: str, part_of_speech: str = "",
               example_sentence: str = "", cultural_note: str = "",
               source: str = "conversation") -> dict:
    """Save a word taught directly in conversation."""
    igbo = igbo.strip()
    english = english.strip()
    if not igbo or not english:
        return {"status": "error", "reason": "igbo and english are required"}

    existing = _existing_igbo_words()
    if igbo.lower() in existing:
        return {"status": "skipped", "reason": f"'{igbo}' already in knowledge base"}

    store = _load_learned()
    entry = {
        "igbo": igbo,
        "english": english,
        "source": source,
        "acquired_at": datetime.now(timezone.utc).isoformat(),
    }
    if part_of_speech:
        entry["part_of_speech"] = part_of_speech
    if example_sentence:
        entry["example_sentence"] = example_sentence
    if cultural_note:
        entry["cultural_note"] = cultural_note

    store["items"].append(entry)
    _save_learned(store)

    try:
        from app.services.igbo_knowledge import _load
        _load.cache_clear()
    except Exception:
        pass

    audit.log_event("igbo_word_learned", {"igbo": igbo, "english": english, "source": source})
    return {"status": "ok", "igbo": igbo, "english": english}


# ── Stats ──────────────────────────────────────────────────────────────────────

def get_stats() -> dict:
    seed_count = 0
    if _VOCAB_PATH.exists():
        data = json.loads(_VOCAB_PATH.read_text(encoding="utf-8"))
        seed_count = data.get("total_items", 0)

    learned = _load_learned()
    learned_count = len(learned.get("items", []))
    by_source: dict[str, int] = {}
    for item in learned.get("items", []):
        src = item.get("source", "unknown").split(":")[0]
        by_source[src] = by_source.get(src, 0) + 1

    return {
        "seed_vocabulary": seed_count,
        "learned_vocabulary": learned_count,
        "total": seed_count + learned_count,
        "by_source": by_source,
        "last_updated": learned.get("last_updated"),
        "seed_path": str(_SEED_PATH),
        "seed_exists": _SEED_PATH.exists(),
        "unglossed_csv_exists": _NEW_WORDS_CSV.exists(),
    }
