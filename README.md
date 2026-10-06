# Dungeon Assist

Discord-first D&D assistant and DM simulation platform.

## v0.2 playable core
- `/dndhelp`
- `/campaign_setup`
- `/character_create`
- `/proxy` modes with character-owner authorization
- `/campaign_scan` honors Discord channel permissions
- recognizes channels such as `character-wopples`
- `/snapshot`
- reset lock, 2-minute unlock window, exact campaign-name confirmation
- automatic pre-reset recovery snapshot
- full reset returns characters to base Level 1 state and wipes bot campaign memories
- modular engine interface and Relationship Engine scaffold

## Setup
1. Python 3.11+
2. `python -m venv .venv`
3. Activate it.
4. `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and add your Discord token.
6. Enable Message Content intent in Discord Developer Portal.
7. Invite the bot with application commands and only the channel permissions you want.
8. `python run.py`

## Privacy
Dungeon Assist never bypasses Discord permissions. Scanning only reads channels visible to the bot. Proxy control belongs to the character owner. Future voice transcription must be opt-in and visible.

## Roadmap
- v0.2: dice/parser, initiative, HP/conditions, Level-1 builder, recap
- v0.3: LLM provider, structured memories/beliefs, Wopples persona, audit logs
- v0.4: opt-in voice/STT/TTS
- v0.5: encounter/NPC/faction/reputation/rumor/world/causality engines
- v0.6: maps, grid, fog/DM view, browser companion

Simulation engines update structured state. The LLM explains/roleplays state. DM approval controls canon-changing generated events.


## Running on AWS EC2

If you are using an Amazon Linux EC2 instance, open **EC2 → Instances → your instance → Connect → EC2 Instance Connect**. You can do this entirely from a Chromebook browser.

### Install Dungeon Assist

Paste the following directly into the EC2 terminal:

```bash
sudo dnf install -y git python3 python3-pip && \
cd ~ && \
git clone https://github.com/killakhang/dungeon-assist.git 2>/dev/null || true
cd ~/dungeon-assist
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "=== DUNGEON ASSIST INSTALLED ==="
```

### Start the Discord bot securely

First reset any Discord bot token that has been exposed. Never put a real token in GitHub, the README, or source code.

Then run:

```bash
cd ~/dungeon-assist
source .venv/bin/activate
read -s -p "Paste NEW Discord token: " DISCORD_TOKEN
echo
export DISCORD_TOKEN
python run.py
```

The token is entered invisibly because `read -s` disables terminal echo. When the bot starts successfully, you should see a message similar to:

```text
Dungeon Assist ready as ...
```

This foreground method is useful for the first test. A persistent background service should be configured separately before relying on the bot to survive terminal disconnects or EC2 reboots.


## Discord installation and permissions

Dungeon Assist is intended for **Guild Install** (server installation), not User Install. Discord requires a server owner or member with permission to manage/install apps to authorize the bot once. Dungeon Assist cannot and should not bypass that authorization.

The bot does **not** require Administrator. For the current v0.2 slash-command feature set, grant only:
- View Channels
- Send Messages
- Read Message History (needed later for explicitly requested campaign scanning)
- Use Application Commands

Normal players can use commands after installation without being server administrators, subject to the server/channel command permissions configured by the server's admins.

## v0.2 implemented commands

- `/campaign_setup`
- `/character_create`, `/character_show`
- `/hp`, `/condition`
- `/roll`
- `/initiative_add`, `/initiative`, `/initiative_clear`
- `/quest_add`, `/quests`
- `/scene`
- `/note`, `/recap`
- `/snapshot`

Campaign state persists in SQLite (`dungeon_assist.db`). The next layers are sessions/event bus, inventory/resources, knowledge/secrets, homebrew/rules configuration, DM approval/rollback, relationships/factions, AI proxy/memory, then voice/maps.


## Ruleset

Dungeon Assist uses the **2024 revised D&D 5e rules** as its canonical/default ruleset.

Character creation, sheet education, leveling, classes, backgrounds, Origin Feats, Weapon Mastery, spells, and rules explanations should follow the 2024 rules and must not silently mix in 2014 rules.

Planned beginner sheet tools:
- guided 2024 character creation, one step at a time
- explanations for ability scores/modifiers, proficiency, AC, saves, skills, attacks, spellcasting, equipment, and class resources
- `/sheet_help` for field-by-field education
- `/sheet_check` for missing or inconsistent character fields
- `/character_sheet` for a readable finished sheet
- `/character_levelup` for guided 2024 leveling
