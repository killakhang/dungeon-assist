"""Beginner-first 2024 character builder metadata.

This module intentionally stores field structure and plain-language teaching text,
not proprietary rulebook text.
"""

BUILD_2024 = [
    ("class", "Class", "What kind of adventurer is your character? Examples include a warrior, spellcaster, or expert.", "Your class is your character's main adventuring role. It determines many abilities you gain as you level."),
    ("species", "Species", "What species is your character?", "Species describes what kind of fantasy person your character is and contributes character traits."),
    ("background", "Background", "What did your character do before adventuring?", "A background represents your character's life and training before the adventure began."),
    ("origin_feat", "Origin Feat", "What Origin Feat does your character have?", "An Origin Feat is an early character feature connected to character creation and background."),
    ("alignment", "Alignment", "How would you describe your character's general moral outlook?", "Alignment is a broad roleplaying description of moral outlook. It does not force your character to behave a particular way."),
    ("strength", "Strength", "Choose your Strength score.", "Strength represents physical power."),
    ("dexterity", "Dexterity", "Choose your Dexterity score.", "Dexterity represents agility, reflexes, and coordination."),
    ("constitution", "Constitution", "Choose your Constitution score.", "Constitution represents health, endurance, and toughness."),
    ("intelligence", "Intelligence", "Choose your Intelligence score.", "Intelligence represents reasoning, memory, and learned knowledge."),
    ("wisdom", "Wisdom", "Choose your Wisdom score.", "Wisdom represents awareness, intuition, and practical judgment."),
    ("charisma", "Charisma", "Choose your Charisma score.", "Charisma represents force of personality and social presence."),
]

DEFAULT_2024 = {
    "ruleset": "2024_5e",
    "origin_feat": "",
    "subclass": "",
    "weapon_masteries": [],
    "class_features": [],
    "species_traits": [],
    "background_features": [],
    "feats": [],
    "resources": {},
    "saving_throw_proficiencies": [],
    "skill_proficiencies": [],
    "attacks": [],
    "equipment": [],
    "proficiencies_languages": [],
    "spellcasting_class": "",
    "spellcasting_ability": "",
    "spell_save_dc": None,
    "spell_attack_bonus": None,
    "cantrips": [],
    "spells": {},
    "spell_slots": {},
}

def next_question(sheet):
    for key, label, question, explanation in BUILD_2024:
        value = sheet.get(key)
        if value is None or value == "" or value == []:
            return {"key": key, "label": label, "question": question, "explanation": explanation}
    return None


# Beginner discovery choices. These are concise navigation/examples, not copied rulebook text.
CHOICES_2024 = {
    "class": [
        ("Fighter","Weapon-focused warrior."),
        ("Wizard","Scholar of arcane magic."),
        ("Rogue","Skillful, sneaky precision adventurer."),
        ("Cleric","Divine spellcaster and supporter."),
        ("Ranger","Wilderness-focused warrior."),
        ("Bard","Magic, skills, and social talent."),
        ("Monk","Fast martial artist."),
        ("Paladin","Armored warrior with sacred magic."),
        ("Sorcerer","Innate magical power."),
        ("Warlock","Magic tied to a supernatural patron."),
        ("Barbarian","Tough frontline warrior."),
        ("Druid","Nature magic and transformation."),
    ],
    "species": [
        ("Human","Familiar fantasy adventurer."),
        ("Elf","Classic magical fantasy ancestry."),
        ("Dwarf","Sturdy classic fantasy ancestry."),
        ("Dragonborn","Draconic fantasy ancestry."),
        ("Goliath","Large, powerful fantasy ancestry."),
        ("Halfling","Small classic fantasy adventurer."),
        ("Orc","Powerful orc adventurer."),
        ("Tiefling","Supernatural fiendish heritage."),
    ],
    "alignment": [
        ("Lawful Good","Values order and helping others."),
        ("Neutral Good","Generally tries to do good."),
        ("Chaotic Good","Values freedom while trying to do good."),
        ("Lawful Neutral","Strongly values rules or order."),
        ("Neutral","Not strongly pulled toward either extreme."),
        ("Chaotic Neutral","Strongly values freedom and independence."),
        ("Lawful Evil","Uses order toward selfish or harmful ends."),
        ("Neutral Evil","Primarily pursues selfish or harmful goals."),
        ("Chaotic Evil","Destructive and unconstrained by order."),
    ],
}

ABILITY_EXAMPLES = {
    "strength": "Physical power. Example: lifting, wrestling, forcing something open.",
    "dexterity": "Agility and coordination. Example: sneaking, balance, quick movement.",
    "constitution": "Endurance and toughness. Example: surviving physical hardship.",
    "intelligence": "Reasoning and learned knowledge. Example: recalling studied information.",
    "wisdom": "Awareness and intuition. Example: noticing danger or reading a situation.",
    "charisma": "Force of personality. Example: persuading, performing, or intimidating.",
}

def choices_for(field):
    return CHOICES_2024.get(field, [])

def help_for(field):
    for key, label, question, explanation in BUILD_2024:
        if key == field:
            return explanation
    return ABILITY_EXAMPLES.get(field, "No beginner explanation is available yet.")
