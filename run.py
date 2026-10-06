import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from dungeon_assist.store import Store
from dungeon_assist.dice import roll_expression, d20, ability_modifier
from dungeon_assist.ai import ask_ai, ai_enabled, load_seed, plan_action

load_dotenv()
VERSION = "0.6.0"
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
    print("Dungeon Assist v" + VERSION + " ready as", bot.user)

@bot.tree.error
async def tree_error(i, error):
    msg = str(getattr(error, "original", error))
    if i.response.is_done():
        await i.followup.send("Warning: " + msg, ephemeral=True)
    else:
        await i.response.send_message("Warning: " + msg, ephemeral=True)

@bot.tree.command(name="dndhelp", description="Show every Dungeon Assist command")
async def dndhelp(i):
    items=[
        ("SYSTEM","/ai","Tell Dungeon Assist what you want in normal language."),
        ("","/version","Show the running Dungeon Assist version."),
        ("CHARACTERS","/character_create","Create a character."),
        ("","/character_show","Show a character sheet."),
        ("","/character_edit","Edit a sheet field."),
        ("","/character_fill","AI suggests missing sheet information."),
        ("","/character_explain","Explain the sheet for a beginner."),
        ("","/character_ai","Use the character AI with memory and knowledge."),
        ("","/character_build","AI walks you through missing character fields."),
        ("","/remember","Give a character a persistent memory."),
        ("","/memories","Show what a character remembers."),
        ("","/knowledge_add","Teach a character campaign knowledge."),
        ("","/knows","Show what a character knows."),
        ("","/portrait","Set a character portrait."),
        ("","/proxy","Roleplay as a character."),
        ("ROLLS","/roll","Roll dice."),
        ("","/check","Roll a character skill check."),
        ("","/save","Roll a saving throw."),
        ("","/attack","Roll an attack against AC and damage."),
        ("COMBAT","/hp","Set HP."),
        ("","/damage","Apply damage."),
        ("","/heal","Restore HP."),
        ("","/temp_hp","Set temporary HP."),
        ("","/condition","Add or remove a condition."),
        ("","/initiative_add","Add initiative."),
        ("","/initiative","Show initiative."),
        ("","/initiative_clear","Clear initiative."),
        ("","/combat_begin","Start combat."),
        ("","/combat_next","Advance one turn."),
        ("","/combat_prev","Go back one turn."),
        ("","/combat_status","Show round and active turn."),
        ("","/combat_end","End combat."),
        ("WORLD","/scene","Set the current scene."),
        ("","/quest_add","Add a quest."),
        ("","/quests","Show quests."),
        ("","/lore_add","Save campaign lore."),
        ("","/lore","Read campaign lore."),
        ("","/rule","Ask a D&D rules question."),
        ("","/world","Ask/develop campaign world information."),
        ("","/relationship","Set affinity, trust, fear, or resentment."),
        ("","/relationships","Show relationship state."),
        ("CAMPAIGN","/campaign_setup","Create/select campaign."),
        ("","/note","Record a campaign event."),
        ("","/recap","Show recent campaign events."),
        ("","/snapshot","Create a recovery snapshot."),
        ("","/reset_campaign","Reset campaign state with RESET confirmation."),
    ]
    e=discord.Embed(title="🏰 Dungeon Assist v" + VERSION,description="AI: "+("READY" if ai_enabled() else "NOT CONFIGURED"))
    text=[]
    for section,cmd,desc in items:
        if section: text.append("**"+section+"**")
        text.append("**"+cmd+"**")
        text.append(desc)
    chunks=[]; current=""
    for line in text:
        if len(current)+len(line)+1>1000: chunks.append(current); current=""
        current+=line+"\n"
    if current: chunks.append(current)
    for n,ch in enumerate(chunks): e.add_field(name="Commands" if n==0 else "Continued",value=ch,inline=False)
    e.set_footer(text="Every command is printed vertically.")
    await i.response.send_message(embed=e)

@bot.tree.command(name="ai", description="Tell Dungeon Assist what you want in normal language")
@app_commands.describe(message="Example: Wopples takes 7 damage")
async def ai_command(i, message: str):
    g=gid(i)
    await i.response.defer()
    try:
        context={
            "characters":[x["name"] for x in store.db.execute("SELECT name FROM characters WHERE guild=?",(g,))],
            "combat":store.combat_state(g),
            "initiative":store.initiative(g)
        }
        p=plan_action(message,context)
        a=p.get("action","chat")
        name=p.get("character")
        if a=="damage":
            r=store.set_hp_delta(g,name,-abs(int(p.get("amount") or 0))); out="💥 **"+r["name"]+"**\nHP "+str(r["hp"])+"/"+str(r["max_hp"])
        elif a=="heal":
            r=store.set_hp_delta(g,name,abs(int(p.get("amount") or 0))); out="💚 **"+r["name"]+"**\nHP "+str(r["hp"])+"/"+str(r["max_hp"])
        elif a=="temp_hp":
            r=store.set_temp_hp(g,name,int(p.get("amount") or 0)); out="🛡️ **"+name+"**\nTemporary HP "+str(r.get("temp_hp",0))
        elif a=="set_hp":
            r=store.set_hp(g,name,int(p.get("amount") or 0)); out="**"+r["name"]+"**\nHP "+str(r["hp"])+"/"+str(r["max_hp"])
        elif a in {"condition_add","condition_remove"}:
            r=store.condition(g,name,str(p.get("text") or p.get("value") or ""),a=="condition_remove"); out="**"+r["name"]+"** conditions\n"+(r["conditions"] or "none")
        elif a=="sheet_edit":
            field=str(p.get("field") or "").lower()
            allowed={"species","background","alignment","strength","dexterity","constitution","intelligence","wisdom","charisma","armor_class","speed","personality","ideals","bonds","flaws","equipment","backstory","portrait_url","ruleset","age","height","weight","eyes","skin","hair","appearance","spellcasting_class","spellcasting_ability"}
            if field not in allowed: raise ValueError("AI requested an unsupported sheet field.")
            r=store.patch_sheet(g,name,{field:p.get("value")}); out="✏️ **"+name+"**\n"+field.replace("_"," ").title()+" → "+str(p.get("value"))
        elif a=="initiative_add":
            store.initiative_add(g,name,int(p.get("initiative") or p.get("value") or 0)); out="⚔️ Added **"+name+"** to initiative."
        elif a=="combat_begin":
            store.combat_begin(g); out="⚔️ Combat started."
        elif a=="combat_next":
            r=store.combat_next(g); out="⚔️ **Round "+str(r["round"])+"**\nTurn: **"+r["combatant"]["name"]+"**"
        elif a=="combat_prev":
            r=store.combat_next(g,True); out="⚔️ **Round "+str(r["round"])+"**\nTurn: **"+r["combatant"]["name"]+"**"
        elif a=="combat_status":
            s=store.combat_state(g); rows=store.initiative(g); out="⚔️ **Round "+str(s["round"])+"**\n"+"\n".join(("➡️ " if s["active"] and n==s["turn"] else "")+x["name"] for n,x in enumerate(rows))
        elif a=="combat_end":
            store.combat_end(g); out="Combat ended."
        elif a=="scene":
            store.scene(g,str(p.get("text") or p.get("value") or "")); out="🎭 Scene updated."
        elif a=="note":
            store.event(g,"note",str(p.get("text") or message),i.user.id); out="📝 Campaign event recorded."
        elif a=="quest_add":
            store.quest_add(g,str(p.get("text") or p.get("value") or "")); out="📜 Quest added."
        elif a=="lore_add":
            key=str(p.get("target") or p.get("field") or "Lore"); store.lore_set(g,key,str(p.get("text") or p.get("value") or ""),bool(p.get("secret",False))); out="📚 Lore saved: **"+key+"**"
        elif a=="relationship":
            r=store.relationship_set(g,name,str(p.get("target")),str(p.get("metric")),int(p.get("value") or 0)); out="❤️ **"+name+" → "+str(p.get("target"))+"**\n"+str(p.get("metric")).title()+" "+str(r[str(p.get("metric"))])
        else:
            out=ask_ai(message,purpose="Dungeon Assist conversational interface")
        if a!="chat": store.event(g,"ai_action",message+" => "+a,i.user.id)
        await i.followup.send(out[:1900])
    except Exception as e:
        await i.followup.send("I couldn't safely do that.\n"+str(e))

@bot.tree.command(name="version", description="Show the running Dungeon Assist version")
async def version(i):
    e=discord.Embed(title="Dungeon Assist", description="**Version**\n"+VERSION+"\n**AI**\n"+("READY" if ai_enabled() else "NOT CONFIGURED"))
    e.set_footer(text="Use /dndhelp to see commands.")
    await i.response.send_message(embed=e)

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
        "ruleset": "2014_5e",
        "species": species,
        "background": mech.get("background", "Unchosen"),
        "alignment": mech.get("alignment", "Unchosen"),
        "experience_points": 0,
        "inspiration": False,
        "strength": None, "dexterity": None, "constitution": None,
        "intelligence": None, "wisdom": None, "charisma": None,
        "armor_class": None, "initiative_bonus": None, "speed": None,
        "temp_hp": 0, "hit_dice": "", "death_save_successes": 0, "death_save_failures": 0,
        "save_proficiencies": [], "skill_proficiencies": [], "passive_perception": None,
        "attacks": [], "equipment": [], "currency": {"cp":0,"sp":0,"ep":0,"gp":0,"pp":0},
        "proficiencies_languages": [], "features_traits": [],
        "personality": [], "ideals": [], "bonds": [], "flaws": [],
        "age": "", "height": "", "weight": "", "eyes": "", "skin": "", "hair": "",
        "appearance": "", "backstory": "", "allies_organizations": [], "treasure": [],
        "spellcasting_class": "", "spellcasting_ability": "", "spell_save_dc": None,
        "spell_attack_bonus": None, "cantrips": [], "spells": {}, "spell_slots": {},
        "portrait_url": ""
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

@bot.tree.command(name="character_build", description="AI walks you through completing a character")
async def character_build(i, name: str, answer: str=""):
    s=store.sheet(gid(i),name)
    fields=["species","class","background","alignment","strength","dexterity","constitution","intelligence","wisdom","charisma","armor_class","speed","personality","ideals","bonds","flaws","equipment","backstory"]
    missing=[f for f in fields if s.get(f) in (None,"",[],"Unchosen")]
    await i.response.defer()
    if not missing:
        await i.followup.send("✅ **"+name+"**\nCore character fields are filled.\nUse /character_show to review."); return
    prompt="You are a beginner D&D character creation wizard. Current sheet: "+str(s)+"\nMissing fields: "+str(missing)+"\nUser's latest answer: "+answer+"\nAsk exactly ONE simple question that helps choose the next missing field. Explain unfamiliar choices briefly. Do not claim anything was saved."
    await i.followup.send(ask_ai(prompt,name,"one-question-at-a-time character builder")[:1900])

@bot.tree.command(name="remember", description="Give a character a persistent memory")
async def remember(i, character: str, memory: str, importance: int=50):
    store.memory_add(gid(i),character,memory,"memory",importance)
    await i.response.send_message("🧠 **"+character+" remembers**\n"+memory)

@bot.tree.command(name="memories", description="Show a character's persistent memories")
async def memories(i, character: str):
    rows=store.memories(gid(i),character,20)
    text="\n".join("🧠 "+x["text"]+" • "+str(x["importance"]) for x in rows) or "No stored memories."
    await i.response.send_message("**"+character+" • MEMORIES**\n"+text[:1800])

@bot.tree.command(name="knowledge_add", description="Teach a character a campaign fact")
async def knowledge_add(i, character: str, topic: str, fact: str):
    store.knowledge_set(gid(i),character,topic,fact,"campaign")
    await i.response.send_message("📚 **"+character+" learned**\n"+topic+"\n"+fact)

@bot.tree.command(name="knows", description="Show what a character knows")
async def knows(i, character: str):
    rows=store.knowledge(gid(i),character)
    text="\n".join("📖 **"+x["key"]+"**\n"+x["text"] for x in rows) or "No character-specific knowledge stored."
    await i.response.send_message(("**"+character+" • KNOWLEDGE**\n"+text)[:1900])

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
        ctx=store.character_context(gid(i),name)\n        prompt = "Character context including sheet, memories, knowledge, and relationships:\n" + str(ctx) + "\nUser message:\n" + message + "\nRespond in character when appropriate. Never let the character know campaign facts absent from their supplied knowledge/memories unless the user just told them in this message. Preserve established persona and alignment."
        answer = ask_ai(prompt, name, "character roleplay and D&D assistant")
        store.event(gid(i), "character_ai", name + ": " + message, i.user.id)
        await i.followup.send(answer[:1900])
    except Exception as e:
        await i.followup.send("AI unavailable: " + str(e))
def sheet_embed(s):
    e=discord.Embed(title=s["name"], description=str(s.get("species","Unchosen"))+" • "+str(s.get("class","Unchosen"))+" "+str(s.get("level",1)))
    if s.get("portrait_url"): e.set_thumbnail(url=s["portrait_url"])
    e.add_field(name="HP",value=str(s["hp"])+"/"+str(s["max_hp"])+"  Temp "+str(s.get("temp_hp",0)),inline=True)
    e.add_field(name="AC",value=str(s.get("armor_class","—")),inline=True)
    e.add_field(name="Speed",value=str(s.get("speed","—")),inline=True)
    stats=[]
    for key,label in [("strength","STR"),("dexterity","DEX"),("constitution","CON"),("intelligence","INT"),("wisdom","WIS"),("charisma","CHA")]:
        stats.append(label+" "+str(s.get(key) if s.get(key) is not None else "—"))
    e.add_field(name="Abilities",value="\n".join(stats),inline=False)
    e.set_footer(text="Dungeon Assist • character sheet")
    return e

SKILLS={"acrobatics":"dexterity","animal_handling":"wisdom","arcana":"intelligence","athletics":"strength","deception":"charisma","history":"intelligence","insight":"wisdom","intimidation":"charisma","investigation":"intelligence","medicine":"wisdom","nature":"intelligence","perception":"wisdom","performance":"charisma","persuasion":"charisma","religion":"intelligence","sleight_of_hand":"dexterity","stealth":"dexterity","survival":"wisdom"}

@bot.tree.command(name="character_edit", description="Set a character-sheet field")
async def character_edit(i, name: str, field: str, value: str):
    allowed={"species","background","alignment","strength","dexterity","constitution","intelligence","wisdom","charisma","armor_class","speed","personality","ideals","bonds","flaws","equipment","backstory","portrait_url","ruleset"}
    field=field.lower()
    if field not in allowed: raise ValueError("Unsupported field. Use /character_show to see the sheet.")
    if field in {"strength","dexterity","constitution","intelligence","wisdom","charisma","armor_class","speed"}: value=int(value)
    s=store.patch_sheet(gid(i),name,{field:value})
    await i.response.send_message(embed=sheet_embed(s))

@bot.tree.command(name="portrait", description="Set a character portrait URL")
async def portrait(i, character: str, image_url: str):
    s=store.patch_sheet(gid(i),character,{"portrait_url":image_url})
    await i.response.send_message(embed=sheet_embed(s))

@bot.tree.command(name="check", description="Roll a character skill check")
async def check(i, character: str, skill: str, advantage: bool=False, disadvantage: bool=False):
    s=store.sheet(gid(i),character); key=skill.lower().replace(" ","_")
    if key not in SKILLS: raise ValueError("Unknown skill.")
    ability=SKILLS[key]; mod=ability_modifier(s.get(ability))
    profs=[str(x).lower().replace(" ","_") for x in s.get("skill_proficiencies",[])]
    if key in profs: mod+=2+(max(1,int(s.get("level",1)))-1)//4
    r=d20(mod,advantage,disadvantage)
    e=discord.Embed(title=character+" • "+skill.title(),description="🎲 "+str(r["rolls"])+"\n**Total: "+str(r["total"])+"**")
    e.add_field(name="Modifier",value=("%+d"%mod),inline=True); e.add_field(name="Mode",value=r["mode"].title(),inline=True)
    await i.response.send_message(embed=e)

@bot.tree.command(name="save", description="Roll an ability saving throw")
async def save(i, character: str, ability: str, advantage: bool=False, disadvantage: bool=False):
    s=store.sheet(gid(i),character); ability=ability.lower()
    aliases={"str":"strength","dex":"dexterity","con":"constitution","int":"intelligence","wis":"wisdom","cha":"charisma"}; ability=aliases.get(ability,ability)
    if ability not in aliases.values(): raise ValueError("Use STR, DEX, CON, INT, WIS, or CHA.")
    mod=ability_modifier(s.get(ability)); profs=[str(x).lower() for x in s.get("save_proficiencies",[])]
    if ability in profs or ability[:3] in profs: mod+=2+(max(1,int(s.get("level",1)))-1)//4
    r=d20(mod,advantage,disadvantage)
    await i.response.send_message(embed=discord.Embed(title=character+" • "+ability.title()+" Save",description="🎲 "+str(r["rolls"])+"\n**Total: "+str(r["total"])+"**"))

@bot.tree.command(name="attack", description="Make an attack against AC and roll damage on a hit")
async def attack(i, character: str, target: str, attack_bonus: int, target_ac: int, damage: str="1d8"):
    a=d20(attack_bonus); hit=a["natural"]==20 or (a["natural"]!=1 and a["total"]>=target_ac)
    e=discord.Embed(title="⚔️ "+character+" attacks "+target)
    e.add_field(name="Attack",value=str(a["rolls"])+" "+("%+d"%attack_bonus)+" = **"+str(a["total"])+"**",inline=False)
    e.add_field(name="Target AC",value=str(target_ac),inline=True)
    e.add_field(name="Result",value="CRITICAL HIT" if a["natural"]==20 else "HIT" if hit else "MISS",inline=True)
    if hit:
        expr=damage
        if a["natural"]==20:
            m=__import__("re").match(r"^(\d*)d(\d+)([+-]\d+)?$",damage.replace(" ",""))
            if m: expr=str(int(m.group(1) or 1)*2)+"d"+m.group(2)+(m.group(3) or "")
        d=roll_expression(expr); e.add_field(name="Damage",value=d["detail"]+" = **"+str(d["total"])+"**",inline=False)
    await i.response.send_message(embed=e)

@bot.tree.command(name="damage", description="Damage a tracked character")
async def damage(i, character: str, amount: int):
    c=store.set_hp_delta(gid(i),character,-abs(amount)); await i.response.send_message("💥 **"+c["name"]+"**\nHP "+str(c["hp"])+"/"+str(c["max_hp"]))

@bot.tree.command(name="heal", description="Heal a tracked character")
async def heal(i, character: str, amount: int):
    c=store.set_hp_delta(gid(i),character,abs(amount)); await i.response.send_message("💚 **"+c["name"]+"**\nHP "+str(c["hp"])+"/"+str(c["max_hp"]))

@bot.tree.command(name="temp_hp", description="Set temporary hit points")
async def temp_hp(i, character: str, amount: int):
    s=store.set_temp_hp(gid(i),character,amount); await i.response.send_message("🛡️ **"+character+"**\nTemporary HP "+str(s.get("temp_hp",0)))

@bot.tree.command(name="combat_begin", description="Start combat using current initiative")
async def combat_begin(i):
    store.combat_begin(gid(i)); rows=store.initiative(gid(i))
    await i.response.send_message(embed=discord.Embed(title="⚔️ Combat Begins",description="\n".join(str(n+1)+". "+x["name"]+" • "+str(x["total"]) for n,x in enumerate(rows)) or "Add combatants with /initiative_add"))

@bot.tree.command(name="combat_next", description="Advance to the next combatant")
async def combat_next(i):
    s=store.combat_next(gid(i)); await i.response.send_message("⚔️ **Round "+str(s["round"])+"**\nTurn: **"+s["combatant"]["name"]+"**")

@bot.tree.command(name="combat_prev", description="Go back one combat turn")
async def combat_prev(i):
    s=store.combat_next(gid(i),True); await i.response.send_message("⚔️ **Round "+str(s["round"])+"**\nTurn: **"+s["combatant"]["name"]+"**")

@bot.tree.command(name="combat_status", description="Show combat round and turn order")
async def combat_status(i):
    s=store.combat_state(gid(i)); rows=store.initiative(gid(i))
    lines=[]
    for n,x in enumerate(rows): lines.append(("➡️ " if s["active"] and n==s["turn"] else "")+str(n+1)+". "+x["name"]+" • "+str(x["total"]))
    await i.response.send_message(embed=discord.Embed(title="⚔️ Combat • Round "+str(s["round"]),description="\n".join(lines) or "No combatants."))

@bot.tree.command(name="combat_end", description="End combat and clear initiative")
async def combat_end(i):
    store.combat_end(gid(i)); await i.response.send_message("Combat ended.")

@bot.tree.command(name="relationship", description="Set a relationship metric from -100 to 100")
async def relationship(i, source: str, target: str, metric: str, value: int):
    r=store.relationship_set(gid(i),source,target,metric.lower(),value)
    await i.response.send_message("**"+source+" → "+target+"**\nAffinity "+str(r["affinity"])+"\nTrust "+str(r["trust"])+"\nFear "+str(r["fear"])+"\nResentment "+str(r["resentment"]))

@bot.tree.command(name="relationships", description="Show relationship state")
async def relationships(i, character: str=""):
    rows=store.relationships(gid(i),character or None)
    await i.response.send_message("\n".join(x["source"]+" → "+x["target"]+" | affinity "+str(x["affinity"])+" | trust "+str(x["trust"])+" | fear "+str(x["fear"])+" | resentment "+str(x["resentment"]) for x in rows)[:1900] or "No relationships yet.")

@bot.tree.command(name="lore_add", description="Add campaign lore")
async def lore_add(i, key: str, text: str, secret: bool=False):
    store.lore_set(gid(i),key,text,secret); await i.response.send_message("Lore saved: **"+key+"**",ephemeral=secret)

@bot.tree.command(name="lore", description="Read campaign lore")
async def lore(i, key: str):
    x=store.lore_get(gid(i),key,False); await i.response.send_message(embed=discord.Embed(title="📚 "+x["key"],description=x["text"][:4000]))

@bot.tree.command(name="rule", description="Ask the AI to explain a D&D rule")
async def rule(i, question: str):
    await i.response.defer()
    try: await i.followup.send(ask_ai("Explain this D&D rules question clearly. If edition matters, say so. Do not invent a rule: "+question,purpose="D&D rules helper")[:1900])
    except Exception as e: await i.followup.send("AI unavailable: "+str(e))

@bot.tree.command(name="world", description="Ask about or develop the campaign world")
async def world(i, question: str):
    await i.response.defer()
    try: await i.followup.send(ask_ai(question,purpose="campaign world and lore assistant")[:1900])
    except Exception as e: await i.followup.send("AI unavailable: "+str(e))

@bot.tree.command(name="proxy", description="Roleplay a message as a configured character")
async def proxy(i, character: str, message: str):
    s=store.sheet(gid(i),character); await i.response.defer()
    try:
        ctx=store.character_context(gid(i),character)\n        answer=ask_ai("Character context: "+str(ctx)+"\nSituation/message: "+message+"\nReply only as this character. Do not use campaign knowledge the character has not learned.",character,"character proxy")
        e=discord.Embed(description=answer[:4000]); e.set_author(name=character)
        if s.get("portrait_url"): e.set_thumbnail(url=s["portrait_url"])
        await i.followup.send(embed=e)
    except Exception as e: await i.followup.send("AI unavailable: "+str(e))

@bot.tree.command(name="reset_campaign", description="DANGER: reset campaign state after confirmation")
async def reset_campaign(i, confirmation: str):
    if confirmation != "RESET": await i.response.send_message("Reset cancelled. Type exactly RESET to confirm.",ephemeral=True); return
    store.snapshot(gid(i)); store.campaign_reset(gid(i)); await i.response.send_message("Campaign state reset. A snapshot was created first.")

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
