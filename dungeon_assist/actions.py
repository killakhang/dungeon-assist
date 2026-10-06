"""Core action/resource engine for Wopples' Dungeon Buddy.

This is deliberately data-driven: character attacks, spell slots, counters, and rests
live on the saved character sheet instead of being hard-coded into Discord commands.
"""

def proficiency_bonus(level):
    return 2 + (max(1, int(level)) - 1) // 4

def modifier(score):
    if score is None:
        return 0
    return (int(score) - 10) // 2

def resource_set(sheet, name, current, maximum=None, reset="long"):
    resources=dict(sheet.get("resources") or {})
    maximum=int(current if maximum is None else maximum)
    current=max(0,min(int(current),maximum))
    resources[name]={"current":current,"max":maximum,"reset":reset}
    return resources

def resource_change(sheet, name, delta):
    resources=dict(sheet.get("resources") or {})
    if name not in resources:
        raise ValueError("Resource not found.")
    r=dict(resources[name])
    r["current"]=max(0,min(int(r.get("max",0)),int(r.get("current",0))+int(delta)))
    resources[name]=r
    return resources

def apply_rest(sheet, kind):
    if kind not in {"short","long"}:
        raise ValueError("Rest must be short or long.")
    out=dict(sheet)
    resources=dict(out.get("resources") or {})
    for name,r0 in resources.items():
        r=dict(r0)
        if r.get("reset") == kind or (kind=="long" and r.get("reset") in {"short","long"}):
            r["current"]=int(r.get("max",0))
        resources[name]=r
    out["resources"]=resources
    if kind=="long":
        out["death_save_successes"]=0
        out["death_save_failures"]=0
    return out

def add_attack(sheet, name, bonus, damage, damage_type="", notes=""):
    attacks=list(sheet.get("attacks") or [])
    item={"name":name,"bonus":int(bonus),"damage":damage,"damage_type":damage_type,"notes":notes}
    attacks=[x for x in attacks if str(x.get("name","")).lower()!=name.lower()]
    attacks.append(item)
    return attacks

def spell_slot_set(sheet, level, current, maximum=None):
    slots=dict(sheet.get("spell_slots") or {})
    maximum=int(current if maximum is None else maximum)
    current=max(0,min(int(current),maximum))
    slots[str(int(level))]={"current":current,"max":maximum}
    return slots

def spend_spell_slot(sheet, level):
    slots=dict(sheet.get("spell_slots") or {})
    key=str(int(level))
    if key not in slots or int(slots[key].get("current",0)) < 1:
        raise ValueError("No spell slot available at that level.")
    row=dict(slots[key]); row["current"]=int(row["current"])-1; slots[key]=row
    return slots
