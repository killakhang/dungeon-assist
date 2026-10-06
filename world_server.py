"""Wopples World v0.1 authoritative multiplayer server."""
import asyncio, json, os, time, subprocess, sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
import uvicorn
from wopples_world.combat import CombatWorld

combat=CombatWorld()

app=FastAPI(title="Wopples World")
players={}
clients=set()
lock=asyncio.Lock()
bot_process=None

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
