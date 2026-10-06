"""Printable original-layout D&D 2024 character sheet PDF generator."""
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

def _v(sheet, key, default="-"):
    v=sheet.get(key)
    if v in (None,"",[]): return default
    if isinstance(v, dict): return ", ".join(f"{k}: {x}" for k,x in v.items()) or default
    if isinstance(v, list): return ", ".join(str(x) for x in v) or default
    return str(v)

def _mod(score):
    try:
        n=int(score)
        m=(n-10)//2
        return f"{m:+d}"
    except (TypeError,ValueError):
        return "-"

def build_character_pdf(sheet):
    out=BytesIO()
    doc=SimpleDocTemplate(out,pagesize=letter,rightMargin=30,leftMargin=30,topMargin=30,bottomMargin=30,
                          title=f"{_v(sheet,'name','Character')} - Character Sheet")
    styles=getSampleStyleSheet()
    title=ParagraphStyle("SheetTitle",parent=styles["Title"],fontSize=20,leading=23,alignment=TA_CENTER,spaceAfter=8)
    h=ParagraphStyle("Section",parent=styles["Heading2"],fontSize=11,leading=13,spaceBefore=8,spaceAfter=4)
    body=ParagraphStyle("BodySmall",parent=styles["BodyText"],fontSize=8.5,leading=11)
    story=[Paragraph(_v(sheet,"name","Character").upper(),title)]
    summary=[
        ["CLASS",_v(sheet,"class"),"LEVEL",_v(sheet,"level","1"),"SPECIES",_v(sheet,"species")],
        ["BACKGROUND",_v(sheet,"background"),"ALIGNMENT",_v(sheet,"alignment"),"RULESET",_v(sheet,"ruleset","D&D 2024")],
    ]
    t=Table(summary,colWidths=[55,115,45,45,55,135])
    t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.5,colors.grey),("FONTNAME",(0,0),(-1,-1),"Helvetica"),
                           ("FONTSIZE",(0,0),(-1,-1),8),("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
                           ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("PADDING",(0,0),(-1,-1),5)]))
    story += [t,Spacer(1,8),Paragraph("CORE STATS",h)]
    abilities=[]
    for key,label in [("strength","STR"),("dexterity","DEX"),("constitution","CON"),("intelligence","INT"),("wisdom","WIS"),("charisma","CHA")]:
        score=_v(sheet,key)
        abilities.append([label,score,_mod(score)])
    t=Table([["ABILITY","SCORE","MOD"]]+abilities,colWidths=[90,70,70])
    t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.5,colors.grey),("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
                           ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("ALIGN",(1,1),(-1,-1),"CENTER"),
                           ("FONTSIZE",(0,0),(-1,-1),9),("PADDING",(0,0),(-1,-1),5)]))
    combat=[
        ["HP",f"{_v(sheet,'hp','0')} / {_v(sheet,'max_hp','0')}","TEMP HP",_v(sheet,"temp_hp","0")],
        ["ARMOR CLASS",_v(sheet,"armor_class"),"SPEED",_v(sheet,"speed")],
        ["INITIATIVE",_v(sheet,"initiative_bonus"),"HIT DICE",_v(sheet,"hit_dice")],
        ["CONDITIONS",_v(sheet,"conditions"),"INSPIRATION",_v(sheet,"inspiration","False")],
    ]
    ct=Table(combat,colWidths=[80,120,80,120])
    ct.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.5,colors.grey),("FONTNAME",(0,0),(-1,-1),"Helvetica"),
                            ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8.5),("PADDING",(0,0),(-1,-1),5)]))
    story += [Spacer(1,8),Paragraph("COMBAT",h),ct]
    story += [Paragraph("PROFICIENCIES & FEATURES",h),
              Paragraph("<b>Saving Throws:</b> "+_v(sheet,"save_proficiencies"),body),
              Paragraph("<b>Skills:</b> "+_v(sheet,"skill_proficiencies"),body),
              Paragraph("<b>Languages / Proficiencies:</b> "+_v(sheet,"proficiencies_languages"),body),
              Paragraph("<b>Features & Traits:</b> "+_v(sheet,"features_traits"),body),
              Paragraph("<b>Attacks:</b> "+_v(sheet,"attacks"),body),
              Paragraph("<b>Equipment:</b> "+_v(sheet,"equipment"),body),
              PageBreak(),Paragraph(_v(sheet,"name","Character")+" - ROLEPLAY & SPELLS",title)]
    for label,key in [("Personality","personality"),("Ideals","ideals"),("Bonds","bonds"),("Flaws","flaws"),("Appearance","appearance"),
                      ("Backstory","backstory"),("Allies & Organizations","allies_organizations"),("Treasure","treasure")]:
        story += [Paragraph(label.upper(),h),Paragraph(_v(sheet,key),body)]
    story += [Paragraph("SPELLCASTING",h),
              Paragraph("<b>Class:</b> "+_v(sheet,"spellcasting_class"),body),
              Paragraph("<b>Ability:</b> "+_v(sheet,"spellcasting_ability")+" &nbsp;&nbsp; <b>Save DC:</b> "+_v(sheet,"spell_save_dc")+" &nbsp;&nbsp; <b>Attack:</b> "+_v(sheet,"spell_attack_bonus"),body),
              Paragraph("<b>Cantrips:</b> "+_v(sheet,"cantrips"),body),
              Paragraph("<b>Spells:</b> "+_v(sheet,"spells"),body),
              Paragraph("<b>Spell Slots:</b> "+_v(sheet,"spell_slots"),body),
              Spacer(1,12),Paragraph("Generated by Wopples' Dungeon Buddy. Original print-friendly layout; not an official Wizards character sheet.",body)]
    doc.build(story)
    out.seek(0)
    return out
