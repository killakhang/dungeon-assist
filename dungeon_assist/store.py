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
    def snapshot(self,g):
        self._campaign(g); data={"campaign":dict(self.db.execute("SELECT * FROM campaigns WHERE guild=?",(g,)).fetchone()),"characters":[dict(x) for x in self.db.execute("SELECT * FROM characters WHERE guild=?",(g,))],"quests":[dict(x) for x in self.db.execute("SELECT * FROM quests WHERE guild=?",(g,))],"initiative":[dict(x) for x in self.db.execute("SELECT * FROM initiative WHERE guild=?",(g,))]}
        sid=str(uuid.uuid4())[:8]; self.db.execute("INSERT INTO snapshots VALUES(?,?,?,?)",(sid,g,json.dumps(data),datetime.now(timezone.utc).isoformat())); self.db.commit(); return sid
