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
