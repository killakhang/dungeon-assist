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

@app.get("/")
async def home():
    return FileResponse("wopples_world/app.html")

def _web_sheet(name):
    try:
        return store.sheet(WEB_GUILD,name)
    except Exception:
        store.setup_campaign(WEB_GUILD,"Wopples World")
        store.create_character(WEB_GUILD,0,name,"Paladin",10)
        store.save_sheet(WEB_GUILD,name,{"ruleset":"D&D 2024","species":"Human","background":"Soldier","alignment":"Chaotic Good","strength":15,"dexterity":12,"constitution":14,"intelligence":10,"wisdom":11,"charisma":14,"personality":["Chaotic","cartoonish","curious"],"equipment":[],"features_traits":[]})
        return store.sheet(WEB_GUILD,name)

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
