# Wopples World Combat Roadmap

Goal: work upward from a mechanically fun room to five friends fighting an epic boss or monster squad.

## Combat rule
Movement must feel good before progression systems hide weaknesses.

## Stage 1 — Action Room
One player, then multiplayer. Movement, facing, attack, stamina, dodge with short invulnerability, hit range, telegraphs, damage, down state. No loot treadmill required.

## Stage 2 — Five-player Monster Squad
Up to five connected players share one authoritative encounter. Several enemies choose targets and pressure the group. No mandatory tank/healer/DPS roles.

## Stage 3 — Skill Boss
Boss phases, readable telegraphs, shockwaves/projectiles, weak windows, revives, environmental hazards. Entire phase can be pure movement/timing/skill with no tactical pause.

## Stage 4 — Wopples Think Time
Battle-Network-inspired tactical windows layered onto selected encounters. Players choose a limited loadout action, then execution returns to real time. Action-only encounters remain in the game.

## Stage 5 — Epic Five-player Encounter
Boss plus adds, phase transitions, arena changes, cooperative mechanics, combo interactions, down/revive, spectator/rejoin, reconnect/resync, server validation and persistent rewards that improve the shared town.

## Networking
Server is authoritative for HP, stamina, cooldowns, monster AI, hit validation and encounter state. Clients send intent. Add fixed server ticks, client interpolation/prediction and reconciliation as the prototype matures.

## First prototype controls
Move: WASD / arrows
Attack: J
Dodge: Space
Interact: E

## Prototype enemies
Angry Blob squad tests target pressure and movement.
Mushroom King tests a high-HP boss and health-based phase changes.

This module remains independent from browser rendering so a future Godot client can use the same combat rules/protocol.
