"""Real-time browser bridge for Wopples' Dungeon Buddy.

Run beside the Discord bot. Both processes use the same SQLite campaign database.
The browser receives live board state over WebSockets and may move/damage/heal tokens.
"""

import asyncio, json, os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
from dungeon_assist.store import Store

app=FastAPI(title="Wopples Dungeon Buddy VTT")
store=Store(os.getenv("DUNGEON_DB","dungeon_assist.db"))
clients={}

def state(guild):
    return {"type":"state","guild":guild,"scene":store.vtt_scene(guild),"creatures":store.creatures(guild),"walls":store.vtt_walls(guild),"lights":store.vtt_lights(guild),"initiative":store.initiative(guild),"combat":store.combat_state(guild)}

async def broadcast(guild):
    dead=[]
    payload=json.dumps(state(guild))
    for ws in clients.get(guild,set()):
        try: await ws.send_text(payload)
        except Exception: dead.append(ws)
    for ws in dead: clients.get(guild,set()).discard(ws)

@app.get("/")
async def index():
    return FileResponse("board/index.html")

@app.get("/api/{guild}/state")
async def get_state(guild:int, token:str):
    if token != store.guild_access(guild)["vtt_token"]: raise HTTPException(403,"Invalid VTT access token")
    try: return state(guild)
    except Exception as e: raise HTTPException(400,str(e))

@app.websocket("/ws/{guild}")
async def socket(ws:WebSocket,guild:int):
    token=ws.query_params.get("token","")
    if token != store.guild_access(guild)["vtt_token"]:
        await ws.close(code=1008,reason="Invalid VTT access token"); return
    await ws.accept(); clients.setdefault(guild,set()).add(ws)
    await ws.send_text(json.dumps(state(guild)))
    try:
        while True:
            msg=json.loads(await ws.receive_text())
            action=msg.get("action")
            name=str(msg.get("name",""))
            if action=="move":
                store.creature_move(guild,name,int(msg["x"]),int(msg["y"]))
            elif action=="damage":
                store.creature_hp(guild,name,-abs(int(msg.get("amount",1))))
            elif action=="heal":
                store.creature_hp(guild,name,abs(int(msg.get("amount",1))))
            elif action=="door":
                store.vtt_door_toggle(guild,int(msg["id"]))
            elif action=="wall_add":
                store.vtt_wall_add(guild,msg["x1"],msg["y1"],msg["x2"],msg["y2"],msg.get("kind","wall"),msg.get("door_state","closed"))
            elif action=="light_add":
                store.vtt_light_add(guild,msg["x"],msg["y"],msg.get("radius",4),msg.get("bright",2))
            elif action=="refresh":
                pass
            else:
                await ws.send_text(json.dumps({"type":"error","message":"Unsupported browser action."})); continue
            await broadcast(guild)
    except WebSocketDisconnect:
        clients.get(guild,set()).discard(ws)
    except Exception as e:
        clients.get(guild,set()).discard(ws)
        try: await ws.close(code=1011,reason=str(e)[:100])
        except Exception: pass

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app,host=os.getenv("VTT_HOST","0.0.0.0"),port=int(os.getenv("VTT_PORT","8000")))
