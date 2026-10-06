import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from dungeon_assist.store import Store
from dungeon_assist.dice import roll_expression
from dungeon_assist.ai import ask_ai, ai_enabled, load_seed

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("Set DISCORD_TOKEN in your environment or .env")

store = Store(os.getenv("DUNGEON_DB", "dungeon_assist.db"))
bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

def gid(i):
    if i.guild_id is None:
        raise app_commands.CheckFailure("Use this inside a Discord server.")
    return i.guild_id

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Dungeon Assist v0.3 ready as", bot.user)

@bot.tree.error
async def tree_error(i, error):
    msg = str(getattr(error, "original", error))
    if i.response.is_done():
        await i.followup.send("Warning: " + msg, ephemeral=True)
    else:
        await i.response.send_message("Warning: " + msg, ephemeral=True)

@bot.tree.command(name="dndhelp", description="Show Dungeon Assist commands")
async def dndhelp(i):
    lines = [
        "**DUNGEON ASSIST v0.3**",
        "**CHARACTER**",
        "/character_create",
        "Create a beginner-friendly Level 1 character.",
        "/character_show",
        "Show the character sheet.",
        "/character_fill",
        "AI explains missing fields and suggests choices.",
        "/character_explain",
        "Explain the sheet like you have never played D&D.",
        "/character_ai",
        "Talk to the AI using that character and persona.",
        "**CAMPAIGN**",
        "/campaign_setup",
        "Create or select the campaign.",
        "/scene",
        "Set the current scene.",
        "/note",
        "Record a campaign event.",
        "/recap",
        "Show recent events.",
        "/snapshot",
        "Save a recovery snapshot.",
        "**PLAY**",
        "/roll",
        "Roll dice.",
        "/hp",
        "Set current HP.",
        "/condition",
        "Add or remove a condition.",
        "/initiative_add",
        "Add a combatant.",
        "/initiative",
        "Show turn order.",
        "/initiative_clear",
        "Clear turn order.",
        "/quest_add",
        "Add a quest.",
        "/quests",
        "Show active quests.",
        "**AI**",
        ("READY" if ai_enabled() else "NOT CONFIGURED"),
        "**EXAMPLES**",
        "/character_create name:Wopples",
        "/character_fill name:Wopples",
        "/character_explain name:Wopples",
        "/character_ai name:Wopples message:What do you do?",
        "/roll expression:1d20+5",
    ]
    await i.response.send_message("\n".join(lines))
@bot.tree.command(name="campaign_setup", description="Create or select this server campaign")
async def campaign_setup(i, name: str):
    store.setup_campaign(gid(i), name)
    await i.response.send_message("Campaign **" + name + "** is active.")

@bot.tree.command(name="character_create", description="Beginner-friendly character creator")
@app_commands.describe(name="Character name", character_class="Class or job; optional", species="Species; optional", max_hp="Maximum hit points")
async def character_create(i, name: str, character_class: str = "Unchosen", species: str = "Unchosen", max_hp: int = 10):
    seed = load_seed(name)
    mech = seed.get("mechanical_seed", {})
    if character_class == "Unchosen":
        character_class = mech.get("class", character_class)
    if species == "Unchosen":
        species = mech.get("species", species)
    max_hp = max(1, max_hp)
    store.create_character(gid(i), i.user.id, name, character_class, max_hp)
    store.save_sheet(gid(i), name, {
        "species": species,
        "background": mech.get("background", "Unchosen"),
        "alignment": mech.get("alignment", "Unchosen"),
        "strength": None, "dexterity": None, "constitution": None,
        "intelligence": None, "wisdom": None, "charisma": None,
        "personality": [], "ideals": [], "bonds": [], "flaws": [],
        "equipment": [], "backstory": ""
    })
    lines = [
        "**CHARACTER CREATED**",
        "**Name:** " + name,
        "**Species:** " + species,
        "**Class:** " + character_class,
        "**Level:** 1",
        "**HP:** " + str(max_hp),
        "You do not need to know D&D yet.",
        "**NEXT**",
        "/character_fill name:" + name,
        "AI helps with the blank parts.",
        "/character_explain name:" + name,
        "AI explains what the sheet means.",
    ]
    await i.response.send_message("\n".join(lines))
@bot.tree.command(name="character_show", description="Show a clean character sheet")
async def character_show(i, name: str):
    s = store.sheet(gid(i), name)
    def val(key):
        v = s.get(key)
        if v is None or v == "" or v == []:
            return "Unchosen"
        if isinstance(v, list):
            return ", ".join(str(x) for x in v) or "Unchosen"
        return str(v)
    lines = [
        "**" + s["name"].upper() + " - CHARACTER SHEET**",
        "**Species:** " + val("species"),
        "**Class:** " + val("class"),
        "**Level:** " + val("level"),
        "**Background:** " + val("background"),
        "**Alignment:** " + val("alignment"),
        "**HP:** " + str(s["hp"]) + "/" + str(s["max_hp"]),
        "**STR:** " + val("strength"),
        "**DEX:** " + val("dexterity"),
        "**CON:** " + val("constitution"),
        "**INT:** " + val("intelligence"),
        "**WIS:** " + val("wisdom"),
        "**CHA:** " + val("charisma"),
        "**Personality:** " + val("personality"),
        "**Ideals:** " + val("ideals"),
        "**Bonds:** " + val("bonds"),
        "**Flaws:** " + val("flaws"),
        "**Equipment:** " + val("equipment"),
        "**Backstory:** " + val("backstory"),
    ]
    await i.response.send_message("\n".join(lines))

@bot.tree.command(name="character_fill", description="AI helps fill missing character-sheet fields")
@app_commands.describe(name="Character name", request="What you want help with")
async def character_fill(i, name: str, request: str = "Find missing fields and suggest simple choices"):
    s = store.sheet(gid(i), name)
    await i.response.defer()
    try:
        prompt = "Current sheet:\n" + str(s) + "\nRequest:\n" + request + "\nGive beginner-friendly suggestions. Do not say they were saved. Put each field on its own line."
        answer = ask_ai(prompt, name, "character creation helper")
        await i.followup.send(answer[:1900])
    except Exception as e:
        await i.followup.send("AI unavailable: " + str(e))

@bot.tree.command(name="character_explain", description="Explain a character sheet for a complete beginner")
async def character_explain(i, name: str):
    s = store.sheet(gid(i), name)
    await i.response.defer()
    try:
        prompt = "Explain this D&D sheet like I have never played D&D before:\n" + str(s) + "\nExplain class, level, HP, STR, DEX, CON, INT, WIS, CHA, alignment, background, personality, ideals, bonds and flaws. Keep each item on its own line."
        await i.followup.send(ask_ai(prompt, name, "beginner character-sheet teacher")[:1900])
    except Exception as e:
        await i.followup.send("AI unavailable: " + str(e))

@bot.tree.command(name="character_ai", description="Ask the AI as or about a character")
@app_commands.describe(name="Character name", message="What is happening or what the character should respond to")
async def character_ai(i, name: str, message: str):
    s = store.sheet(gid(i), name)
    await i.response.defer()
    try:
        prompt = "Current character sheet:\n" + str(s) + "\nUser message:\n" + message + "\nRespond in character when appropriate. Preserve established persona and alignment."
        answer = ask_ai(prompt, name, "character roleplay and D&D assistant")
        store.event(gid(i), "character_ai", name + ": " + message, i.user.id)
        await i.followup.send(answer[:1900])
    except Exception as e:
        await i.followup.send("AI unavailable: " + str(e))
@bot.tree.command(name="hp", description="Set current HP")
async def hp(i, character: str, amount: int):
    c = store.set_hp(gid(i), character, amount)
    await i.response.send_message("**{}**: {}/{} HP".format(c["name"], c["hp"], c["max_hp"]))

@bot.tree.command(name="condition", description="Add or remove a condition")
async def condition(i, character: str, condition: str, remove: bool = False):
    c = store.condition(gid(i), character, condition, remove)
    await i.response.send_message("**{}** conditions: {}".format(c["name"], c["conditions"] or "none"))

@bot.tree.command(name="roll", description="Roll dice such as 1d20+5")
async def roll(i, expression: str):
    r = roll_expression(expression)
    await i.response.send_message("Dice {} -> {} = **{}**".format(expression, r["detail"], r["total"]))

@bot.tree.command(name="initiative_add", description="Add a combatant")
async def initiative_add(i, name: str, total: int):
    store.initiative_add(gid(i), name, total)
    await i.response.send_message("Added **{}** at **{}**.".format(name, total))

@bot.tree.command(name="initiative", description="Show initiative order")
async def initiative(i):
    rows = store.initiative(gid(i))
    msg = "\\n".join("{}. **{}** - {}".format(n+1, x["name"], x["total"]) for n, x in enumerate(rows)) or "No active initiative."
    await i.response.send_message("**Initiative**\\n" + msg)

@bot.tree.command(name="initiative_clear", description="Clear initiative")
async def initiative_clear(i):
    store.initiative_clear(gid(i))
    await i.response.send_message("Initiative cleared.")

@bot.tree.command(name="quest_add", description="Add a campaign quest")
async def quest_add(i, title: str):
    store.quest_add(gid(i), title)
    await i.response.send_message("Added quest: **" + title + "**")

@bot.tree.command(name="quests", description="Show active quests")
async def quests(i):
    q = store.quests(gid(i))
    await i.response.send_message("**Quests**\\n" + ("\\n".join("- " + x for x in q) or "None yet."))

@bot.tree.command(name="scene", description="Set current scene or location")
async def scene(i, description: str):
    store.scene(gid(i), description)
    await i.response.send_message("Scene: **" + description + "**")

@bot.tree.command(name="note", description="Record a campaign event")
async def note(i, text: str):
    store.event(gid(i), "note", text, i.user.id)
    await i.response.send_message("Campaign event recorded.")

@bot.tree.command(name="recap", description="Show recent campaign events")
async def recap(i):
    events = store.recap(gid(i), 10)
    msg = "\\n".join("- " + x["text"] for x in events) or "No campaign events yet."
    await i.response.send_message("**Recent events**\\n" + msg)

@bot.tree.command(name="snapshot", description="Save a recovery snapshot")
async def snapshot(i):
    sid = store.snapshot(gid(i))
    await i.response.send_message("Snapshot saved: " + sid)

bot.run(TOKEN)
