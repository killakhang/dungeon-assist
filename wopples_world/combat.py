"""Engine-neutral combat prototype for Wopples World."""
from dataclasses import dataclass, asdict
import math, random, time

@dataclass
class Fighter:
    id:str; name:str; x:float; y:float; hp:int=100; max_hp:int=100
    stamina:float=100; down:bool=False; invuln_until:float=0; attack_until:float=0

@dataclass
class Monster:
    id:str; name:str; x:float; y:float; hp:int=80; max_hp:int=80
    damage:int=15; speed:float=1.2; boss:bool=False; phase:int=1

class CombatWorld:
    def __init__(self):
        self.players={}; self.monsters={}; self.events=[]; self.started=False
    def add_player(self,pid,name):
        self.players[pid]=Fighter(pid,name,4+len(self.players),8); return self.players[pid]
    def spawn_squad(self,n=5):
        self.monsters={f"slime{i}":Monster(f"slime{i}",f"Angry Blob {i+1}",15+i%3,5+i,55,55,12,1.1) for i in range(n)}
        self.started=True; self.emit("encounter","Monster squad arrives!")
    def spawn_boss(self):
        self.monsters={"king":Monster("king","Mushroom King",17,8,700,700,24,.85,True,1)}
        self.started=True; self.emit("encounter","THE MUSHROOM KING AWAKENS")
    def emit(self,kind,text,**data):
        self.events.append({"kind":kind,"text":text,"at":time.time(),**data}); self.events=self.events[-30:]
    def move(self,pid,dx,dy,dt):
        p=self.players[pid]
        if p.down:return
        l=math.hypot(dx,dy) or 1; speed=4.2
        p.x=max(.5,min(23.5,p.x+dx/l*speed*dt));p.y=max(.5,min(15.5,p.y+dy/l*speed*dt))
        p.stamina=min(100,p.stamina+18*dt)
    def dodge(self,pid,dx,dy):
        p=self.players[pid]
        if p.down or p.stamina<22:return False
        p.stamina-=22;p.invuln_until=time.time()+.32
        l=math.hypot(dx,dy) or 1;p.x+=dx/l*1.35;p.y+=dy/l*1.35;return True
    def attack(self,pid):
        p=self.players[pid]; now=time.time()
        if p.down or now<p.attack_until:return
        p.attack_until=now+.38
        targets=[m for m in self.monsters.values() if m.hp>0 and math.hypot(m.x-p.x,m.y-p.y)<1.35]
        if targets:
            m=min(targets,key=lambda z:math.hypot(z.x-p.x,z.y-p.y));m.hp=max(0,m.hp-22)
            self.emit("hit",f"{p.name} bonks {m.name}!",target=m.id,damage=22)
            if not m.hp:self.emit("ko",f"{m.name} defeated!")
    def tick(self,dt):
        now=time.time()
        alive=[p for p in self.players.values() if not p.down]
        for m in self.monsters.values():
            if m.hp<=0 or not alive:continue
            if m.boss:
                ratio=m.hp/m.max_hp;m.phase=3 if ratio<.33 else 2 if ratio<.66 else 1
            p=min(alive,key=lambda q:math.hypot(q.x-m.x,q.y-m.y));d=math.hypot(p.x-m.x,p.y-m.y)
            if d>1:
                m.x+=(p.x-m.x)/d*m.speed*dt;m.y+=(p.y-m.y)/d*m.speed*dt
            elif random.random()<dt*.8 and now>=p.invuln_until:
                p.hp=max(0,p.hp-m.damage);self.emit("hurt",f"{m.name} hits {p.name}!",target=p.id,damage=m.damage)
                if p.hp==0:p.down=True;self.emit("down",f"{p.name} is down!")
    def snapshot(self):
        return {"players":[asdict(x) for x in self.players.values()],"monsters":[asdict(x) for x in self.monsters.values()],"events":self.events,"won":self.started and bool(self.monsters) and all(m.hp<=0 for m in self.monsters.values())}
