"""Fill the official 2024 D&D character sheet with editable AcroForm overlays."""
from io import BytesIO
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from pypdf import PdfReader, PdfWriter

W,H=letter
TEMPLATE=Path(__file__).resolve().parent.parent/"assets"/"DnD_2024_Character-Sheet.pdf"

def _v(s,k,d=""):
    v=s.get(k,d)
    if isinstance(v,list): return ", ".join(map(str,v))
    return "" if v is None else str(v)

def _mod(v):
    try:return f"{(int(v)-10)//2:+d}"
    except:return ""

def _overlay(sheet,page):
    out=BytesIO(); c=canvas.Canvas(out,pagesize=letter); form=c.acroform
    def f(name,x,y,w,h=14,value="",size=8,multi=False):
        form.textfield(name=name,value=str(value or ""),x=x,y=y,width=w,height=h,borderWidth=0,
          fillColor=None,textColor=colors.black,fontName="Helvetica",fontSize=size,fieldFlags=4096 if multi else 0)
    if page==0:
        f("name",25,739,220,18,_v(sheet,"name"),10); f("background",25,716,120,14,_v(sheet,"background"))
        f("class",150,716,100,14,_v(sheet,"class")); f("species",25,694,120,14,_v(sheet,"species"))
        f("subclass",150,694,100,14,_v(sheet,"subclass")); f("level",264,716,35,14,_v(sheet,"level"),9)
        f("armor_class",321,715,44,32,_v(sheet,"armor_class"),14); f("hp",385,696,50,16,_v(sheet,"hp"),11)
        f("max_hp",443,696,42,16,_v(sheet,"max_hp")); f("temp_hp",443,722,42,16,_v(sheet,"temp_hp"))
        f("hit_dice",497,696,42,16,_v(sheet,"hit_dice")); f("proficiency_bonus",17,615,86,28,_v(sheet,"proficiency_bonus"),13)
        f("initiative_bonus",229,614,72,20,_v(sheet,"initiative_bonus"),11); f("speed",321,614,72,20,_v(sheet,"speed"),11)
        f("passive_perception",508,614,79,20,_v(sheet,"passive_perception"),10)
        coords={"strength":(37,527),"dexterity":(37,405),"constitution":(37,281),"intelligence":(130,588),"wisdom":(130,405),"charisma":(130,281)}
        for k,(x,y) in coords.items(): f(k,x+32,y,38,20,_v(sheet,k),11); f(k+"_modifier",x,y+4,34,24,_mod(sheet.get(k)),13)
        f("saving_throws",119,468,90,190,_v(sheet,"saving_throws"),7,True); f("skills",119,326,90,145,_v(sheet,"skills"),7,True)
        f("attacks",226,471,361,143,_v(sheet,"attacks"),8,True); f("class_features",226,221,361,230,_v(sheet,"class_features") or _v(sheet,"features_traits"),8,True)
        f("species_traits",226,25,174,165,_v(sheet,"species_traits"),8,True); f("feats",412,25,175,165,_v(sheet,"feats"),8,True)
        f("proficiencies_languages",17,25,194,120,_v(sheet,"proficiencies_languages"),7,True)
    else:
        f("spellcasting_ability",17,733,118,18,_v(sheet,"spellcasting_ability"),9); f("spell_save_dc",48,681,86,18,_v(sheet,"spell_save_dc"),10)
        f("spell_attack_bonus",48,645,86,18,_v(sheet,"spell_attack_bonus"),10); f("spell_slots",151,672,245,70,_v(sheet,"spell_slots"),7,True)
        spells=_v(sheet,"prepared_spells") or _v(sheet,"cantrips"); f("prepared_spells",17,25,378,595,spells,7,True)
        f("appearance",411,683,177,78,_v(sheet,"appearance"),8,True)
        story=_v(sheet,"backstory"); pers=_v(sheet,"personality"); combined=(story+"\n\n"+pers).strip()
        f("backstory_personality",411,481,177,170,combined,8,True); f("alignment",411,464,177,14,_v(sheet,"alignment"),8)
        f("languages",411,390,177,52,_v(sheet,"proficiencies_languages"),8,True); f("equipment",411,95,177,266,_v(sheet,"equipment"),8,True)
        f("coins",411,24,177,40,_v(sheet,"coins"),9)
    c.save(); out.seek(0); return out

def build_character_pdf(sheet):
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"Missing character sheet template: {TEMPLATE}")
    base=PdfReader(str(TEMPLATE)); writer=PdfWriter()
    for i,p in enumerate(base.pages):
        ov=PdfReader(_overlay(sheet,i)); p.merge_page(ov.pages[0]); writer.add_page(p)
    writer.set_need_appearances_writer()
    out=BytesIO(); writer.write(out); out.seek(0); return out
