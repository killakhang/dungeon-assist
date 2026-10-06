import json, sqlite3, uuid
from datetime import datetime, timezone

class Store:
    def __init__(self,path):
        self.db=sqlite3.connect(path,check_same_thread=False)
        self.db.row_factory=sqlite3.Row
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS campaigns(guild INTEGER PRIMARY KEY,name TEXT,scene TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS characters(guild INTEGER,name TEXT COLLATE NOCASE,owner INTEGER,class TEXT,level INTEGER DEFAULT 1,hp INTEGER,max_hp INTEGER,conditions TEXT DEFAULT '',PRIMARY KEY(guild,name));\n        CREATE TABLE IF NOT EXISTS character_sheets(guild INTEGER,name TEXT COLLATE NOCASE,data TEXT DEFAULT '{}',PRIMARY KEY(guild,name));
        CREATE TABLE IF NOT EXISTS initiative(guild INTEGER,name TEXT,total INTEGER);
        CREATE TABLE IF NOT EXISTS quests(guild INTEGER,title TEXT,status TEXT DEFAULT 'active');
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,guild INTEGER,kind TEXT,text TEXT,actor INTEGER,created TEXT);
        CREATE TABLE IF NOT EXISTS snapshots(id TEXT PRIMARY KEY,guild INTEGER,data TEXT,created TEXT);
        CREATE TABLE IF NOT EXISTS combat_state(guild INTEGER PRIMARY KEY,turn INTEGER DEFAULT 0,round INTEGER DEFAULT 1,active INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS relationships(guild INTEGER,source TEXT,target TEXT,affinity INTEGER DEFAULT 0,trust INTEGER DEFAULT 0,fear INTEGER DEFAULT 0,resentment INTEGER DEFAULT 0,PRIMARY KEY(guild,source,target));
        CREATE TABLE IF NOT EXISTS lore(guild INTEGER,key TEXT COLLATE NOCASE,text TEXT,secret INTEGER DEFAULT 0,PRIMARY KEY(guild,key));
        CREATE TABLE IF NOT EXISTS character_memory(id INTEGER PRIMARY KEY AUTOINCREMENT,guild INTEGER,character TEXT COLLATE NOCASE,kind TEXT,text TEXT,importance INTEGER DEFAULT 50,created TEXT);
        CREATE TABLE IF NOT EXISTS character_knowledge(guild INTEGER,character TEXT COLLATE NOCASE,key TEXT COLLATE NOCASE,text TEXT,source TEXT DEFAULT 'campaign',PRIMARY KEY(guild,character,key));
        CREATE TABLE IF NOT EXISTS factions(guild INTEGER,name TEXT COLLATE NOCASE,description TEXT DEFAULT '',reputation INTEGER DEFAULT 0,PRIMARY KEY(guild,name));
        CREATE TABLE IF NOT EXISTS effects(guild INTEGER,character TEXT COLLATE NOCASE,name TEXT COLLATE NOCASE,rounds INTEGER DEFAULT 0,concentration INTEGER DEFAULT 0,PRIMARY KEY(guild,character,name));
        CREATE TABLE IF NOT EXISTS campaign_settings(guild INTEGER PRIMARY KEY,reset_locked INTEGER DEFAULT 1,theme TEXT DEFAULT 'fantasy');
        """)
    def _campaign(self,g):
        if not self.db.execute("SELECT 1 FROM campaigns WHERE guild=?",(g,)).fetchone(): raise ValueError("Run /campaign_setup first.")
    def setup_campaign(self,g,name):
        self.db.execute("INSERT INTO campaigns(guild,name) VALUES(?,?) ON CONFLICT(guild) DO UPDATE SET name=excluded.name",(g,name)); self.db.commit()
    def create_character(self,g,owner,name,cls,max_hp):
        self._campaign(g); self.db.execute("INSERT OR REPLACE INTO characters(guild,name,owner,class,hp,max_hp) VALUES(?,?,?,?,?,?)",(g,name,owner,cls,max_hp,max_hp)); self.db.commit()
    def save_sheet(self,g,name,data):
        self.character(g,name)
        self.db.execute("INSERT INTO character_sheets(guild,name,data) VALUES(?,?,?) ON CONFLICT(guild,name) DO UPDATE SET data=excluded.data",(g,name,json.dumps(data)))
        self.db.commit()
        return self.sheet(g,name)
    def sheet(self,g,name):
        c=self.character(g,name)
        r=self.db.execute("SELECT data FROM character_sheets WHERE guild=? AND name=?",(g,name)).fetchone()
        extra=json.loads(r["data"]) if r else {}
        return {**c, **extra}
    def patch_sheet(self,g,name,updates):
        current=self.sheet(g,name)
        base={"guild","name","owner","class","level","hp","max_hp","conditions"}
        extra={k:v for k,v in current.items() if k not in base}
        extra.update(updates)
        return self.save_sheet(g,name,extra)
    def character(self,g,name):
        r=self.db.execute("SELECT * FROM characters WHERE guild=? AND name=?",(g,name)).fetchone()
        if not r: raise ValueError("Character not found.")
        return dict(r)
    def set_hp(self,g,name,amount):
        c=self.character(g,name); amount=max(0,min(amount,c["max_hp"])); self.db.execute("UPDATE characters SET hp=? WHERE guild=? AND name=?",(amount,g,name)); self.db.commit(); return self.character(g,name)
    def condition(self,g,name,value,remove=False):
        c=self.character(g,name); items=[x for x in c["conditions"].split(",") if x]
        if remove: items=[x for x in items if x.lower()!=value.lower()]
        elif value.lower() not in [x.lower() for x in items]: items.append(value)
        self.db.execute("UPDATE characters SET conditions=? WHERE guild=? AND name=?",(",".join(items),g,name)); self.db.commit(); return self.character(g,name)
    def initiative_add(self,g,name,total):
        self._campaign(g); self.db.execute("DELETE FROM initiative WHERE guild=? AND name=?",(g,name)); self.db.execute("INSERT INTO initiative VALUES(?,?,?)",(g,name,total)); self.db.commit()
    def initiative(self,g): return [dict(x) for x in self.db.execute("SELECT name,total FROM initiative WHERE guild=? ORDER BY total DESC,name",(g,))]
    def initiative_clear(self,g): self.db.execute("DELETE FROM initiative WHERE guild=?",(g,)); self.db.commit()
    def quest_add(self,g,title): self._campaign(g); self.db.execute("INSERT INTO quests(guild,title) VALUES(?,?)",(g,title)); self.db.commit()
    def quests(self,g): return [x["title"] for x in self.db.execute("SELECT title FROM quests WHERE guild=? AND status='active'",(g,))]
    def scene(self,g,text): self._campaign(g); self.db.execute("UPDATE campaigns SET scene=? WHERE guild=?",(text,g)); self.event(g,"scene",text,0); self.db.commit()
    def event(self,g,kind,text,actor):
        self._campaign(g); self.db.execute("INSERT INTO events(guild,kind,text,actor,created) VALUES(?,?,?,?,?)",(g,kind,text,actor,datetime.now(timezone.utc).isoformat())); self.db.commit()
    def recap(self,g,limit=10): return [dict(x) for x in self.db.execute("SELECT text,kind,created FROM events WHERE guild=? ORDER BY id DESC LIMIT ?",(g,limit))]

    def set_hp_delta(self,g,name,delta):
        c=self.character(g,name); return self.set_hp(g,name,c["hp"]+delta)
    def set_temp_hp(self,g,name,amount):
        return self.patch_sheet(g,name,{"temp_hp":max(0,amount)})
    def combat_begin(self,g):
        self._campaign(g); self.db.execute("INSERT INTO combat_state(guild,turn,round,active) VALUES(?,0,1,1) ON CONFLICT(guild) DO UPDATE SET turn=0,round=1,active=1",(g,)); self.db.commit()
    def combat_state(self,g):
        r=self.db.execute("SELECT * FROM combat_state WHERE guild=?",(g,)).fetchone(); return dict(r) if r else {"guild":g,"turn":0,"round":1,"active":0}
    def combat_next(self,g,back=False):
        rows=self.initiative(g)
        if not rows: raise ValueError("No combatants in initiative.")
        s=self.combat_state(g)
        if not s["active"]: raise ValueError("Run /combat_begin first.")
        turn=s["turn"] + (-1 if back else 1); rnd=s["round"]
        if turn>=len(rows): turn=0; rnd+=1
        if turn<0: turn=len(rows)-1; rnd=max(1,rnd-1)
        self.db.execute("UPDATE combat_state SET turn=?,round=? WHERE guild=?",(turn,rnd,g)); self.db.commit()
        return {"round":rnd,"turn":turn,"combatant":rows[turn]}
    def combat_end(self,g):
        self.db.execute("DELETE FROM combat_state WHERE guild=?",(g,)); self.initiative_clear(g)
    def relationship_set(self,g,source,target,metric,value):
        if metric not in {"affinity","trust","fear","resentment"}: raise ValueError("Metric must be affinity, trust, fear, or resentment.")
        value=max(-100,min(100,value))
        self.db.execute("INSERT INTO relationships(guild,source,target,"+metric+") VALUES(?,?,?,?) ON CONFLICT(guild,source,target) DO UPDATE SET "+metric+"=excluded."+metric,(g,source,target,value)); self.db.commit()
        return dict(self.db.execute("SELECT * FROM relationships WHERE guild=? AND source=? AND target=?",(g,source,target)).fetchone())
    def relationships(self,g,source=None):
        if source: rows=self.db.execute("SELECT * FROM relationships WHERE guild=? AND source=? ORDER BY target",(g,source))
        else: rows=self.db.execute("SELECT * FROM relationships WHERE guild=? ORDER BY source,target",(g,))
        return [dict(x) for x in rows]
    def lore_set(self,g,key,text,secret=False):
        self._campaign(g); self.db.execute("INSERT INTO lore(guild,key,text,secret) VALUES(?,?,?,?) ON CONFLICT(guild,key) DO UPDATE SET text=excluded.text,secret=excluded.secret",(g,key,text,int(secret))); self.db.commit()
    def lore_get(self,g,key,include_secret=False):
        q="SELECT * FROM lore WHERE guild=? AND key=?"
        r=self.db.execute(q,(g,key)).fetchone()
        if not r or (r["secret"] and not include_secret): raise ValueError("Lore entry not found.")
        return dict(r)
    def memory_add(self,g,character,text,kind="memory",importance=50):
        self.character(g,character); importance=max(0,min(100,int(importance)))
        self.db.execute("INSERT INTO character_memory(guild,character,kind,text,importance,created) VALUES(?,?,?,?,?,?)",(g,character,kind,text,importance,datetime.now(timezone.utc).isoformat())); self.db.commit()
    def memories(self,g,character,limit=20):
        self.character(g,character)
        return [dict(x) for x in self.db.execute("SELECT id,kind,text,importance,created FROM character_memory WHERE guild=? AND character=? ORDER BY importance DESC,id DESC LIMIT ?",(g,character,limit))]
    def knowledge_set(self,g,character,key,text,source="campaign"):
        self.character(g,character)
        self.db.execute("INSERT INTO character_knowledge(guild,character,key,text,source) VALUES(?,?,?,?,?) ON CONFLICT(guild,character,key) DO UPDATE SET text=excluded.text,source=excluded.source",(g,character,key,text,source)); self.db.commit()
    def knowledge(self,g,character):
        self.character(g,character)
        return [dict(x) for x in self.db.execute("SELECT key,text,source FROM character_knowledge WHERE guild=? AND character=? ORDER BY key",(g,character))]
    def character_context(self,g,character):
        return {"sheet":self.sheet(g,character),"memories":self.memories(g,character,12),"knowledge":self.knowledge(g,character),"relationships":self.relationships(g,character)}

    def faction_set(self,g,name,description="",reputation=0):
        self._campaign(g); reputation=max(-100,min(100,int(reputation)))
        self.db.execute("INSERT INTO factions(guild,name,description,reputation) VALUES(?,?,?,?) ON CONFLICT(guild,name) DO UPDATE SET description=excluded.description,reputation=excluded.reputation",(g,name,description,reputation)); self.db.commit()
    def factions(self,g):
        return [dict(x) for x in self.db.execute("SELECT name,description,reputation FROM factions WHERE guild=? ORDER BY name",(g,))]
    def effect_set(self,g,character,name,rounds=0,concentration=False):
        self.character(g,character)
        self.db.execute("INSERT INTO effects(guild,character,name,rounds,concentration) VALUES(?,?,?,?,?) ON CONFLICT(guild,character,name) DO UPDATE SET rounds=excluded.rounds,concentration=excluded.concentration",(g,character,name,max(0,int(rounds)),int(concentration))); self.db.commit()
    def effects(self,g,character):
        return [dict(x) for x in self.db.execute("SELECT name,rounds,concentration FROM effects WHERE guild=? AND character=? ORDER BY name",(g,character))]
    def effect_remove(self,g,character,name):
        self.db.execute("DELETE FROM effects WHERE guild=? AND character=? AND name=?",(g,character,name)); self.db.commit()
    def death_save(self,g,character,success):
        s=self.sheet(g,character); key="death_save_successes" if success else "death_save_failures"; n=min(3,int(s.get(key,0))+1)
        return self.patch_sheet(g,character,{key:n})
    def reset_death_saves(self,g,character):
        return self.patch_sheet(g,character,{"death_save_successes":0,"death_save_failures":0})
    def settings(self,g):
        self._campaign(g); self.db.execute("INSERT OR IGNORE INTO campaign_settings(guild) VALUES(?)",(g,)); self.db.commit()
        return dict(self.db.execute("SELECT * FROM campaign_settings WHERE guild=?",(g,)).fetchone())
    def set_reset_lock(self,g,locked):
        self.settings(g); self.db.execute("UPDATE campaign_settings SET reset_locked=? WHERE guild=?",(int(locked),g)); self.db.commit()
    def set_theme(self,g,theme):
        self.settings(g); self.db.execute("UPDATE campaign_settings SET theme=? WHERE guild=?",(theme,g)); self.db.commit()

    def campaign_reset(self,g):
        self._campaign(g)
        if self.settings(g)["reset_locked"]: raise ValueError("Campaign reset is locked. Use /reset_unlock first.")
        for table in ("characters","character_sheets","initiative","quests","events","relationships","lore","combat_state","character_memory","character_knowledge","factions","effects"):
            self.db.execute("DELETE FROM "+table+" WHERE guild=?",(g,))
        self.db.execute("UPDATE campaigns SET scene='' WHERE guild=?",(g,)); self.db.commit()

    def snapshot(self,g):
        self._campaign(g); data={"campaign":dict(self.db.execute("SELECT * FROM campaigns WHERE guild=?",(g,)).fetchone()),"characters":[dict(x) for x in self.db.execute("SELECT * FROM characters WHERE guild=?",(g,))],"quests":[dict(x) for x in self.db.execute("SELECT * FROM quests WHERE guild=?",(g,))],"initiative":[dict(x) for x in self.db.execute("SELECT * FROM initiative WHERE guild=?",(g,))]}
        sid=str(uuid.uuid4())[:8]; self.db.execute("INSERT INTO snapshots VALUES(?,?,?,?)",(sid,g,json.dumps(data),datetime.now(timezone.utc).isoformat())); self.db.commit(); return sid
