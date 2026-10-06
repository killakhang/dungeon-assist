import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from dungeon_assist.store import Store
from dungeon_assist.dice import roll_expression

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
    print("Dungeon Assist v0.2 ready as", bot.user)

@bot.tree.error
async def tree_error(i, error):
    msg = str(getattr(error, "original", error))
    if i.response.is_done():
        await i.followup.send("Warning: " + msg, ephemeral=True)
    else:
        await i.response.send_message("Warning: " + msg, ephemeral=True)

@bot.tree.command(name="dndhelp", description="Show Dungeon Assist commands")
async def dndhelp(i):
    await i.response.send_message("**Dungeon Assist v0.2**\\n/campaign_setup /character_create /character_show /hp /condition /roll /initiative_add /initiative /initiative_clear /quest_add /quests /scene /note /recap /snapshot")

@bot.tree.command(name="campaign_setup", description="Create or select this server campaign")
async def campaign_setup(i, name: str):
    store.setup_campaign(gid(i), name)
    await i.response.send_message("Campaign **" + name + "** is active.")

@bot.tree.command(name="character_create", description="Create a Level-1 character")
async def character_create(i, name: str, character_class: str, max_hp: int = 10):
    store.create_character(gid(i), i.user.id, name, character_class, max_hp)
    await i.response.send_message("Created **" + name + "**, Level 1 " + character_class + ".")

@bot.tree.command(name="character_show", description="Show a character")
async def character_show(i, name: str):
    c = store.character(gid(i), name)
    await i.response.send_message("**{}** - Level {} {}\\nHP {}/{}\\nConditions: {}".format(c["name"], c["level"], c["class"], c["hp"], c["max_hp"], c["conditions"] or "none"))

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
