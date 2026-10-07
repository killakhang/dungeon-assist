"""Wopples World v0.1 authoritative multiplayer server."""
import asyncio, json, os, time, subprocess, sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from dungeon_assist.store import Store
from dungeon_assist.ai import ask_ai
from dungeon_assist.pdf_sheet import build_character_pdf
import uvicorn
from wopples_world.combat import CombatWorld

combat=CombatWorld()

app=FastAPI(title="Wopples World")
players={}
clients=set()
lock=asyncio.Lock()
bot_process=None
store=Store(os.getenv("DUNGEON_DB", "dungeon_assist.db"))
WEB_GUILD=int(os.getenv("WEB_GUILD_ID", "1"))

@app.on_event("startup")
async def start_discord_bot():
    global bot_process
    if os.getenv("DISCORD_TOKEN"):
        bot_process=subprocess.Popen([sys.executable, "run.py"])
        print(f"Dungeon Assist Discord bot started (pid={bot_process.pid})", flush=True)
    else:
        print("DISCORD_TOKEN is not set; Discord bot not started.", flush=True)

@app.on_event("shutdown")
async def stop_discord_bot():
    global bot_process
    if bot_process and bot_process.poll() is None:
        bot_process.terminate()
        try:
            bot_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            bot_process.kill()



class ChatRequest(BaseModel):
    character: str = "Wopples"
    message: str

class CharacterPatch(BaseModel):
    name: str | None = None
    class_name: str | None = None
    level: int | None = None
    species: str | None = None
    background: str | None = None
    alignment: str | None = None
    strength: int | None = None
    dexterity: int | None = None
    constitution: int | None = None
    intelligence: int | None = None
    wisdom: int | None = None
    charisma: int | None = None
    hp: int | None = None
    max_hp: int | None = None
    temp_hp: int | None = None
    armor_class: int | None = None
    speed: str | None = None
    initiative_bonus: str | None = None
    hit_dice: str | None = None
    personality: str | None = None
    ideals: str | None = None
    bonds: str | None = None
    flaws: str | None = None
    appearance: str | None = None
    backstory: str | None = None
    proficiencies_languages: str | None = None
    features_traits: str | None = None
    attacks: str | None = None
    equipment: str | None = None
    subclass: str | None = None
    proficiency_bonus: str | None = None
    heroic_inspiration: str | None = None
    passive_perception: str | None = None
    senses: str | None = None
    saving_throws: str | None = None
    skills: str | None = None
    weapon_masteries: str | None = None
    feats: str | None = None
    class_features: str | None = None
    species_traits: str | None = None
    coins: str | None = None
    spellcasting_ability: str | None = None
    spell_save_dc: str | None = None
    spell_attack_bonus: str | None = None
    cantrips: str | None = None
    prepared_spells: str | None = None
    spell_slots: str | None = None

@app.get("/")
async def home():
    return FileResponse("wopples_world/app.html")

def _web_sheet(name):
    try:
        return store.sheet(WEB_GUILD,name)
    except Exception:
        store.setup_campaign(WEB_GUILD,"Wopples World")
        store.create_character(WEB_GUILD,0,name,"Paladin",10)
        store.save_sheet(WEB_GUILD,name,{
            "ruleset":"D&D 2024","species":"Goblin","background":"Wayfarer","alignment":"Chaotic Neutral",
            "class":"Paladin","subclass":"Oath of Vengeance","level":10,
            "strength":18,"dexterity":14,"constitution":16,"intelligence":10,"wisdom":12,"charisma":18,
            "proficiency_bonus":"+4","armor_class":20,"hp":94,"max_hp":94,"temp_hp":0,"speed":"30 ft.","initiative_bonus":"+2","hit_dice":"10d10",
            "passive_perception":"15","heroic_inspiration":"No","saving_throws":"○ Strength +4\n○ Dexterity +2\n○ Constitution +3\n○ Intelligence +0\n● Wisdom +5\n● Charisma +8",
            "skills":"○ Acrobatics +2\n○ Animal Handling +1\n○ Arcana +0\n● Athletics +8\n○ Deception +4\n○ History +0\n● Insight +5\n○ Intimidation +4\n○ Investigation +0\n○ Medicine +1\n○ Nature +0\n● Perception +5\n○ Performance +4\n● Persuasion +8\n○ Religion +0\n○ Sleight of Hand +2\n○ Stealth +2\n○ Survival +1",
            "senses":"Darkvision 60 ft.; Passive Perception 15",
            "proficiencies_languages":"Armor: Light, Medium, Heavy, Shields\nWeapons: Simple, Martial\nLanguages: Common, Goblin",
            "attacks":"Longsword — +8 to hit — 1d8+4 slashing (1d10+4 versatile)\nJavelin — +8 to hit — 1d6+4 piercing",
            "weapon_masteries":"Longsword; Javelin",
            "class_features":"Lay on Hands; Fighting Style; Paladin's Smite; Channel Divinity; Extra Attack; Faithful Steed; Aura of Protection; Abjure Foes; Aura of Courage",
            "species_traits":"Darkvision; Fey Ancestry; Fury of the Small; Nimble Escape",
            "features_traits":"Chaotic goblin paladin; protects friends fiercely, solves sacred problems with questionable methods.",
            "feats":"Ability Score Improvements used to support Strength and Charisma.",
            "equipment":"Chain Mail; Shield; Longsword; 6 Javelins; Holy Symbol; Priest's Pack",
            "coins":"9 GP","spellcasting_ability":"Charisma","spell_save_dc":"16","spell_attack_bonus":"+8",
            "cantrips":"","prepared_spells":"Bless\nCommand\nCure Wounds\nDetect Magic\nProtection from Evil and Good\nAid\nFind Steed\nLesser Restoration\nRevivify",
            "spell_slots":"1st: 4 / 4\n2nd: 3 / 3\n3rd: 2 / 2",
            "personality":["Chaotic","cartoonish","curious","recklessly confident","loyal when it counts"],
            "ideals":"Freedom. Rules are tools, not cages.","bonds":"The party is Wopples' people. Wopples may complain, but nobody else gets to hurt them.",
            "flaws":"Impulsive, distractible, suspicious of authority, and dangerously confident around mysterious buttons.",
            "appearance":"Small green goblin adventurer with expressive ears, battered gear, and the posture of someone about to make a questionable decision.",
            "backstory":"Wopples became a paladin less because institutions chose him and more because Wopples decided the world needed a champion with worse judgment. His oath is sincere even when his methods are chaotic."
        })
        return store.sheet(WEB_GUILD,name)

WOPPLES_CANON={
    "ruleset":"D&D 2024","species":"Goblin","background":"Wayfarer","alignment":"Chaotic Neutral","class":"Paladin","subclass":"Oath of Vengeance","level":10,
    "strength":18,"dexterity":14,"constitution":16,"intelligence":10,"wisdom":12,"charisma":18,"proficiency_bonus":"+4","armor_class":20,"hp":94,"max_hp":94,"temp_hp":0,
    "speed":"30 ft.","initiative_bonus":"+2","hit_dice":"10d10","passive_perception":"15","heroic_inspiration":"No",
    "saving_throws":"○ Strength +4\\n○ Dexterity +2\\n○ Constitution +3\\n○ Intelligence +0\\n● Wisdom +5\\n● Charisma +8",
    "skills":"○ Acrobatics +2\\n○ Animal Handling +1\\n○ Arcana +0\\n● Athletics +8\\n○ Deception +4\\n○ History +0\\n● Insight +5\\n○ Intimidation +4\\n○ Investigation +0\\n○ Medicine +1\\n○ Nature +0\\n● Perception +5\\n○ Performance +4\\n● Persuasion +8\\n○ Religion +0\\n○ Sleight of Hand +2\\n○ Stealth +2\\n○ Survival +1",
    "senses":"Darkvision 60 ft.; Passive Perception 15","proficiencies_languages":"Armor: Light, Medium, Heavy, Shields\\nWeapons: Simple, Martial\\nLanguages: Common, Goblin",
    "attacks":"Longsword — +8 to hit — 1d8+4 slashing (1d10+4 versatile)\\nJavelin — +8 to hit — 1d6+4 piercing","weapon_masteries":"Longsword; Javelin",
    "class_features":"Lay on Hands; Fighting Style; Paladin's Smite; Channel Divinity; Extra Attack; Faithful Steed; Aura of Protection; Abjure Foes; Aura of Courage",
    "species_traits":"Darkvision; Fey Ancestry; Fury of the Small; Nimble Escape","features_traits":"Chaotic goblin paladin; protects friends fiercely, solves sacred problems with questionable methods.",
    "feats":"Ability Score Improvements used to support Strength and Charisma.","equipment":"Chain Mail; Shield; Longsword; 6 Javelins; Holy Symbol; Priest's Pack","coins":"9 GP",
    "spellcasting_ability":"Charisma","spell_save_dc":"16","spell_attack_bonus":"+8","cantrips":"","prepared_spells":"Bless\\nCommand\\nCure Wounds\\nDetect Magic\\nProtection from Evil and Good\\nAid\\nFind Steed\\nLesser Restoration\\nRevivify","spell_slots":"1st: 4 / 4\\n2nd: 3 / 3\\n3rd: 2 / 2",
    "personality":["Chaotic","cartoonish","curious","recklessly confident","loyal when it counts"],"ideals":"Freedom. Rules are tools, not cages.","bonds":"The party is Wopples' people. Wopples may complain, but nobody else gets to hurt them.",
    "flaws":"Impulsive, distractible, suspicious of authority, and dangerously confident around mysterious buttons.","appearance":"Small green goblin adventurer with expressive ears, battered gear, and the posture of someone about to make a questionable decision.",
    "backstory":"Wopples became a paladin less because institutions chose him and more because Wopples decided the world needed a champion with worse judgment. His oath is sincere even when his methods are chaotic."
}

@app.post("/api/character/{name}/canon")
async def load_canon(name:str):
    _web_sheet(name)
    data=dict(WOPPLES_CANON)
    return store.patch_sheet(WEB_GUILD,name,data)

@app.get("/api/character/{name}")
async def web_character(name:str):
    return _web_sheet(name)

@app.patch("/api/character/{name}")
async def web_character_patch(name:str, patch:CharacterPatch):
    _web_sheet(name)
    updates={}
    for key,value in patch.model_dump(exclude_none=True).items():
        if key == "class_name": key = "class"
        if key == "personality": value=[x.strip() for x in value.split(",") if x.strip()]
        updates[key]=value
    return store.patch_sheet(WEB_GUILD,name,updates)

@app.post("/api/chat")
async def web_chat(req:ChatRequest):
    s=_web_sheet(req.character)
    try: ctx=store.character_context(WEB_GUILD,req.character)
    except Exception: ctx={"sheet":s}
    try:
        reply=await asyncio.to_thread(ask_ai,"Character context: "+str(ctx)+"\nUser says: "+req.message+"\nReply only as the character. Be conversational and concise.",req.character,"browser character proxy")
        return {"reply":reply}
    except Exception as e:
        raise HTTPException(status_code=503,detail=str(e))

@app.get("/api/character/{name}/pdf")
async def web_character_pdf(name:str):
    pdf=build_character_pdf(_web_sheet(name))
    safe="".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name) or "character"
    return StreamingResponse(pdf,media_type="application/pdf",headers={"Content-Disposition":f'inline; filename="{safe}_character_sheet.pdf"'})

@app.get("/world")
async def world():
    return FileResponse("wopples_world/index.html")

async def broadcast():
    dead=[]
    msg=json.dumps({"type":"state","players":players,"combat":combat.snapshot(),"server_time":time.time()})
    for ws in list(clients):
        try: await ws.send_text(msg)
        except Exception: dead.append(ws)
    for ws in dead: clients.discard(ws)

@app.websocket("/world/ws")
async def world_ws(ws:WebSocket):
    await ws.accept(); clients.add(ws)
    name=(ws.query_params.get("name") or "Goblin")[:24]
    pid=str(id(ws))
    players[pid]={"id":pid,"name":name,"x":8.0,"y":7.0}
    combat.add_player(pid,name)
    try:
        await broadcast()
        while True:
            data=json.loads(await ws.receive_text())
            action=data.get("action","move")
            if action=="attack": combat.attack(pid)
            elif action=="dodge": combat.dodge(pid,float(data.get("dx",1)),float(data.get("dy",0)))
            elif action=="spawn_squad": combat.spawn_squad(min(8,max(1,int(data.get("count",5)))))
            elif action=="spawn_boss": combat.spawn_boss()
            elif action=="heal": combat.heal(pid)
            elif action=="revive": combat.revive(pid,str(data.get("target_id","")))
            combat.tick(.08)
            async with lock:
                p=players[pid]
                # Server owns canonical position and caps movement per update.
                tx=float(data.get("x",p["x"])); ty=float(data.get("y",p["y"]))
                dx=max(-.35,min(.35,tx-p["x"])); dy=max(-.35,min(.35,ty-p["y"]))
                p["x"]=max(.5,min(23.5,p["x"]+dx)); p["y"]=max(.5,min(15.5,p["y"]+dy))
            await broadcast()
    except WebSocketDisconnect: pass
    finally:
        clients.discard(ws); players.pop(pid,None); combat.players.pop(pid,None); await broadcast()

if __name__=="__main__":
    uvicorn.run(app,host=os.getenv("WORLD_HOST","0.0.0.0"),port=int(os.getenv("WORLD_PORT","8010")))
