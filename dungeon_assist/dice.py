import random, re

PATTERN=re.compile(r"^\s*(\d{0,2})d(\d{1,4})([+-]\d+)?\s*$",re.I)

def roll_expression(expression):
    m=PATTERN.match(expression)
    if not m: raise ValueError("Use dice like 1d20+5 or 2d6.")
    count=int(m.group(1) or 1); sides=int(m.group(2)); mod=int(m.group(3) or 0)
    if not 1 <= count <= 50 or not 2 <= sides <= 1000:
        raise ValueError("Dice must be 1-50 dice with 2-1000 sides.")
    rolls=[random.randint(1,sides) for _ in range(count)]
    total=sum(rolls)+mod
    sign=f"{mod:+d}" if mod else ""
    return {"rolls":rolls,"modifier":mod,"total":total,"detail":f"{rolls}{sign}"}
