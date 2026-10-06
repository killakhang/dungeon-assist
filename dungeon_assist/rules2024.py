RULESET = "2024_5e"

FIELD_HELP = {
    "ability_scores": "STR, DEX, CON, INT, WIS, and CHA describe broad capabilities. A score produces a modifier used by checks, saves, attacks, and class features.",
    "proficiency": "Proficiency means your character is trained with a save, skill, weapon, tool, or other game element. At level 1 the proficiency bonus is +2.",
    "armor_class": "Armor Class (AC) is the number an attack roll normally needs to meet or beat to hit you. Armor, Dexterity, shields, and features can affect it.",
    "hit_points": "Hit Points (HP) measure how much harm your character can withstand before dropping to 0 HP.",
    "saving_throws": "A saving throw is a defensive roll against danger. Your class determines which two saves receive proficiency.",
    "skills": "Skills are common adventuring tasks tied to ability checks. Proficiency adds your proficiency bonus when that skill applies.",
    "background": "In the 2024 rules, your background is mechanically important: it helps define your origin, including ability-score options and an Origin Feat.",
    "origin_feat": "An Origin Feat is a feat gained as part of your character's origin under the 2024 rules.",
    "species": "Species describes your character's ancestry and species traits. In the 2024 rules, ability-score increases come from background rather than species.",
    "class": "Class is your main adventuring role. It determines core features, Hit Die, proficiencies, and how the character develops as levels increase.",
    "weapon_mastery": "Some 2024 classes can use Weapon Mastery properties with weapons they have selected for mastery.",
    "spellcasting": "Spellcasters track a spellcasting ability and, when applicable, spell attack bonus, spell save DC, prepared/known spells, and spell slots."
}

CORE_FIELDS = (
    "species", "class", "background",
    "strength", "dexterity", "constitution",
    "intelligence", "wisdom", "charisma"
)

def help_topic(topic):
    key = topic.strip().lower().replace(" ", "_")
    if key not in FIELD_HELP:
        raise ValueError("Unknown topic. Try: " + ", ".join(FIELD_HELP))
    return FIELD_HELP[key]

def check_sheet(sheet):
    issues = []
    if sheet.get("ruleset") != RULESET:
        issues.append("Ruleset should be 2024_5e.")
    for field in CORE_FIELDS:
        if sheet.get(field) in (None, "", [], "Unchosen"):
            issues.append("Missing " + field.replace("_", " ") + ".")
    for ability in ("strength","dexterity","constitution","intelligence","wisdom","charisma"):
        value = sheet.get(ability)
        if value not in (None, "", "Unchosen"):
            try:
                n = int(value)
                if n < 1 or n > 30:
                    issues.append(ability.title() + " should normally be between 1 and 30.")
            except (TypeError, ValueError):
                issues.append(ability.title() + " must be a number.")
    if not sheet.get("max_hp") or int(sheet.get("max_hp", 0)) < 1:
        issues.append("Maximum HP must be at least 1.")
    return issues
