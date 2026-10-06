import json
import os
from pathlib import Path

from openai import OpenAI

CHARACTER_DIR = Path(__file__).resolve().parent.parent / "config" / "characters"

def ai_enabled():
    return bool(os.getenv("OPENAI_API_KEY"))

def load_seed(name):
    path = CHARACTER_DIR / (name.lower() + ".json")
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

def ask_ai(prompt, character=None, purpose="D&D assistant"):
    if not ai_enabled():
        raise RuntimeError("AI is not configured. Set OPENAI_API_KEY on EC2.")
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
    client = OpenAI()
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5"),
        instructions=instructions,
        input=prompt,
        store=False,
    )
    return response.output_text.strip()


def plan_action(message, context=None):
    """Translate natural language into one validated Dungeon Assist action."""
    if not ai_enabled():
        raise RuntimeError("AI is not configured. Set OPENAI_API_KEY on EC2.")
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
        "reply": "brief explanation"
    }
    instructions = (
        "You are the action planner for Dungeon Assist. Convert the user's message into exactly one JSON object. "
        "Use only the actions listed in the supplied schema. Never invent dice results. Never choose a destructive reset action. "
        "If the request is ambiguous, informational, roleplay, asks a rules question, or cannot safely map to one action, choose chat. "
        "Do not wrap JSON in markdown. Keep names exactly as the user supplied them."
    )
    client = OpenAI()
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5"),
        instructions=instructions,
        input="Schema:\n"+json.dumps(schema)+"\nContext:\n"+json.dumps(context or {})+"\nUser:\n"+message,
        store=False,
    )
    raw=response.output_text.strip()
    if raw.startswith("```"):
        raw=raw.split("\n",1)[1].rsplit("```",1)[0]
    data=json.loads(raw)
    if not isinstance(data,dict) or "action" not in data:
        raise ValueError("AI returned an invalid action plan.")
    return data
