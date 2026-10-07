"""Editable, print-friendly D&D 2024-style character sheet generator."""
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

W,H=letter

def _v(s,k,d=""):
    v=s.get(k,d)
    if isinstance(v,list): return ", ".join(map(str,v))
    if isinstance(v,dict): return ", ".join(f"{a}: {b}" for a,b in v.items())
    return "" if v is None else str(v)

def _mod(v):
    try:
        m=(int(v)-10)//2
        return f"{m:+d}"
    except Exception: return ""

def build_character_pdf(sheet):
    out=BytesIO(); c=canvas.Canvas(out,pagesize=letter)
    form=c.acroform
    c.setTitle(f"{_v(sheet,'name','Character')} - Editable Character Sheet")
    def title(txt,y):
        c.setFont("Helvetica-Bold",12); c.drawString(36,y,txt)
        c.setStrokeColor(colors.HexColor("#777777")); c.line(36,y-4,W-36,y-4)
    def field(label,key,x,y,w=150,h=18,value=None,multi=False):
        c.setFont("Helvetica-Bold",6.5); c.setFillColor(colors.HexColor("#444444")); c.drawString(x,y+h+3,label.upper())
        val=_v(sheet,key) if value is None else str(value)
        flags=4096 if multi else 0
        form.textfield(name=key,value=val,x=x,y=y,width=w,height=h,borderWidth=.7,borderColor=colors.HexColor("#777777"),
            fillColor=colors.white,textColor=colors.black,fontName="Helvetica",fontSize=8,fieldFlags=flags)
    c.setFillColor(colors.black); c.setFont("Helvetica-Bold",18); c.drawString(36,754,"2024 CHARACTER SHEET")
    c.setFont("Helvetica",7); c.drawRightString(W-36,758,"Editable • Wopples Dungeon Buddy")
    field("Character Name","name",36,710,230); field("Class","class",278,710,100); field("Level","level",390,710,45)
    field("Species","species",447,710,109); field("Background","background",36,674,160); field("Alignment","alignment",208,674,120)
    field("Ruleset","ruleset",340,674,216,value=_v(sheet,"ruleset","D&D 2024"))
    title("ABILITY SCORES",646)
    abilities=[("STR","strength"),("DEX","dexterity"),("CON","constitution"),("INT","intelligence"),("WIS","wisdom"),("CHA","charisma")]
    x=36
    for lab,key in abilities:
        field(lab,key,x,604,54,22); field("MOD",key+"_modifier",x,568,54,18,value=_mod(sheet.get(key))); x+=88
    title("COMBAT",544)
    field("Armor Class","armor_class",36,502,75); field("Initiative","initiative_bonus",123,502,75); field("Speed","speed",210,502,75)
    field("Current HP","hp",297,502,75); field("Max HP","max_hp",384,502,75); field("Temp HP","temp_hp",471,502,75)
    field("Hit Dice","hit_dice",36,466,110); field("Conditions","conditions",158,466,258); field("Inspiration","inspiration",428,466,118)
    title("PROFICIENCIES, ATTACKS & EQUIPMENT",442)
    field("Proficiencies / Languages","proficiencies_languages",36,366,245,54,multi=True)
    field("Attacks","attacks",293,366,263,54,multi=True)
    field("Features & Traits","features_traits",36,278,245,66,multi=True)
    field("Equipment","equipment",293,278,263,66,multi=True)
    title("ROLEPLAY",252)
    field("Personality","personality",36,188,245,42,multi=True); field("Ideals","ideals",293,188,263,42,multi=True)
    field("Bonds","bonds",36,124,245,42,multi=True); field("Flaws","flaws",293,124,263,42,multi=True)
    c.setFont("Helvetica",6.5); c.drawString(36,92,"Fields remain editable in PDF viewers that support AcroForm forms.")
    c.showPage()
    c.setFont("Helvetica-Bold",18); c.drawString(36,754,_v(sheet,"name","Character")+" — DETAILS")
    title("APPEARANCE & STORY",724)
    field("Appearance","appearance",36,624,520,72,multi=True); field("Backstory","backstory",36,446,520,150,multi=True)
    field("Allies & Organizations","allies_organizations",36,352,250,66,multi=True); field("Treasure","treasure",306,352,250,66,multi=True)
    title("SPELLCASTING",324)
    field("Spellcasting Class","spellcasting_class",36,282,140); field("Ability","spellcasting_ability",188,282,90)
    field("Save DC","spell_save_dc",290,282,80); field("Attack Bonus","spell_attack_bonus",382,282,100)
    field("Cantrips","cantrips",36,194,250,66,multi=True); field("Spells","spells",306,194,250,66,multi=True)
    field("Spell Slots","spell_slots",36,106,520,66,multi=True)
    c.save(); out.seek(0); return out
