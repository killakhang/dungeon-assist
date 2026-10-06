# Dungeon Assist

Discord-first D&D assistant and DM simulation platform.

## v0.1
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
