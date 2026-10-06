import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("Set DISCORD_TOKEN in your environment or .env")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Dungeon Assist ready as {bot.user}")

@bot.tree.command(name="dndhelp", description="Show Dungeon Assist help")
async def dndhelp(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Dungeon Assist v0.1 — campaign setup, characters, proxy modes, scans, snapshots, and safe reset foundations."
    )

bot.run(TOKEN)
