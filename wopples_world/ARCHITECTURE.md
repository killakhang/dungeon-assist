# Wopples World — Portable Client Architecture

Wopples World must not depend on the browser client for game rules or persistent world state.

## Rule
**Server owns the world. Clients render it.**

The authoritative Python world server owns player/NPC positions, inventories, crops, time, money, combat, quests, permissions, persistence, and validation. Clients send intentions such as move, interact, plant, attack, or chat. The server validates them, changes canonical state, and emits events/state.

## Layers

### 1. Shared protocol
All clients communicate with the server using a versioned JSON protocol over WebSocket/HTTP.

Envelope:
- protocol_version
- type
- request_id
- player_id
- payload
- server_tick

Commands include:
- player.move
- world.interact
- crop.plant
- crop.water
- item.use
- shop.buy
- shop.sell
- chat.send

Events include:
- world.snapshot
- player.moved
- crop.changed
- inventory.changed
- npc.changed
- clock.changed
- chat.message

Never make browser DOM, canvas coordinates, Godot nodes, Unity objects, or engine-specific types part of the network protocol.

### 2. Authoritative simulation
Python modules implement world rules independent of FastAPI:
- simulation/
- systems/
- models/
- persistence/

FastAPI/WebSocket is a transport adapter, not the game itself.

### 3. Clients
Clients are replaceable:
- web/ — current lightweight browser client
- godot/ — future desktop/mobile Godot client
- optional native/3D client later

A new client consumes the same snapshots/events and sends the same commands. This lets us move from browser to Godot without rewriting the world/server.

### 4. Assets
Keep game data separate from presentation.

Use stable asset IDs such as:
- character.wopples
- crop.turnip
- tile.grass.01

Clients map IDs to their own sprites/models/audio. The same Wopples can therefore be rendered as:
- 16/32-bit pixel art
- high-resolution 2D
- skeletal 2D animation
- HD-2D style
- isometric art
- 3D model

Gameplay code must not depend on sprite dimensions or a specific art resolution.

### 5. Map format
Store logical maps in engine-neutral data: tile/grid coordinates, collision shapes, entities, triggers, spawn points, zone links, metadata, and asset IDs. Rendering details belong to the client.

### 6. Persistence
SQLite is fine for the prototype. Hide persistence behind repository/service interfaces so a hosted persistent world can later migrate to PostgreSQL without changing clients.

## Planned migration

### Phase A — Browser prototype
Fast iteration, multiplayer networking, farming loop, NPCs, persistence.

### Phase B — Protocol stabilization
Versioned commands/events, authentication, reconnect/resync, interpolation, server ticks, interest management.

### Phase C — Godot client
Build a Godot 2D client using the exact same server. Improve animation, particles, shaders, lighting, audio, controller support, UI and map tooling.

### Phase D — Mini-MMO
Persistent hosted server, accounts, zones, parties, permissions, server-side NPC simulation, database migration, backups, anti-cheat validation and scalable zone processes.

### Phase E — Optional graphical evolution
Keep the same simulation/protocol while replacing presentation with HD 2D, isometric, 2.5D or 3D if desired.

## Non-negotiable design constraints
1. No authoritative game state only in a client.
2. No engine-specific objects in persistence/network messages.
3. Every network command is validated server-side.
4. Protocol versions are explicit.
5. Assets are referenced by IDs, not hard-coded file paths in simulation.
6. Game systems are testable without launching a graphical client.
7. Browser remains a useful lightweight client even after a richer client exists.
