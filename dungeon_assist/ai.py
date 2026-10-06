import json
import os
from pathlib import Path

from openai import OpenAI

CHARACTER_DIR = Path(__file__).resolve().parent.parent / "config" / "characters"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def ai_enabled():
    return bool(os.getenv("OPENROUTER_API_KEY"))


def _client():
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("AI is not configured. Set OPENROUTER_API_KEY.")
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=key)


def _model():
    return os.getenv("OPENROUTER_MODEL", "openrouter/free")


def _chat(instructions, prompt):
    response = _client().chat.completions.create(
        model=_model(),
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": prompt},
        ],
    )
    text = response.choices[0].message.content
    if not text:
        raise RuntimeError("OpenRouter returned an empty response.")
    return text.strip()


def load_seed(name):
    path = CHARACTER_DIR / (name.lower() + ".json")
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def ask_ai(prompt, character=None, purpose="D&D assistant"):
    if not ai_enabled():
        raise RuntimeError("AI is not configured. Set OPENROUTER_API_KEY.")
    seed = load_seed(character) if character else {}
    instructions = (
        "You are Dungeon Assist, a beginner-friendly D&D assistant. "
        "Explain unfamiliar terms in plain English. Keep Discord output clean and vertical, "
        "with one item per line and no unnecessary blank lines. Never invent dice results. "
        "When roleplaying a character, honor the supplied character configuration and current sheet. "
        "Purpose: " + purpose
    )
    if seed:
        instructions += "\nCharacter configuration:\n" + json.dumps(seed, indent=2)
    return _chat(instructions, prompt)


def plan_action(message, context=None):
    """Translate natural language into one validated Dungeon Assist action."""
    if not ai_enabled():
        raise RuntimeError("AI is not configured. Set OPENROUTER_API_KEY.")
    schema = {
        "action": "chat|damage|heal|temp_hp|set_hp|condition_add|condition_remove|sheet_edit|initiative_add|combat_begin|combat_next|combat_prev|combat_status|combat_end|scene|note|quest_add|lore_add|relationship",
        "character": "string or null",
        "target": "string or null",
        "field": "string or null",
        "value": "string, number, boolean, or null",
        "amount": "integer or null",
        "metric": "affinity|trust|fear|resentment|null",
        "text": "string or null",
        "initiative": "integer or null",
        "secret": "boolean",
        "reply": "brief explanation",
    }
    instructions = (
        "You are the action planner for Dungeon Assist. Convert the user's message into exactly one JSON object. "
        "Use only the actions listed in the supplied schema. Never invent dice results. Never choose a destructive reset action. "
        "If the request is ambiguous, informational, roleplay, asks a rules question, or cannot safely map to one action, choose chat. "
        "Do not wrap JSON in markdown. Keep names exactly as the user supplied them."
    )
    raw = _chat(
        instructions,
        "Schema:\n" + json.dumps(schema) + "\nContext:\n" + json.dumps(context or {}) + "\nUser:\n" + message,
    )
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    data = json.loads(raw)
    if not isinstance(data, dict) or "action" not in data:
        raise ValueError("AI returned an invalid action plan.")
    return data
