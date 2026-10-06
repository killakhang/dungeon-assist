# Wopples World — Game Vision v0.2

> **Cute does not mean easy.**

## Fantasy
A tiny, foolish goblin and up to four friends live in a warm, whimsical, handmade fantasy world that is beautiful to wander through and brutally dangerous to master.

The visual direction is original whimsical fantasy: crooked cottages, giant roots, soft forests, mossy ruins, glowing spirits, strange food, oversized mushrooms, warm lanterns, expressive creatures, hand-painted-feeling shapes and playful animation. It may draw broad influence from pastoral animated fantasy, but must not imitate any particular film, studio character, or copyrighted visual design.

Wopples remains deliberately simple, cute and dumb-looking. His dialogue is third-person and short:
- "Wopples non like."
- "Wopples touch."
- "Wopples fine."
- "Wopples go anyway."

## Core loop

**Town → prepare → explore → movement challenge → dangerous encounter → discover/rescue/collect → choose whether to push deeper → boss/treasure → return → permanently improve the shared town → unlock new possibilities → revisit old places with new abilities.**

Farming is optional. Exploration, mastery, discovery, collection, combat and rebuilding are primary.

## Difficulty philosophy

Combat should eventually reach the challenge level associated with demanding action RPGs, but difficulty must come from learnable mechanics rather than inflated health.

- Enemies can kill careless players quickly.
- Attacks are readable and consistent.
- Dodging, spacing, stamina, commitment and timing matter.
- Panic rolling/dodging is punishable.
- Healing creates vulnerability.
- Encounters punish getting surrounded.
- Boss phases test learned mechanics.
- A death should usually produce: "I know what I did wrong."
- Five players do not automatically trivialize content.
- Multiplayer scaling changes mechanics, pressure and enemy composition—not just HP.
- No giant warning overlays are required for every attack; animation/audio/world cues should teach players.

## Combat modes

### Pure Action
No turns and no tactical pause. Movement, jumping, dashing, dodging, attacking, parrying, traversal abilities and environmental interaction happen continuously. Some bosses and entire phases are exclusively action/skill encounters.

### Think-Time Hybrid
Selected encounters use real-time movement and execution with brief tactical selection windows inspired by action/tactical hybrids. A player selects from their equipped actions/items, then immediately returns to real-time execution.

Think Time is not mandatory for every encounter.

### Mixed bosses
Bosses may transition between tactical setup and uncompromising action phases. The transition itself should change how players think.

## Movement

Movement is a core progression system:
- responsive run
- jump
- dodge/dash
- wall interaction
- later: grapple, glide, bounce, swim and other traversal powers

Traversal abilities must work in both exploration and combat whenever possible. Old regions contain visible but initially unreachable secrets.

## Expedition tension

Players leave the safety of town and accumulate expedition rewards. Going farther increases danger and potential rewards. Returning banks progress. Wiping risks some unbanked expedition resources.

Death can leave a recoverable spirit/cache at the place of death. Exact loss rules will be tuned through playtesting so failure creates tension without making friends quit.

## Shared town

Adventure rewards physically change the home world.

Examples:
- Rescue a blacksmith → blacksmith appears in town.
- Recover a workshop blueprint → players can construct it.
- Defeat a regional boss → ecology/dialogue/vendors may change.
- Find strange furniture/artifacts → display them.
- Discover creatures/eggs → some can inhabit or affect town.

Players can naturally specialize in fighting, exploration, creatures, collecting, decorating, crafting or other activities without mandatory MMO tank/healer/DPS roles.

## Reward philosophy

Prefer possibility-changing rewards over tiny numerical upgrades.

Examples:
- Goblin Hook — grapple terrain and some enemies.
- Exploding Boots — a well-timed dodge can leave an explosive surprise.
- Rat Flute — summons unreliable rats.
- Moon Key — initially unexplained; creates a world mystery.

Weapons can evolve and branch with use. Different weapon families should materially change timing, range, movement and strategy.

## World psychology

The world should constantly create:
- "What is over there?"
- "How do I reach that?"
- "Should we go one room deeper?"
- "What does this thing do?"
- "We have to show the others."
- "We can beat this boss if we try again."

Randomness creates stories and discoveries, not arbitrary unavoidable failure.

## Five-player target

Primary social target: host/player plus up to four friends.

Epic encounters eventually support:
- five synchronized players
- server-authoritative health/stamina/cooldowns/hits
- revives/down states
- reconnect/resync
- boss phase transitions
- enemy squads
- hazards/projectiles
- cooperative mechanics
- individual mechanical skill
- optional Think-Time windows
- persistent rewards for the shared world

## Feel hierarchy

**Seconds:** movement, dodges, attacks and impacts feel excellent.

**Minutes:** learn encounter → overcome it → discover reward/secret.

**20–30 minutes:** expedition → rising risk → decision to retreat/push → major encounter → return.

**Hours:** builds, weapon evolution, traversal abilities, regions and mysteries.

**Days:** shared settlement visibly develops.

**Weeks+:** difficult bosses, collections, hidden areas, world changes and stories with friends.

## Prototype order

1. One room, Wopples and one enemy.
2. Tune movement, attack commitment, dodge, stamina, hit reactions and telegraphs until fighting one enemy is fun.
3. Add server-synchronized five-player combat.
4. Add a coordinated monster squad.
5. Add Mushroom King as the first skill boss.
6. Add down/revive and expedition-loss/recovery prototype.
7. Add traversal challenge room.
8. Add first Think-Time encounter.
9. Connect combat reward to a visible town improvement.
10. Only then expand content.

## Architecture rule

**Server owns the world. Clients render it.**

All combat, progression and persistence remain engine-neutral so the browser is a prototype client, not a permanent graphical limitation. A future Godot/high-resolution 2D/2.5D client should consume the same authoritative game protocol.
