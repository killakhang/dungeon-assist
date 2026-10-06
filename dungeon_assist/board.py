from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

CELL=64
COLS=12
ROWS=8

def render_board(creatures, title="Dungeon Assist"):
    im=Image.new("RGB",(COLS*CELL,ROWS*CELL),(38,51,68))
    d=ImageDraw.Draw(im)
    for x in range(COLS+1): d.line((x*CELL,0,x*CELL,ROWS*CELL),fill=(75,85,99),width=1)
    for y in range(ROWS+1): d.line((0,y*CELL,COLS*CELL,y*CELL),fill=(75,85,99),width=1)
    for c in creatures:
        x=max(0,min(COLS-1,int(c["x"])))*CELL; y=max(0,min(ROWS-1,int(c["y"])))*CELL
        friendly=c.get("kind") in ("hero","player","ally")
        fill=(34,110,70) if friendly else (145,45,45)
        d.ellipse((x+7,y+7,x+CELL-7,y+CELL-7),fill=fill,outline=(245,245,245),width=3)
        label=str(c["name"])[:12]
        d.text((x+5,y+CELL-15),label,fill=(255,255,255))
        hp=max(0,int(c["hp"])); mx=max(1,int(c["max_hp"]))
        d.rectangle((x+7,y+3,x+CELL-7,y+7),fill=(55,55,55))
        d.rectangle((x+7,y+3,x+7+int((CELL-14)*hp/mx),y+7),fill=(50,200,90))
    out=BytesIO(); im.save(out,"PNG"); out.seek(0); return out
